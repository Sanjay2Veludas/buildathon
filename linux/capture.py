import os
import subprocess
import time
from pathlib import Path

import cv2


def _timestamp_tag() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def capture_photos(camera_index: int, out_dir: str, count: int, width: int, height: int, gap_ms: int) -> list[str]:
    _ensure_dir(out_dir)
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))

    if not cap.isOpened():
        return []

    stamp = _timestamp_tag()
    paths: list[str] = []
    for i in range(count):
        ok, frame = cap.read()
        if not ok:
            continue
        path = os.path.join(out_dir, f"{stamp}_img_{i + 1}.jpg")
        cv2.imwrite(path, frame)
        paths.append(path)
        time.sleep(gap_ms / 1000.0)

    cap.release()
    return paths


def record_audio(out_dir: str, seconds: int, input_device_hint: str) -> str:
    """Record audio via arecord and return the path to the WAV file.

    Safe to call from a background thread — does not touch the serial bridge.
    """
    _ensure_dir(out_dir)
    stamp = _timestamp_tag()
    wav_path = os.path.join(out_dir, f"{stamp}_audio.wav")

    cmd = [
        "arecord",
        "-d", str(seconds),
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        wav_path,
    ]

    env = os.environ.copy()
    if input_device_hint:
        env["ALSA_CARD_HINT"] = input_device_hint

    subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    return wav_path
