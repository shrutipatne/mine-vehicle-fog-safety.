"""sensor_fusion.py - combine camera detections with radar distance.

Camera answers "WHAT is it?", radar answers "HOW FAR?".
Distance is NEVER estimated from bounding-box size."""
import config


def _in_corridor(center, frame_width):
    half = frame_width * config.CENTER_CORRIDOR_FRACTION / 2
    return abs(center[0] - frame_width / 2) <= half


def _area(det):
    x1, y1, x2, y2 = det["bbox"]
    return (x2 - x1) * (y2 - y1)


def fuse_camera_radar(detections, radar_data, frame_width=config.FRAME_WIDTH):
    """Return a list of fused objects with keys:
    label, confidence, bbox, center, distance (float or "UNKNOWN"), velocity, source.
    source is CAMERA+RADAR, CAMERA ONLY or RADAR OBSTACLE."""
    dist = radar_data.get("distance")
    vel = radar_data.get("velocity")
    radar_ok = isinstance(dist, (int, float))

    fused = []
    # Radar has no bearing here: give its distance to the largest detection
    # inside the central "vehicle path" corridor.
    target = None
    if radar_ok:
        candidates = [d for d in detections if _in_corridor(d["center"], frame_width)]
        if candidates:
            target = max(candidates, key=_area)

    for det in detections:
        matched = radar_ok and det is target
        fused.append({
            "label": det["label"], "confidence": det["confidence"],
            "bbox": det["bbox"], "center": det["center"],
            "distance": float(dist) if matched else "UNKNOWN",   # never invented
            "velocity": vel if matched else None,
            "source": "CAMERA+RADAR" if matched else "CAMERA ONLY",
        })

    # Radar sees something but the camera has no object in the path
    if radar_ok and target is None:
        fused.append({
            "label": "UNKNOWN", "confidence": 0.0, "bbox": None, "center": None,
            "distance": float(dist), "velocity": vel, "source": "RADAR OBSTACLE",
        })
    return fused


def select_primary(fused):
    """Most important object: nearest known distance, else most confident camera object."""
    if not fused:
        return None
    with_dist = [o for o in fused if isinstance(o["distance"], float)]
    if with_dist:
        return min(with_dist, key=lambda o: o["distance"])
    return max(fused, key=lambda o: o["confidence"])
