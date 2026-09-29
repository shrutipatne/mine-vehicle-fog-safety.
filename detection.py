"""detection.py - YOLO object detection and box drawing.

NOTE: A pretrained COCO model does NOT reliably recognise mine dumpers, haul
trucks or mine-specific obstacles, especially in fog. A custom mine dataset and
fine-tuning are REQUIRED for reliable use (see README.md, section 11)."""
import cv2
import config

_model = None


def load_model():
    """Load YOLO. Returns True/False - never crashes if the model is missing."""
    global _model
    try:
        from ultralytics import YOLO
        _model = YOLO(config.YOLO_MODEL_PATH)
        print(f"[YOLO] Loaded {config.YOLO_MODEL_PATH}")
        return True
    except Exception as e:      # missing file, no internet, old ultralytics...
        print(f"[YOLO] Could not load '{config.YOLO_MODEL_PATH}': {e}")
        _model = None
        return False


def model_ready():
    return _model is not None


def detect_objects(frame):
    """Run YOLO on one frame.
    Returns list of dicts: class, label, confidence, bbox(x1,y1,x2,y2), center(cx,cy)."""
    if _model is None or frame is None:
        return []
    try:
        results = _model.predict(frame, imgsz=config.INFERENCE_IMG_SIZE,
                                 conf=config.CONF_THRESHOLD, verbose=False)
    except Exception as e:
        print(f"[YOLO] Inference error: {e}")
        return []

    detections = []
    for box in results[0].boxes:
        name = _model.names[int(box.cls[0])]
        if not config.DETECT_ALL_CLASSES and name not in config.RELEVANT_CLASSES:
            continue
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        detections.append({
            "class": name,
            "label": config.DISPLAY_NAMES.get(name, name.title()),
            "confidence": float(box.conf[0]),
            "bbox": (x1, y1, x2, y2),
            "center": ((x1 + x2) // 2, (y1 + y2) // 2),
        })
    return detections


def draw_fused_objects(frame, fused):
    """Draw boxes + labels (with radar distance if known) on the frame."""
    for obj in fused:
        if obj["bbox"] is None:
            continue
        x1, y1, x2, y2 = obj["bbox"]
        d = obj["distance"]
        has_d = isinstance(d, float)
        color = (0, 200, 255) if has_d else (200, 200, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        dist_txt = f"{d:.1f}m" if has_d else "dist ?"
        text = f"{obj['label']} {obj['confidence']*100:.0f}% {dist_txt}"
        cv2.putText(frame, text, (x1, max(15, y1 - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        cv2.circle(frame, obj["center"], 3, color, -1)
    return frame
