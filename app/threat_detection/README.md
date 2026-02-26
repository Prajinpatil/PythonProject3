# ThreatVision – ML Threat Detection Module
# Drop into any Flask/Django project

## Quick Start

### 1. Install dependencies
```bash
pip install flask ultralytics opencv-python numpy
# For GPU (optional but faster):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. Add to your Flask app
```python
from threat_detection.routes import threat_bp
app.register_blueprint(threat_bp, url_prefix="/threat")
```

### 3. Add to your HTML page
```html
<script src="/static/ThreatVision.js"></script>
<script>
  const tv = new ThreatVision({ apiBase: '/threat' });
  tv.start();
</script>
```

---

## Architecture

```
Browser (webcam)
    │
    │  POST /threat/frame  (base64 JPEG @ 4-5fps)
    ▼
Flask Backend
    ├── YOLOv8 (nano by default)          → detects persons/animals/birds
    ├── MotionTracker (frame-diff)        → per-object motion score
    └── ThreatClassifier                  → rule-based score + learned bias
            │
            │  is_threat?  score >= alert_threshold
            ▼
    Response JSON  →  Frontend draws boxes, shows alerts
            │
            │  User clicks Confirm/Dismiss
            ▼
    POST /threat/feedback  →  model nudges per-label bias (online learning)
```

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/threat/frame` | POST | Analyse a frame |
| `/threat/feedback` | POST | Confirm/dismiss an alert |
| `/threat/rules` | GET | Get current rules |
| `/threat/rules` | POST | Update a rule |
| `/threat/stats` | GET | Learned biases & feedback |
| `/threat/stream` | GET | MJPEG webcam stream (dev) |

### POST /threat/frame
```json
{ "frame": "<base64 JPEG>", "annotate": false }
```
Response:
```json
{
  "detections": [
    { "label": "person", "confidence": 0.92, "threat_score": 0.81,
      "is_threat": true, "reason": "human detected, fast motion",
      "box": [120, 80, 340, 460], "roi_motion": 0.6 }
  ],
  "alerts": [ /* same objects where is_threat=true */ ],
  "frame_meta": { "brightness": 105, "motion": 0.52, "timestamp": "..." }
}
```

### POST /threat/feedback
```json
{ "label": "person", "is_threat": false }
```
This slowly shifts the learned bias so future detections of this label
become less/more likely to trigger.

### POST /threat/rules (user-defined rules)
```json
{ "key": "alert_threshold", "value": 0.65 }
```
All settable keys:
- `alert_threshold` – score above which = threat (default 0.55)
- `person_base_score` – starting score for humans (0.6)
- `animal_base_score` – starting score for animals (0.3)
- `bird_base_score` – starting score for birds (0.1)
- `motion_weight` – how much fast motion boosts score (0.25)
- `night_weight` – boost in low-light conditions (0.10)
- `fast_motion_threshold` – motion score to trigger boost (0.45)
- `unknown_boost` – extra score for unrecognised persons (0.20)
- `known_safe_penalty` – reduction for user-marked-safe labels (0.30)
- `confidence_min` – ignore detections below this confidence (0.40)

---

## Learning Loop

Every Confirm/Dismiss button click sends feedback to the server:
```
new_bias = old_bias + 0.05 * (target - old_bias)
```
- Confirm threat → bias nudges +0.2
- Dismiss alert  → bias nudges -0.2, label added to `known_safe`

Biases are persisted to `data/learned_weights.pkl` and survive restarts.

---

## Configuration
```python
app.config["THREAT_MODEL_SIZE"] = "n"   # n / s / m / l / x
app.config["THREAT_DEVICE"]     = "cpu" # cpu / cuda / mps
```

Model sizes:
| Size | Speed | Accuracy |
|------|-------|----------|
| n    | ~30ms | Good     |
| s    | ~50ms | Better   |
| m    | ~90ms | Great    |
| l/x  | slow  | Best     |
