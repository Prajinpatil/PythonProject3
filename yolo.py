import cv2
import numpy as np
from ultralytics import YOLO
model = YOLO('yolov8s.pt')
camera = cv2.VideoCapture(0)
# 2. Configuration
TARGET_LABELS = ['person', 'dog', 'cat', 'car']
ALERT_COOLDOWN = 30  # Only print alert every 30 frames to avoid spamming
frame_count = 0
print(f"System Active. Monitoring for: {TARGET_LABELS}")
print("Press 'q' to quit.")
while True:
    ret, frame = camera.read()
    if not ret:
        print("Failed to grab frame.")
        break
    frame_count += 1
    h, w, _ = frame.shape
    minDim = min(h, w)
    start_x = (w - minDim) // 2
    start_y = (h - minDim) // 2
    # Center Crop and Resize
    cropped = frame[start_y:start_y + minDim, start_x:start_x + minDim]
    resized = cv2.resize(cropped, (640, 640))
    # Gaussian Blur (helps ignore sensor noise)
    blurred = cv2.GaussianBlur(resized, (5, 5), 0)
    # STEP 2: YOLO DETECTION

    results = model(blurred, verbose=False, stream=True)
    # STEP 3:  ALERTS
    for result in results:

        detected_classes = result.boxes.cls.cpu().numpy()
        for class_id in detected_classes:
            label = model.names[int(class_id)]

            if label in TARGET_LABELS:

                if frame_count % ALERT_COOLDOWN == 0:
                    print(f">>> ALERT: {label.upper()} detected!")
        # STEP 4: VISUALS
        annotated_frame = result.plot()
        cv2.imshow('Security Monitor', annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
camera.release()
cv2.destroyAllWindows()