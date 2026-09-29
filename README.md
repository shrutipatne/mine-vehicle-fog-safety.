# Mine Vehicle Fog-Safety Prototype (SIH 2026)

**PROTOTYPE FOR DEMONSTRATION/SIMULATION ONLY.** Not validated in any operating mine, not a certified
safety system. The 25 m / 10 m thresholds are demo values. The system only shows warnings; it never
controls the vehicle.

## Install & run
    pip install opencv-python numpy ultralytics pyserial pandas
    python main.py
Works with no radar (`SIMULATION_MODE = True`). Use a video file: `CAMERA_SOURCE = "fog_test.mp4"`.

## Keys
q/ESC quit | a auto/manual | w/s distance +/-2 m | 1-5 presets (60/40/25/15/8 m) |
n no radar target | f radar fault | m mute buzzer

## Files
- config.py          -> all thresholds and settings
- camera.py          -> camera capture, reconnect, CLAHE enhancement
- detection.py       -> YOLO26n detection, box drawing
- radar.py           -> serial radar input + simulation + placeholder parser
- sensor_fusion.py   -> camera + radar integration
- risk_assessment.py -> LOW/MEDIUM/HIGH risk + alert/buzzer
- logger.py          -> CSV logging
- main.py            -> runs everything, draws the dashboard

## Block diagram / data flow
    Camera -> capture_camera_frame() -> enhance_frame() (CLAHE) -> detect_objects() (YOLO)
                                                                        |
    Radar  -> read_radar_data() ---------------------------> fuse_camera_radar()
                                                                        |
                                              calculate_risk() -> generate_alert()
                                                                        |
                                            OpenCV dashboard + buzzer + CSV log

## Explanation
1. **Camera:** cv2.VideoCapture reads frames continuously; each is resized (640x480). If the camera fails,
   the program shows "CAMERA NOT AVAILABLE" and retries every few seconds.
2. **OpenCV processing:** frame -> LAB colour; CLAHE on lightness channel + mild gamma. This improves local
   contrast only; it does NOT remove dense fog.
3. **YOLO:** YOLO26n runs on the frame at a configurable size/confidence, returning class, confidence, box and
   centre. The pretrained COCO model does not know mine dumpers (truck is a stand-in); mine-specific
   fine-tuning is required.
4. **Radar:** returns nearest-obstacle distance (m) and optional velocity (m/s). Readings outside min/max
   range or older than 1 s are discarded.
5. **Synchronisation:** the radar is read immediately after each frame is processed; stale radar data is
   dropped. For real hardware, use timestamps on both streams.
6. **Fusion:** radar gives distance, camera gives identity. A single-beam radar has no bearing, so its
   distance is assigned to the largest detection in the central vehicle-path corridor. Other objects:
   distance "UNKNOWN". Radar reading with no camera object: "RADAR OBSTACLE", identity UNKNOWN.
   Distance is never estimated from box size.
7. **Risk:** distance > 25 m LOW; 10-25 m MEDIUM; <= 10 m HIGH; no valid distance LOW; invalid radar
   SENSOR_FAULT.
8. **Alert:** LOW normal; MEDIUM warning + short beep; HIGH flashing border, "COLLISION WARNING" + repeated
   beep; fault message. Also printed in the terminal. Replace `_buzz()` with GPIO code for a real buzzer.
9. **Storage:** safety_log.csv (timestamp, object_class, confidence, radar_distance, radar_velocity,
   risk_level, alert_status), written on change or every 2 s while risk is not LOW. No frames saved.
10. **Real radar:** set `SIMULATION_MODE=False`, `SERIAL_PORT`, `SERIAL_BAUD`; implement
    `parse_radar_packet()` in radar.py from the datasheet (sync bytes, checksum, scaling to metres).
    Adapt `readline()` if the radar uses binary frames.
11. **Training YOLO:** collect real mine images/video (dumpers, excavators, people, light vehicles) in clear,
    fog, dust, dusk conditions; label with CVAT/Roboflow; split train/val/test by *site/day*;
    `yolo detect train data=mine.yaml model=yolo26n.pt imgsz=640 epochs=100`; evaluate per class and per
    visibility condition; set `YOLO_MODEL_PATH` to the new `best.pt`.
12. **Safe testing:** use recorded fog videos, a webcam with a toy/printed vehicle, and the keyboard-driven
    simulated radar. For hardware, test bench-top or on a closed area with a stationary target, never on a
    live haul road.

## Separation of scope
- **Prototype (implemented):** camera, CLAHE, YOLO, simulated/serial radar, fusion, risk, alerts, logging.
- **Research concepts (not implemented):** learned defogging/dehazing, camera-radar calibration and
  tracking (Kalman filter), thermal cameras, time-to-collision.
- **Real deployment requires:** mine dataset, calibrated radar, hardware timestamps, rugged/IP-rated
  hardware, false-alarm/miss-rate testing, functional-safety certification, DGMS/regulatory approval, and
  operator training.
