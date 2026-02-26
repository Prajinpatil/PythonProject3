"""
Threat Detection Router  —  FastAPI
====================================
Registered in main.py as:
    from app.threat_detection.routes import router as threat_router
    app.include_router(threat_router, prefix="/threat", tags=["Threat Detection"])

Endpoints
---------
GET  /threat/stream/{cam_id}      – MJPEG stream (annotated, runs YOLO per frame)
POST /threat/frame                – process a single base64 frame
GET  /threat/dashboard/stats      – live header-card numbers for the dashboard
GET  /threat/alerts/live          – current active + recent alert list
POST /threat/feedback             – confirm or dismiss an alert (triggers learning)
GET  /threat/rules                – get current threat-scoring rule config
POST /threat/rules                – update a single rule value
GET  /threat/stats                – learned biases + feedback summary
"""

from __future__ import annotations

import asyncio
import base64
import os
import time
import threading
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────────────────────
# ROUTER  (main.py does: from app.threat_detection.routes import router)
# ─────────────────────────────────────────────────────────────────────────────
router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────────────────────
class FrameRequest(BaseModel):
    frame: str                          # base64 encoded JPEG/PNG
    cam_id: str = "CAM-BROWSER"
    annotate: bool = False


class FeedbackRequest(BaseModel):
    label: str
    is_threat: bool
    features: Optional[Dict[str, Any]] = None


class RuleUpdateRequest(BaseModel):
    key: str
    value: float


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STATE  (in-memory — survives the process lifetime)
# ─────────────────────────────────────────────────────────────────────────────
_state: Dict[str, Any] = {
    "cameras_online":  0,
    "events_today":    0,
    "active_alerts":   [],              # alerts active in last 30 s
    "alert_history":   deque(maxlen=200),
}
_state_lock = threading.Lock()

# Open camera handles  { cam_id: cv2.VideoCapture }
_cameras: Dict[str, cv2.VideoCapture] = {}
_cam_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# DETECTOR SINGLETON  (lazy-loaded on first request)
# ─────────────────────────────────────────────────────────────────────────────
_detector = None
_detector_lock = threading.Lock()


