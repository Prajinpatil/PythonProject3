"""
ThreatVision Detection Engine
- YOLOv8 for object detection (humans, animals, birds)
- Threat classifier with rule engine
- Online learning loop (feedback-based retraining)
"""

import cv2
import numpy as np
import json
import os
import time
import pickle
from datetime import datetime
from pathlib import Path
from collections import deque

# ─────────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────────
HUMAN_CLASSES   = {"person"}
ANIMAL_CLASSES  = {"cat", "dog", "horse", "sheep", "cow", "elephant",
                   "bear", "zebra", "giraffe"}
BIRD_CLASSES    = {"bird"}

DETECTABLE      = HUMAN_CLASSES | ANIMAL_CLASSES | BIRD_CLASSES

# COCO class IDs that map to our categories (for YOLOv8 / ultralytics)
COCO_CATEGORY_MAP = {
    0:  "person",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
}

# ─────────────────────────────────────────────
# MOTION TRACKER  (frame-diff based)
# ─────────────────────────────────────────────
class MotionTracker:
    def __init__(self, history: int = 5, threshold: float = 25.0):
        self.prev_frames: deque = deque(maxlen=history)
        self.threshold = threshold

    def get_motion_score(self, frame_gray: np.ndarray) -> float:
        """Returns 0-1 motion intensity for the whole frame."""
        if len(self.prev_frames) == 0:
            self.prev_frames.append(frame_gray)
            return 0.0
        diff = cv2.absdiff(self.prev_frames[-1], frame_gray)
        score = float(diff.mean()) / self.threshold
        self.prev_frames.append(frame_gray)
        return min(score, 1.0)

    def get_roi_motion(self, frame_gray: np.ndarray, box) -> float:
        """Returns motion score inside a bounding box (x1,y1,x2,y2)."""
        x1, y1, x2, y2 = map(int, box)
        if len(self.prev_frames) == 0:
            return 0.0
        roi_curr = frame_gray[y1:y2, x1:x2]
        roi_prev = self.prev_frames[-1][y1:y2, x1:x2]
        if roi_curr.size == 0 or roi_prev.size == 0:
            return 0.0
        diff = cv2.absdiff(roi_curr, roi_prev)
        return min(float(diff.mean()) / self.threshold, 1.0)


# ─────────────────────────────────────────────
# THREAT CLASSIFIER
# ─────────────────────────────────────────────
class ThreatClassifier:
    """
    Rule-based + learned threat scoring.
    score ∈ [0, 1].  score >= alert_threshold → report.
    """

    DEFAULT_RULES = {
        "person_base_score":        0.6,   # humans start higher
        "animal_base_score":        0.3,
        "bird_base_score":          0.1,
        "motion_weight":            0.25,  # fast-moving boost
        "night_weight":             0.10,  # low brightness boost
        "alert_threshold":          0.55,  # above this → THREAT
        "confidence_min":           0.40,  # ignore low-conf detections
        "unknown_boost":            0.20,  # extra if not in known list
        "known_safe_penalty":       0.30,  # reduce if marked safe
        "fast_motion_threshold":    0.45,  # motion score to trigger boost
    }

    def __init__(self, rules_path: str = None, weights_path: str = None):
        self.rules = dict(self.DEFAULT_RULES)
        self.rules_path = rules_path or "data/user_rules.json"
        self.weights_path = weights_path or "data/learned_weights.pkl"
        self.known_safe: set = set()       # labels user marked safe
        self.feedback_log: list = []       # (features, was_threat) pairs

        self._load_rules()
        self._load_weights()

    # ── persistence ──────────────────────────
    def _load_rules(self):
        if os.path.exists(self.rules_path):
            with open(self.rules_path) as f:
                self.rules.update(json.load(f))

    def save_rules(self):
        os.makedirs(os.path.dirname(self.rules_path) or ".", exist_ok=True)
        with open(self.rules_path, "w") as f:
            json.dump(self.rules, f, indent=2)

    def _load_weights(self):
        self.learned_bias: dict = {}
        if os.path.exists(self.weights_path):
            with open(self.weights_path, "rb") as f:
                data = pickle.load(f)
                self.learned_bias = data.get("bias", {})
                self.known_safe   = set(data.get("known_safe", []))
                self.feedback_log = data.get("feedback_log", [])

    def _save_weights(self):
        os.makedirs(os.path.dirname(self.weights_path) or ".", exist_ok=True)
        with open(self.weights_path, "wb") as f:
            pickle.dump({
                "bias":         self.learned_bias,
                "known_safe":   list(self.known_safe),
                "feedback_log": self.feedback_log[-500:],   # keep last 500
            }, f)

    # ── scoring ──────────────────────────────
    def score(self, label: str, confidence: float,
              motion: float, brightness: float) -> dict:
        """
        Returns a result dict:
            {label, confidence, threat_score, is_threat, reason}
        """
        r = self.rules

        if confidence < r["confidence_min"]:
            return self._result(label, confidence, 0.0, False, "low confidence")

        # base score per category
        if label in HUMAN_CLASSES:
            base = r["person_base_score"]
        elif label in ANIMAL_CLASSES:
            base = r["animal_base_score"]
        else:
            base = r["bird_base_score"]

        score = base

        # motion boost
        if motion >= r["fast_motion_threshold"]:
            score += r["motion_weight"] * motion

        # night / low-light boost
        if brightness < 80:
            score += r["night_weight"]

        # known-safe penalty
        if label in self.known_safe:
            score -= r["known_safe_penalty"]

        # unknown-person boost
        if label == "person" and "person" not in self.known_safe:
            score += r["unknown_boost"]

        # learned bias (from user feedback)
        score += self.learned_bias.get(label, 0.0)

        score = float(np.clip(score, 0.0, 1.0))
        is_threat = score >= r["alert_threshold"]

        reasons = []
        if label in HUMAN_CLASSES:      reasons.append("human detected")
        if motion >= r["fast_motion_threshold"]: reasons.append("fast motion")
        if brightness < 80:             reasons.append("low light")
        if label in self.known_safe:    reasons.append("marked safe")

        return self._result(label, confidence, score, is_threat,
                            ", ".join(reasons) or "normal detection")

    @staticmethod
    def _result(label, conf, score, is_threat, reason):
        return {
            "label":       label,
            "confidence":  round(conf, 3),
            "threat_score": round(score, 3),
            "is_threat":   is_threat,
            "reason":      reason,
            "timestamp":   datetime.utcnow().isoformat(),
        }

    # ── learning ─────────────────────────────
    def record_feedback(self, label: str, was_threat: bool,
                        features: dict = None):
        """
        Call this when the user confirms/denies a threat alert.
        The model adjusts its per-label bias over time.
        """
        self.feedback_log.append({
            "label": label,
            "was_threat": was_threat,
            "features": features or {},
            "ts": time.time(),
        })

        # simple gradient: nudge bias toward correct answer
        current = self.learned_bias.get(label, 0.0)
        target   = 0.2 if was_threat else -0.2
        # slow learning rate so it doesn't over-fit to one event
        new_bias = current + 0.05 * (target - current)
        self.learned_bias[label] = round(new_bias, 4)

        if not was_threat:
            self.known_safe.add(label)
        else:
            self.known_safe.discard(label)

        self._save_weights()

    def update_rule(self, key: str, value):
        if key in self.rules:
            self.rules[key] = value
            self.save_rules()
            return True
        return False


