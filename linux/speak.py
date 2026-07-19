import hashlib
import os
import subprocess
from pathlib import Path


def _hash_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def synth_to_cache(text: str, cache_dir: str, rate: int, voice: str) -> str:
    _ensure_dir(cache_dir)
    filename = f"tts_{_hash_key(text)}.wav"
    out_path = os.path.join(cache_dir, filename)
    if os.path.exists(out_path):
        return out_path

    cmd = [
        "espeak-ng",
        "-s", str(rate),
        "-v", voice,
        "-w", out_path,
        text,
    ]
    subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return out_path


def play_wav(path: str) -> bool:
    if not os.path.exists(path):
        return False
    cmd = ["aplay", path]
    proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0


def speak(text: str, cache_dir: str, rate: int, voice: str) -> bool:
    wav = synth_to_cache(text=text, cache_dir=cache_dir, rate=rate, voice=voice)
    return play_wav(wav)


def precache_lines(lines: list[str], cache_dir: str, rate: int, voice: str) -> None:
    for line in lines:
        synth_to_cache(text=line, cache_dir=cache_dir, rate=rate, voice=voice)
