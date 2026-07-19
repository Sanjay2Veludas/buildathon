import socket
import time
from enum import Enum

import yaml

from bridge import MCUBridge
from brain import analyze_event
from capture import capture_bundle
from speak import precache_lines, speak


class State(Enum):
    IDLE = "IDLE"
    EVENT = "EVENT"
    POINTING = "POINTING"
    CAPTURING = "CAPTURING"
    ANALYZING = "ANALYZING"
    RESPONDING = "RESPONDING"
    ACTION = "ACTION"
    FAULT = "FAULT"


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def network_ok(host: str, port: int, timeout_s: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def set_state_ui(bridge: MCUBridge, state: State) -> None:
    if state == State.IDLE:
        bridge.set_led("idle")
        bridge.lcd_text("IDLE", "Armed online")
    elif state == State.EVENT:
        bridge.set_led("event")
        bridge.lcd_text("EVENT", "Sound trigger")
    elif state == State.POINTING:
        bridge.set_led("event")
        bridge.lcd_text("POINTING", "Turret move")
    elif state == State.CAPTURING:
        bridge.set_led("event")
        bridge.lcd_text("CAPTURING", "Image+Audio")
    elif state == State.ANALYZING:
        bridge.set_led("event")
        bridge.lcd_text("ANALYZING", "Cloud request")
    elif state == State.RESPONDING:
        bridge.set_led("event")
        bridge.lcd_text("RESPONDING", "Speaking")
    elif state == State.ACTION:
        bridge.lcd_text("ACTION", "Applying tier")
    else:
        bridge.set_led("alarm")
        bridge.lcd_text("FAULT", "Cloud/network")


def apply_action(bridge: MCUBridge, severity: str) -> None:
    if severity == "benign":
        bridge.set_led("event")
    elif severity == "notable":
        bridge.set_led("alert")
    else:
        bridge.set_led("alarm")


def run() -> None:
    cfg = load_config("linux/config.yaml")

    bridge = MCUBridge(
        port=cfg["serial"]["port"],
        baud=cfg["serial"]["baud"],
        timeout_s=cfg["serial"]["timeout_s"],
    )

    bridge.set_threshold(int(cfg["sensors"]["trigger_threshold"]))
    bridge.set_armed(True)

    precache_lines(
        lines=[
            "System online and armed.",
            "Cloud analysis unavailable. Check network.",
            "Alert detected. Taking action.",
            "Notable event recorded.",
            "Benign sound detected.",
        ],
        cache_dir=cfg["audio"]["tts_cache_dir"],
        rate=int(cfg["audio"]["tts_rate"]),
        voice=str(cfg["audio"]["tts_voice"]),
    )

    state = State.IDLE
    set_state_ui(bridge, state)

    while True:
        evt = bridge.wait_event(timeout_s=0.1)
        if evt is None:
            time.sleep(0.01)
            continue

        state = State.EVENT
        set_state_ui(bridge, state)

        state = State.POINTING
        set_state_ui(bridge, state)
        pointed = bridge.point_turret(evt.bearing_deg, motion_timeout_s=float(cfg["turret"]["motion_timeout_s"]))

        state = State.CAPTURING
        set_state_ui(bridge, state)
        cap = capture_bundle(
            camera_index=int(cfg["capture"]["camera_index"]),
            artifacts_dir=str(cfg["capture"]["artifacts_dir"]),
            image_count=int(cfg["capture"]["image_count"]),
            image_width=int(cfg["capture"]["image_width"]),
            image_height=int(cfg["capture"]["image_height"]),
            image_gap_ms=int(cfg["capture"]["image_gap_ms"]),
            audio_seconds=int(cfg["capture"]["audio_seconds"]),
            input_device_hint=str(cfg["audio"]["input_device_hint"]),
        )

        host = str(cfg["network"]["check_host"])
        port = int(cfg["network"]["check_port"])
        timeout_s = float(cfg["network"]["check_timeout_s"])
        if (not pointed) or (not cap.ok) or (not network_ok(host, port, timeout_s)):
            state = State.FAULT
            set_state_ui(bridge, state)
            speak(
                text="Cloud analysis unavailable. Check network.",
                cache_dir=str(cfg["audio"]["tts_cache_dir"]),
                rate=int(cfg["audio"]["tts_rate"]),
                voice=str(cfg["audio"]["tts_voice"]),
            )
            time.sleep(1.0)
            state = State.IDLE
            set_state_ui(bridge, state)
            continue

        state = State.ANALYZING
        set_state_ui(bridge, state)
        result = analyze_event(
            images=cap.images,
            audio_path=cap.audio_path,
            model=str(cfg["brain"]["model"]),
            timeout_s=int(cfg["brain"]["timeout_s"]),
            max_tokens=int(cfg["brain"]["max_tokens"]),
            temperature=float(cfg["brain"]["temperature"]),
            retry_count=int(cfg["brain"]["retry_count"]),
        )

        state = State.RESPONDING
        set_state_ui(bridge, state)
        speak(
            text=result.spoken_response,
            cache_dir=str(cfg["audio"]["tts_cache_dir"]),
            rate=int(cfg["audio"]["tts_rate"]),
            voice=str(cfg["audio"]["tts_voice"]),
        )

        state = State.ACTION
        set_state_ui(bridge, state)
        apply_action(bridge, result.severity)
        time.sleep(0.8)

        state = State.IDLE
        set_state_ui(bridge, state)


if __name__ == "__main__":
    run()