# ─────────────────────────────────────────────
# MAIN DETECTOR  (wraps YOLO + classifier)
# ─────────────────────────────────────────────
class ThreatDetector:
    """
    High-level interface used by the Flask/Django view.

    Usage:
        detector = ThreatDetector()
        results  = detector.process_frame(frame_bgr)
    """

    def __init__(self, model_size: str = "n", device: str = "cpu"):
        """
        model_size: 'n' (nano, fast) | 's' | 'm' | 'l' | 'x' (accurate)
        """
        self.classifier  = ThreatClassifier(
            rules_path="data/user_rules.json",
            weights_path="data/learned_weights.pkl",
        )
        self.motion      = MotionTracker()
        self._model      = None
        self._model_size = model_size
        self._device     = device
        self._init_model()

    def _init_model(self):
        try:
            from ultralytics import YOLO
            model_name = f"yolov8{self._model_size}.pt"
            self._model = YOLO(model_name)
            print(f"[ThreatDetector] Loaded {model_name}")
        except ImportError:
            print("[ThreatDetector] ultralytics not installed – using mock mode")
            self._model = None

    # ── main entry point ─────────────────────
    def process_frame(self, frame_bgr: np.ndarray) -> dict:
        """
        Accept a BGR numpy frame (from OpenCV / video feed decode).
        Returns:
            {
              "detections": [...],   # all detected objects
              "alerts":     [...],   # only threats
              "frame_meta": {...},
            }
        """
        h, w = frame_bgr.shape[:2]
        gray       = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        motion     = self.motion.get_motion_score(gray)

        raw_detections = self._run_yolo(frame_bgr)

        detections = []
        alerts     = []

        for det in raw_detections:
            label      = det["label"]
            confidence = det["confidence"]
            box        = det["box"]   # [x1,y1,x2,y2]

            roi_motion = self.motion.get_roi_motion(gray, box)
            result     = self.classifier.score(
                label, confidence, roi_motion, brightness)

            entry = {**result, "box": box, "roi_motion": round(roi_motion, 3)}
            detections.append(entry)

            if result["is_threat"]:
                alerts.append(entry)

        return {
            "detections":   detections,
            "alerts":       alerts,
            "frame_meta": {
                "width":      w,
                "height":     h,
                "brightness": round(brightness, 1),
                "motion":     round(motion, 3),
                "timestamp":  datetime.utcnow().isoformat(),
            },
        }

    def _run_yolo(self, frame: np.ndarray) -> list:
        if self._model is None:
            return self._mock_detections(frame)

        results = self._model(frame, verbose=False)[0]
        out = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in COCO_CATEGORY_MAP:
                continue
            label = COCO_CATEGORY_MAP[cls_id]
            conf  = float(box.conf[0])
            xyxy  = box.xyxy[0].tolist()
            out.append({"label": label, "confidence": conf, "box": xyxy})
        return out

    def _mock_detections(self, frame: np.ndarray) -> list:
        """Fallback when ultralytics is not installed."""
        return []

    # ── feedback API ─────────────────────────
    def confirm_threat(self, label: str, features: dict = None):
        self.classifier.record_feedback(label, True, features)

    def dismiss_threat(self, label: str, features: dict = None):
        self.classifier.record_feedback(label, False, features)

    def update_rule(self, key: str, value):
        return self.classifier.update_rule(key, value)

    def get_rules(self) -> dict:
        return dict(self.classifier.rules)

    def get_learned_biases(self) -> dict:
        return dict(self.classifier.learned_bias)