def get_detector():
    global _detector
    if _detector is None:
        with _detector_lock:
            if _detector is None:           # double-checked locking
                from app.threat_detection.detector import ThreatDetector
                model_size = os.getenv("THREAT_MODEL_SIZE", "n")
                device     = os.getenv("THREAT_DEVICE", "cpu")
                _detector  = ThreatDetector(model_size=model_size, device=device)
    return _detector


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _b64_to_frame(b64_str: str) -> Optional[np.ndarray]:
    """Decode a base64 data-URI or raw base64 string → BGR numpy array."""
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    try:
        raw = base64.b64decode(b64_str)
        arr = np.frombuffer(raw, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


def _annotate(frame: np.ndarray, result: dict) -> np.ndarray:
    """Draw bounding boxes + threat labels onto a copy of the frame."""
    out = frame.copy()
    for det in result.get("detections", []):
        x1, y1, x2, y2 = map(int, det["box"])
        threat = det["is_threat"]
        color  = (0, 30, 220) if threat else (0, 200, 80)
        label  = f"{'! ' if threat else ''}{det['label']} {det['threat_score']:.0%}"
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(out, label, (x1, max(y1 - 6, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return out


def _threat_level(score: float) -> str:
    if score >= 0.80: return "CRITICAL"
    if score >= 0.55: return "WARNING"
    return "INFO"


def _register_detections(cam_id: str, result: dict):
    """Update global alert state from a processed frame result."""
    now_str = datetime.now().strftime("%H:%M:%S")
    with _state_lock:
        for det in result.get("alerts", []):
            alert = {
                "id":        f"{cam_id}-{int(time.time() * 1000)}",
                "cam":       cam_id,
                "label":     det["label"],
                "score":     det["threat_score"],
                "reason":    det["reason"],
                "level":     _threat_level(det["threat_score"]),
                "time":      now_str,
                "timestamp": time.time(),
            }
            _state["active_alerts"].append(alert)
            _state["alert_history"].appendleft(alert)
            _state["events_today"] += 1

        # expire alerts older than 30 seconds
        cutoff = time.time() - 30
        _state["active_alerts"] = [
            a for a in _state["active_alerts"] if a["timestamp"] > cutoff
        ]


def _get_or_open_camera(cam_id: str, device_index: int = 0) -> Optional[cv2.VideoCapture]:
    with _cam_lock:
        if cam_id not in _cameras:
            cap = cv2.VideoCapture(device_index)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not cap.isOpened():
                return None
            _cameras[cam_id] = cap
            with _state_lock:
                _state["cameras_online"] = len(_cameras)
        return _cameras.get(cam_id)


# ─────────────────────────────────────────────────────────────────────────────
# MJPEG STREAM GENERATOR  (runs in a thread via asyncio.to_thread)
# ─────────────────────────────────────────────────────────────────────────────
def _mjpeg_frames(cam_id: str, device_index: int, annotate: bool):
    """
    Synchronous generator — yields raw MJPEG boundary bytes.
    Called via asyncio.to_thread so it doesn't block the event loop.
    """
    cap = _get_or_open_camera(cam_id, device_index)
    if cap is None:
        return

    detector = get_detector()

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        result = detector.process_frame(frame)
        _register_detections(cam_id, result)

        display = _annotate(frame, result) if annotate else frame

        # burn timestamp + cam label onto frame
        ts = datetime.now().strftime("%H:%M:%S")
        cv2.putText(display, f"[{cam_id}]  {ts}",
                    (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 1)

        ok, buf = cv2.imencode(".jpg", display, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buf.tobytes()
            + b"\r\n"
        )


async def _async_mjpeg(cam_id: str, device_index: int, annotate: bool):
    """
    Async wrapper around the sync generator.
    Yields chunks without blocking the FastAPI event loop.
    """
    loop = asyncio.get_event_loop()

    def _next(gen):
        try:
            return next(gen)
        except StopIteration:
            return None

    gen = _mjpeg_frames(cam_id, device_index, annotate)
    while True:
        chunk = await loop.run_in_executor(None, _next, gen)
        if chunk is None:
            break
        yield chunk
        # small yield so other coroutines can run between frames
        await asyncio.sleep(0)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stream/{cam_id}")
async def camera_stream(
    cam_id: str,
    device: int = Query(default=0, description="OpenCV camera device index"),
    raw: int    = Query(default=0, description="Set to 1 to skip annotation"),
):
    """
    Live MJPEG stream for one camera slot.
    The browser <img src="/threat/stream/CAM-01-NORTH?device=0"> plays it natively.
    """
    annotate = raw != 1
    return StreamingResponse(
        _async_mjpeg(cam_id, device, annotate),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post("/frame")
async def process_frame(body: FrameRequest):
    """
    Process a single base64-encoded frame from the browser webcam capture.
    Returns detections, alerts, and optionally an annotated base64 frame.
    """
    frame = await asyncio.to_thread(_b64_to_frame, body.frame)
    if frame is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    detector = get_detector()
    result   = await asyncio.to_thread(detector.process_frame, frame)
    _register_detections(body.cam_id, result)

    if body.annotate:
        annotated     = _annotate(frame, result)
        ok, buf       = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            result["annotated_frame"] = (
                "data:image/jpeg;base64," + base64.b64encode(buf).decode()
            )

    return JSONResponse(content=result)


@router.get("/dashboard/stats")
async def dashboard_stats():
    """
    Live numbers for the 4 header cards + threat level.
    Polled every 2 s by dashboard.html.
    """
    with _state_lock:
        alerts = list(_state["active_alerts"])
        cams   = _state["cameras_online"]
        events = _state["events_today"]

    max_score = max((a["score"] for a in alerts), default=0.0)
    if max_score >= 0.80:
        threat_level = "CRITICAL"
    elif max_score >= 0.55:
        threat_level = "MODERATE"
    else:
        threat_level = "LOW"

    return {
        "cameras_online":  cams,
        "active_alerts":   len(alerts),
        "events_today":    events,
        "sectors_covered": 8,
        "threat_level":    threat_level,
        "timestamp":       datetime.now().strftime("%H:%M:%S"),
    }


@router.get("/alerts/live")
async def live_alerts():
    """
    Active + recent alerts for the dashboard sidebar.
    Deduplicates and returns up to 20.
    """
    with _state_lock:
        active  = list(_state["active_alerts"])
        history = list(_state["alert_history"])[:20]

    seen, merged = set(), []
    for a in active + history:
        if a["id"] not in seen:
            seen.add(a["id"])
            merged.append(a)

    return {"alerts": merged[:20]}


@router.post("/feedback")
async def submit_feedback(body: FeedbackRequest):
    """
    Confirm or dismiss a threat alert.
    Each call nudges the ML model's per-label learned bias.
    """
    detector = get_detector()

    if body.is_threat:
        await asyncio.to_thread(detector.confirm_threat, body.label, body.features)
    else:
        await asyncio.to_thread(detector.dismiss_threat, body.label, body.features)

    new_bias = detector.get_learned_biases().get(body.label, 0.0)
    return {
        "message":  "Feedback recorded",
        "label":    body.label,
        "new_bias": new_bias,
    }


@router.get("/rules")
async def get_rules():
    """Return current threat-scoring rule configuration."""
    return get_detector().get_rules()


@router.post("/rules")
async def update_rule(body: RuleUpdateRequest):
    """Update a single rule value by key."""
    ok = await asyncio.to_thread(get_detector().update_rule, body.key, body.value)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Unknown rule key: '{body.key}'")
    return {"message": f"Rule '{body.key}' updated to {body.value}"}


@router.get("/stats")
async def get_stats():
    """Learned biases and feedback counts — shows what the model has learned."""
    detector = get_detector()
    biases   = detector.get_learned_biases()
    clf      = detector.classifier

    counts: Dict[str, int] = {}
    for fb in clf.feedback_log:
        counts[fb["label"]] = counts.get(fb["label"], 0) + 1

    return {
        "learned_biases":    biases,
        "feedback_counts":   counts,
        "known_safe_labels": list(clf.known_safe),
        "total_feedback":    len(clf.feedback_log),
    }