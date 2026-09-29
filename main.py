"""main.py - runs the complete prototype.
Keys: q/ESC quit | a auto/manual sim | w/s distance +/-2 m | 1-5 presets
      n toggle 'no radar target' | f toggle radar fault | m mute buzzer"""
import time
from datetime import datetime
import cv2
import numpy as np

import config
import camera
import detection
import radar
import risk_assessment as risk_mod
from sensor_fusion import fuse_camera_radar, select_primary
from logger import EventLogger

RISK_COLORS = {"LOW": (0, 200, 0), "MEDIUM": (0, 165, 255),
               "HIGH": (0, 0, 255), "SENSOR_FAULT": (0, 0, 255)}
FONT = cv2.FONT_HERSHEY_SIMPLEX


def text(img, s, x, y, scale=0.6, color=(255, 255, 255), thick=1):
    cv2.putText(img, s, (x, y), FONT, scale, color, thick, cv2.LINE_AA)


def build_panel(h, primary, radar_status, risk, alert, radar_sim):
    p = np.full((h, config.PANEL_WIDTH, 3), 30, np.uint8)
    text(p, "MINE VEHICLE SAFETY", 15, 30, 0.65, (255, 255, 255), 2)
    text(p, "SYSTEM - PROTOTYPE", 15, 55, 0.55, (180, 180, 180))
    cv2.line(p, (10, 65), (config.PANEL_WIDTH - 10, 65), (120, 120, 120), 1)

    obj = primary["label"] if primary else "None"
    conf = f"{primary['confidence']*100:.0f}%" if primary and primary["confidence"] > 0 else "--"
    d = primary["distance"] if primary else None
    dist = f"{d:.1f} m" if isinstance(d, float) else "UNKNOWN"
    src = primary["source"] if primary else "-"

    y = 95
    for title, val, col in [("Object:", obj, (255, 255, 255)),
                            ("Confidence:", conf, (255, 255, 255)),
                            ("Radar Distance:", dist, (255, 255, 0)),
                            ("Source:", src, (200, 200, 200)),
                            ("Risk:", risk, RISK_COLORS.get(risk, (255, 255, 255))),
                            ("Alert:", alert["message"], alert["color"]),
                            ("Radar Status:", radar_status,
                             (0, 0, 255) if radar_status in ("ERROR", "DISCONNECTED") else (0, 255, 0))]:
        text(p, title, 15, y, 0.5, (160, 160, 160))
        text(p, str(val), 15, y + 24, 0.7, col, 2)
        y += 58
    if radar_sim:
        text(p, "SIMULATED RADAR", 15, h - 15, 0.6, (0, 255, 255), 2)
    return p


def main():
    camera.init_camera()
    if not detection.load_model():
        print("[MAIN] Running WITHOUT detection (model missing). Radar-only mode.")
    logger = EventLogger()
    sim = config.SIMULATION_MODE
    fps, t_prev = 0.0, time.time()

    while True:
        # 1. camera + enhancement
        frame = camera.capture_camera_frame()
        cam_ok = frame is not None
        if cam_ok:
            frame = camera.enhance_frame(frame)
        else:
            frame = np.zeros((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), np.uint8)
            text(frame, "CAMERA NOT AVAILABLE - retrying...", 60, config.FRAME_HEIGHT // 2, 0.8, (0, 0, 255), 2)

        # 2. detection
        detections = detection.detect_objects(frame) if cam_ok else []

        # 3. radar (read right after the frame so both are ~same instant)
        radar_data = radar.read_radar_data()
        radar_status = radar.get_radar_status()
        radar_ok = radar_status in ("CONNECTED", "SIMULATED")

        # 4. fusion
        fused = fuse_camera_radar(detections, radar_data, frame.shape[1])
        primary = select_primary(fused)

        # 5. risk + alert
        distance = primary["distance"] if primary else None
        risk = risk_mod.calculate_risk(distance, bool(detections), radar_ok)
        alert = risk_mod.generate_alert(risk)

        # 6. log
        logger.log(fused, radar_data, risk, alert["status"])

        # 7. draw dashboard
        detection.draw_fused_objects(frame, fused)
        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(now - t_prev, 1e-6))
        t_prev = now
        if not detection.model_ready():
            text(frame, "YOLO MODEL MISSING", 10, 25, 0.7, (0, 0, 255), 2)
        if risk == "HIGH" and int(now * 4) % 2 == 0:       # flashing border
            cv2.rectangle(frame, (0, 0), (frame.shape[1] - 1, frame.shape[0] - 1), (0, 0, 255), 8)
        bar = f"FPS {fps:4.1f} | {datetime.now():%Y-%m-%d %H:%M:%S} | Objects: {len(detections)}"
        cv2.rectangle(frame, (0, frame.shape[0] - 26), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
        text(frame, bar, 8, frame.shape[0] - 8, 0.5)
        if sim:
            text(frame, "SIMULATED RADAR", frame.shape[1] - 210, 25, 0.65, (0, 255, 255), 2)

        panel = build_panel(frame.shape[0], primary, radar_status, risk, alert, sim)
        cv2.imshow(config.WINDOW_NAME, np.hstack((frame, panel)))

        # 8. keyboard
        k = cv2.waitKey(1) & 0xFF
        if k in (ord("q"), 27):
            break
        if sim:
            if k == ord("a"): radar.sim_toggle_auto()
            elif k == ord("w"): radar.sim_adjust(+2)
            elif k == ord("s"): radar.sim_adjust(-2)
            elif k in [ord(str(i)) for i in range(1, 6)]: radar.sim_preset(k - ord("1"))
            elif k == ord("n"): radar.sim_toggle_no_target()
            elif k == ord("f"): radar.sim_toggle_fault()
        if k == ord("m"):
            risk_mod.muted = not risk_mod.muted

    camera.release_camera()
    radar.close_radar()
    logger.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
