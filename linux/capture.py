import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import cv2


@dataclass
class CaptureResult:
    images: list[str]
    audio_path: str
    ok: bool


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


def record_audio_3s(out_dir: str, seconds: int, input_device_hint: str) -> str:
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


def capture_bundle(camera_index: int,
                   artifacts_dir: str,
                   image_count: int,
                   image_width: int,
                   image_height: int,
                   image_gap_ms: int,
                   audio_seconds: int,
                   input_device_hint: str) -> CaptureResult:
    images = capture_photos(
        camera_index=camera_index,
        out_dir=artifacts_dir,
        count=image_count,
        width=image_width,
        height=image_height,
        gap_ms=image_gap_ms,
    )
    audio_path = record_audio_3s(out_dir=artifacts_dir, seconds=audio_seconds, input_device_hint=input_device_hint)

    return CaptureResult(images=images, audio_path=audio_path, ok=(len(images) > 0 and os.path.exists(audio_path)))
