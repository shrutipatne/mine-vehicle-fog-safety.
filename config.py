"""
config.py - ALL settings and thresholds in one place.
PROTOTYPE ONLY: values are demo values, NOT certified mine-safety thresholds.
"""

# ---------------- CAMERA ----------------
CAMERA_SOURCE = 0            # 0 = webcam, or "video.mp4" for a recorded video
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_RETRY_SECONDS = 3.0   # how often to retry a disconnected camera
ENABLE_ENHANCEMENT = True    # CLAHE contrast enhancement (does NOT remove dense fog)
CLAHE_CLIP_LIMIT = 3.0
CLAHE_TILE_GRID = (8, 8)
ENHANCE_GAMMA = 0.9          # <1 brightens slightly, 1.0 = off

# ---------------- YOLO ----------------
YOLO_MODEL_PATH = "yolo26n.pt"   # replace with your fine-tuned mine model later
CONF_THRESHOLD = 0.40
INFERENCE_IMG_SIZE = 416         # smaller = faster, less accurate
DETECT_ALL_CLASSES = False       # True = treat every COCO class as an obstacle
# COCO classes used as a stand-in. A pretrained model does NOT know mine dumpers.
RELEVANT_CLASSES = {"person", "bicycle", "car", "motorcycle", "bus", "truck"}
DISPLAY_NAMES = {"truck": "Truck/Dumper", "car": "Car/Vehicle", "bus": "Bus/Vehicle",
                 "person": "Person", "motorcycle": "Motorcycle", "bicycle": "Bicycle"}

# ---------------- RADAR ----------------
SIMULATION_MODE = True           # True = no hardware needed
SERIAL_PORT = "COM3"             # Linux example: "/dev/ttyUSB0"
SERIAL_BAUD = 115200             # PLACEHOLDER - use your radar's datasheet value
SERIAL_TIMEOUT = 0.05
RADAR_RECONNECT_SECONDS = 3.0
RADAR_MIN_RANGE = 0.5            # meters; below this = invalid
RADAR_MAX_RANGE = 200.0          # meters; above this = invalid
RADAR_STALE_SECONDS = 1.0        # older readings are discarded (sync safeguard)

# Simulation behaviour
SIM_SEQUENCE = [60.0, 40.0, 25.0, 15.0, 8.0]   # demo distances (m)
SIM_SPEED = 6.0                  # m/s the simulated obstacle moves
SIM_DWELL_SECONDS = 2.0          # pause at each waypoint

# ---------------- FUSION ----------------
# A single-beam radar has no bearing, so its distance is assigned to the
# object inside the central "vehicle path" corridor of the image.
CENTER_CORRIDOR_FRACTION = 0.5   # central 50% of image width

# ---------------- RISK (PROTOTYPE VALUES) ----------------
WARNING_DISTANCE = 25.0          # meters -> MEDIUM
CRITICAL_DISTANCE = 10.0         # meters -> HIGH

# ---------------- ALERT ----------------
BUZZER_ENABLED = True            # PC beep (Windows) / terminal bell (others)
MEDIUM_BEEP_INTERVAL = 2.0       # seconds
HIGH_BEEP_INTERVAL = 0.4         # seconds (simulates continuous alarm)

# ---------------- LOGGING ----------------
LOG_FILE = "safety_log.csv"
LOG_INTERVAL_SECONDS = 2.0       # repeat-log interval while risk != LOW

# ---------------- DISPLAY ----------------
WINDOW_NAME = "MINE VEHICLE SAFETY SYSTEM (PROTOTYPE)"
PANEL_WIDTH = 340
