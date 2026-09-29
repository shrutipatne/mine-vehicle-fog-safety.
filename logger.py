"""logger.py - CSV event logger (no raw video frames are stored)."""
import csv
import os
import time
from datetime import datetime
import config

HEADER = ["timestamp", "object_class", "confidence", "radar_distance",
          "radar_velocity", "risk_level", "alert_status"]


class EventLogger:
    def __init__(self, path=config.LOG_FILE):
        self.path = path
        self._last_sig = None
        self._last_time = 0.0
        try:
            new = not os.path.exists(path)
            self._f = open(path, "a", newline="", encoding="utf-8")
            self._w = csv.writer(self._f)
            if new:
                self._w.writerow(HEADER)
                self._f.flush()
        except OSError as e:
            print(f"[LOG] Cannot open log file: {e}")
            self._f = None

    def log(self, fused, radar_data, risk, alert_status):
        """Log on change of (objects, risk, alert) or every LOG_INTERVAL while risk != LOW."""
        if self._f is None:
            return
        rows_src = fused or [{"label": "none", "confidence": 0.0, "distance": None}]
        sig = (tuple(o["label"] for o in rows_src), risk, alert_status)
        now = time.time()
        changed = sig != self._last_sig
        repeat = risk != "LOW" and now - self._last_time >= config.LOG_INTERVAL_SECONDS
        if not (changed or repeat):
            return
        if not fused and risk == "LOW" and not changed:
            return
        self._last_sig, self._last_time = sig, now
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        d = radar_data.get("distance")
        v = radar_data.get("velocity")
        try:
            for o in rows_src:
                self._w.writerow([ts, o["label"], round(o["confidence"], 2),
                                  "" if d is None else d, "" if v is None else v,
                                  risk, alert_status])
            self._f.flush()
        except OSError as e:
            print(f"[LOG] Write error: {e}")

    def close(self):
        if self._f:
            self._f.close()


def load_log_summary(path=config.LOG_FILE):
    """Small pandas helper: count events per risk level."""
    import pandas as pd
    df = pd.read_csv(path)
    return df.groupby("risk_level").size()
