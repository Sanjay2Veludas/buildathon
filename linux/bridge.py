import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import serial


@dataclass
class Event:
    bearing_deg: float
    amplitudes: list[int]
    timestamp_ms: int


class MCUBridge:
    def __init__(self, port: str, baud: int, timeout_s: float = 0.2) -> None:
        self._ser = serial.Serial(port=port, baudrate=baud, timeout=timeout_s)

    def close(self) -> None:
        if self._ser.is_open:
            self._ser.close()

    def _send(self, command: str) -> None:
        payload = (command + "\n").encode("utf-8")
        self._ser.write(payload)

    def _read_json(self, deadline_s: float) -> Optional[Dict[str, Any]]:
        end = time.monotonic() + deadline_s
        while time.monotonic() < end:
            line = self._ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        return None

    def wait_event(self, timeout_s: float = 0.1) -> Optional[Event]:
        msg = self._read_json(timeout_s)
        if msg is None:
            return None
        if msg.get("type") != "event":
            return None
        return Event(
            bearing_deg=float(msg.get("bearing_deg", 0.0)),
            amplitudes=[int(msg.get("a0", 0)), int(msg.get("a1", 0)), int(msg.get("a2", 0))],
            timestamp_ms=int(msg.get("ts", 0)),
        )

    def point_turret(self, deg: float, motion_timeout_s: float) -> bool:
        self._send(f"point_turret deg={deg:.2f}")
        end = time.monotonic() + motion_timeout_s
        while time.monotonic() < end:
            msg = self._read_json(0.2)
            if msg is None:
                continue
            if msg.get("type") == "motion_complete":
                return True
        return False

    def set_led(self, level: str) -> None:
        map_level = {"idle": 0, "event": 1, "alert": 2, "alarm": 3}
        value = map_level.get(level, 0)
        self._send(f"set_led level={value}")

    def lcd_text(self, line1: str, line2: str) -> None:
        safe1 = line1.replace('"', "")[:16]
        safe2 = line2.replace('"', "")[:16]
        self._send(f'lcd_text l1="{safe1}" l2="{safe2}"')

    def set_armed(self, armed: bool) -> None:
        self._send(f"set_armed armed={1 if armed else 0}")

    def set_threshold(self, value: int) -> None:
        self._send(f"set_threshold value={value}")
