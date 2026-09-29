"""radar.py - radar input (real serial OR simulation).

Returns {"distance": meters or None, "velocity": m/s or None}.
No radar brand, packet format or baud rate is assumed."""
import time
import config

# =========================== SIMULATION STATE ===========================
_sim = {"dist": config.SIM_SEQUENCE[0], "idx": 0, "auto": True,
        "dwell_until": 0.0, "last_t": time.time(),
        "no_target": False, "fault": False, "velocity": 0.0}

# ============================ REAL RADAR STATE ==========================
_ser = None
_last_reading = None          # (distance, velocity, timestamp)
_status = "SIMULATED" if config.SIMULATION_MODE else "DISCONNECTED"
_last_connect_try = 0.0


# ------------------------- simulation controls -------------------------
def sim_adjust(delta):
    """Manually change simulated distance (switches to manual mode)."""
    _sim["auto"] = False
    _sim["dist"] = max(config.RADAR_MIN_RANGE, min(config.RADAR_MAX_RANGE, _sim["dist"] + delta))


def sim_preset(index):
    _sim["auto"] = False
    _sim["dist"] = config.SIM_SEQUENCE[index % len(config.SIM_SEQUENCE)]


def sim_toggle_auto():
    _sim["auto"] = not _sim["auto"]


def sim_toggle_no_target():
    _sim["no_target"] = not _sim["no_target"]


def sim_toggle_fault():
    _sim["fault"] = not _sim["fault"]


def sim_is_auto():
    return _sim["auto"]


def _simulate():
    now = time.time()
    dt = now - _sim["last_t"]
    _sim["last_t"] = now
    old = _sim["dist"]
    if _sim["auto"] and now >= _sim["dwell_until"]:
        target = config.SIM_SEQUENCE[_sim["idx"]]
        step = config.SIM_SPEED * dt
        if abs(target - _sim["dist"]) <= step:
            _sim["dist"] = target
            _sim["idx"] = (_sim["idx"] + 1) % len(config.SIM_SEQUENCE)
            _sim["dwell_until"] = now + config.SIM_DWELL_SECONDS
        else:
            _sim["dist"] += step if target > _sim["dist"] else -step
    _sim["velocity"] = (_sim["dist"] - old) / dt if dt > 0 else 0.0   # negative = approaching
    return _sim["dist"], _sim["velocity"]


# =============== >>> REAL RADAR PROTOCOL GOES HERE <<< ================
def parse_radar_packet(raw_bytes):
    """PLACEHOLDER PARSER - replace with your radar's real protocol.

    Input : raw bytes from the serial port (one read).
    Output: (distance_m, velocity_mps) or None if the packet is invalid.

    Steps for a real radar (see its datasheet):
      1. Find the header/sync bytes, check packet length.
      2. Verify checksum/CRC.
      3. Decode distance (and velocity) with the correct scale factor/units.
      4. Return the values in METERS and M/S.

    Example ONLY (assumes ASCII lines like "D:14.5,V:-1.2"; a made-up format):
        text = raw_bytes.decode(errors="ignore").strip()
        d, v = text.split(",")
        return float(d.split(":")[1]), float(v.split(":")[1])
    """
    return None       # default: nothing decoded until you implement the parser
# ======================================================================


def _connect_serial():
    global _ser, _status, _last_connect_try
    _last_connect_try = time.time()
    try:
        import serial
        _ser = serial.Serial(config.SERIAL_PORT, config.SERIAL_BAUD,
                             timeout=config.SERIAL_TIMEOUT)
        _status = "CONNECTED"
        print(f"[RADAR] Connected on {config.SERIAL_PORT}")
    except Exception as e:
        _ser = None
        _status = "ERROR"
        print(f"[RADAR] Serial connect failed: {e}")


def _valid(d):
    return isinstance(d, (int, float)) and config.RADAR_MIN_RANGE <= d <= config.RADAR_MAX_RANGE


def read_radar_data():
    """Return {"distance": value_or_None, "velocity": value_or_None}."""
    global _ser, _status, _last_reading

    if config.SIMULATION_MODE:
        if _sim["fault"]:
            _status = "ERROR"
            return {"distance": None, "velocity": None}
        _status = "SIMULATED"
        d, v = _simulate()
        if _sim["no_target"]:
            return {"distance": None, "velocity": None}
        return {"distance": round(d, 1), "velocity": round(v, 1)}

    # ---- real hardware ----
    if _ser is None:
        if time.time() - _last_connect_try > config.RADAR_RECONNECT_SECONDS:
            _connect_serial()
        return {"distance": None, "velocity": None}
    try:
        raw = _ser.readline()                 # adapt to your protocol (read(n), etc.)
        if raw:
            parsed = parse_radar_packet(raw)
            if parsed and _valid(parsed[0]):
                _last_reading = (parsed[0], parsed[1], time.time())
    except Exception as e:                    # serial.SerialException, unplug, etc.
        print(f"[RADAR] Serial error: {e}")
        try:
            _ser.close()
        except Exception:
            pass
        _ser = None
        _status = "ERROR"
        _last_reading = None
        return {"distance": None, "velocity": None}

    if _last_reading and time.time() - _last_reading[2] <= config.RADAR_STALE_SECONDS:
        return {"distance": _last_reading[0], "velocity": _last_reading[1]}
    return {"distance": None, "velocity": None}       # stale/no data


def get_radar_status():
    """'SIMULATED' / 'CONNECTED' / 'ERROR' / 'DISCONNECTED'."""
    return _status


def close_radar():
    global _ser
    if _ser is not None:
        try:
            _ser.close()
        except Exception:
            pass
        _ser = None
