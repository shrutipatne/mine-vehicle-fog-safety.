"""risk_assessment.py - LOW/MEDIUM/HIGH risk and operator alerts.
Warnings ONLY - this code never sends any vehicle-control command.
Thresholds are prototype values, NOT certified mine-safety limits."""
import sys
import threading
import time
import config

# ------------------------------ RISK ------------------------------
def calculate_risk(distance, object_detected, radar_ok=True):
    """distance: meters, None or "UNKNOWN". object_detected: camera saw something.
    (An obstacle exists if radar has a distance, whatever the camera says.)"""
    if not radar_ok:
        return "SENSOR_FAULT"
    if not isinstance(distance, (int, float)):
        return "LOW"                     # no valid obstacle distance
    if distance <= config.CRITICAL_DISTANCE:
        return "HIGH"
    if distance <= config.WARNING_DISTANCE:
        return "MEDIUM"
    return "LOW"


# ------------------------------ ALERT ------------------------------
_last_beep = 0.0
_last_status = None
muted = False


def _buzz(freq, ms):
    """Non-blocking beep. Replace with GPIO code for a real buzzer (e.g. Raspberry Pi)."""
    def run():
        try:
            import winsound
            winsound.Beep(freq, ms)
        except ImportError:
            sys.stdout.write("\a")
            sys.stdout.flush()
    threading.Thread(target=run, daemon=True).start()


def generate_alert(risk_level):
    """Return {"status", "message", "color"} and trigger the (simulated) buzzer."""
    global _last_beep, _last_status
    now = time.time()
    beep_gap = None
    if risk_level == "HIGH":
        alert = {"status": "COLLISION_WARNING", "message": "COLLISION WARNING", "color": (0, 0, 255)}
        beep_gap, freq, ms = config.HIGH_BEEP_INTERVAL, 1800, 300
    elif risk_level == "MEDIUM":
        alert = {"status": "OBSTACLE_WARNING", "message": "CAUTION: OBSTACLE AHEAD", "color": (0, 165, 255)}
        beep_gap, freq, ms = config.MEDIUM_BEEP_INTERVAL, 1000, 120
    elif risk_level == "SENSOR_FAULT":
        alert = {"status": "SENSOR_FAULT", "message": "RADAR SENSOR FAULT", "color": (0, 0, 255)}
    else:
        alert = {"status": "NORMAL", "message": "NORMAL", "color": (0, 200, 0)}

    if beep_gap and config.BUZZER_ENABLED and not muted and now - _last_beep >= beep_gap:
        _last_beep = now
        _buzz(freq, ms)

    if alert["status"] != _last_status:          # print only on change
        _last_status = alert["status"]
        print(f"[ALERT] {alert['message']}")
    return alert
