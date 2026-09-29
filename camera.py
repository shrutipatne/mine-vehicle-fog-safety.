"""camera.py - camera capture and simple fog-oriented image enhancement."""
import time
import cv2
import numpy as np
import config

_cap = None
_last_retry = 0.0


def init_camera():
    """Open the camera/video source. Returns True on success."""
    global _cap
    if _cap is not None:
        _cap.release()
    _cap = cv2.VideoCapture(config.CAMERA_SOURCE)
    if not _cap.isOpened():
        print(f"[CAMERA] Cannot open source: {config.CAMERA_SOURCE}")
        _cap = None
        return False
    print(f"[CAMERA] Opened source: {config.CAMERA_SOURCE}")
    return True


def capture_camera_frame():
    """Return the current resized frame, or None if the camera is unavailable.
    Never raises: a camera problem must not crash the whole program."""
    global _cap, _last_retry
    if _cap is None:                      # try to reconnect periodically
        if time.time() - _last_retry > config.CAMERA_RETRY_SECONDS:
            _last_retry = time.time()
            init_camera()
        return None
    try:
        ok, frame = _cap.read()
        if not ok and isinstance(config.CAMERA_SOURCE, str):
            _cap.set(cv2.CAP_PROP_POS_FRAMES, 0)      # loop recorded video
            ok, frame = _cap.read()
        if not ok or frame is None or frame.size == 0:
            print("[CAMERA] Invalid frame - releasing camera for retry.")
            _cap.release()
            _cap = None
            return None
        return cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT))
    except cv2.error as e:
        print(f"[CAMERA] OpenCV error: {e}")
        _cap = None
        return None


def enhance_frame(frame):
    """CLAHE on the lightness channel + mild gamma.
    This improves local contrast only. It does NOT remove dense fog."""
    if not config.ENABLE_ENHANCEMENT:
        return frame
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=config.CLAHE_CLIP_LIMIT,
                            tileGridSize=config.CLAHE_TILE_GRID)
    out = cv2.cvtColor(cv2.merge((clahe.apply(l), a, b)), cv2.COLOR_LAB2BGR)
    if config.ENHANCE_GAMMA != 1.0:
        table = np.array([((i / 255.0) ** config.ENHANCE_GAMMA) * 255
                          for i in range(256)]).astype("uint8")
        out = cv2.LUT(out, table)
    return out


def release_camera():
    global _cap
    if _cap is not None:
        _cap.release()
        _cap = None
