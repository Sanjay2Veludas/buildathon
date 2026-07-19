import socket
import threading
import time
from enum import Enum
from pathlib import Path

import yaml

from bridge import MCUBridge
from brain import analyze_event, transcribe_audio
from capture import capture_photos, record_audio
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
        bridge.lcd_text("CAPTURING", "Image+Transcribe")
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
    cfg = load_config(str(Path(__file__).parent / "config.yaml"))

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

        capture_cfg = cfg["capture"]
        audio_cfg = cfg["audio"]
        brain_cfg = cfg["brain"]

        # Audio thread: record then transcribe, fully in parallel with turret + image capture.
        # The serial bridge is only touched from the main thread so there is no contention.
        transcription_holder: list[str] = [""]

        def _record_and_transcribe() -> None:
            path = record_audio(
                out_dir=str(capture_cfg["artifacts_dir"]),
                seconds=int(capture_cfg["audio_seconds"]),
                input_device_hint=str(audio_cfg["input_device_hint"]),
            )
            transcription_holder[0] = transcribe_audio(
                audio_path=path,
                model=str(brain_cfg["model"]),
                timeout_s=int(brain_cfg["timeout_s"]),
            )

        audio_thread = threading.Thread(target=_record_and_transcribe, daemon=True)
        audio_thread.start()

        # Main thread: point turret while audio records in background.
        state = State.POINTING
        set_state_ui(bridge, state)
        pointed = bridge.point_turret(
            evt.bearing_deg,
            motion_timeout_s=float(cfg["turret"]["motion_timeout_s"]),
        )

        # Capture images. Audio thread may still be recording or awaiting transcription.
        state = State.CAPTURING
        set_state_ui(bridge, state)
        images = capture_photos(
            camera_index=int(capture_cfg["camera_index"]),
            out_dir=str(capture_cfg["artifacts_dir"]),
            count=int(capture_cfg["image_count"]),
            width=int(capture_cfg["image_width"]),
            height=int(capture_cfg["image_height"]),
            gap_ms=int(capture_cfg["image_gap_ms"]),
        )

        # Wait for audio recording + transcription to finish before analyzing.
        # Timeout is generous: audio_seconds + one full API timeout + 2s buffer.
        audio_thread.join(
            timeout=float(capture_cfg["audio_seconds"]) + float(brain_cfg["timeout_s"]) + 2.0
        )
        transcription = transcription_holder[0]

        host = str(cfg["network"]["check_host"])
        port = int(cfg["network"]["check_port"])
        timeout_s = float(cfg["network"]["check_timeout_s"])
        if (not pointed) or (not images) or (not network_ok(host, port, timeout_s)):
            state = State.FAULT
            set_state_ui(bridge, state)
            speak(
                text="Cloud analysis unavailable. Check network.",
                cache_dir=str(audio_cfg["tts_cache_dir"]),
                rate=int(audio_cfg["tts_rate"]),
                voice=str(audio_cfg["tts_voice"]),
            )
            time.sleep(1.0)
            state = State.IDLE
            set_state_ui(bridge, state)
            continue

        state = State.ANALYZING
        set_state_ui(bridge, state)
        result = analyze_event(
            images=images,
            transcription=transcription,
            model=str(brain_cfg["model"]),
            timeout_s=int(brain_cfg["timeout_s"]),
            max_tokens=int(brain_cfg["max_tokens"]),
            temperature=float(brain_cfg["temperature"]),
            retry_count=int(brain_cfg["retry_count"]),
        )

        state = State.RESPONDING
        set_state_ui(bridge, state)
        speak(
            text=result.spoken_response,
            cache_dir=str(audio_cfg["tts_cache_dir"]),
            rate=int(audio_cfg["tts_rate"]),
            voice=str(audio_cfg["tts_voice"]),
        )

        state = State.ACTION
        set_state_ui(bridge, state)
        apply_action(bridge, result.severity)
        time.sleep(0.8)

        state = State.IDLE
        set_state_ui(bridge, state)


if __name__ == "__main__":
    run()
