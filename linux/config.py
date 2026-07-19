#!/usr/bin/env python3
"""
Audio-Localizing AI Monitor - Configuration
YAML-based runtime config (no recompile needed)
"""

import os
import yaml
from pathlib import Path

# Sensor configuration
SENSOR_BEARINGS = [0, 120, 240]  # degrees
SENSOR_FIXED_MOUNT = True  # not on turret

# Turret (stepper motor) limits
TURRET_MIN_DEG = -180
TURRET_MAX_DEG = 180
TURRET_HOME_DEG = 0

# Audio thresholds (tunable at runtime via RPC)
THRESHOLD_OFFSET_DEFAULT = 100
THRESHOLD_OFFSET_DEMO = 50  # lower in demo mode

# Timeouts (all in seconds)
LLM_TIMEOUT_SEC = 10
LLM_FALLBACK_TIMEOUT_SEC = 3  # if primary fails, try fallback
AUDIO_CAPTURE_SEC = 3
MOTION_TIMEOUT_SEC = 5

# Operational flags
DEMO_MODE = True  # lower thresholds, faster fallbacks, prefer scripted responses
OFFLINE_MODE = False  # override LLM calls, use canned responses
ALLOW_MOTION_DURING_CAPTURE = True
SERIAL_DEBUG = True

# RPC Bridge
MCU_SERIAL_PORT = "/dev/ttyACM0"  # or "/dev/ttyUSB0" or "COM3" on Windows
MCU_BAUDRATE = 115200
RPC_HEARTBEAT_INTERVAL_SEC = 1.0

# Cloud API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = "claude-3-5-sonnet-20241022"

# Multimodal LLM prompt template
LLM_SYSTEM_PROMPT = """You are an audio-visual event analyzer for a hardware sentry device.
You receive a photo and audio clip (or transcription) of an event.
Classify it and respond tersely.

Output STRICT JSON:
{
  "event_type": "glass breaking|person clapping|dog barking|[other]",
  "severity": "benign|notable|alert",
  "response": "[1-sentence spoken response]",
  "action": "[idle|log|alarm|investigate]"
}
"""

LLM_USER_PROMPT_TEMPLATE = """Analyze this event:
Photo: [image data]
Audio description: {audio_description}

What is happening? Be concise."""

# TTS (Text-to-Speech)
TTS_ENGINE = "espeak-ng"  # or "cloud_polly", "cloud_gcloud"
TTS_CACHED_DIR = "./audio_cache"
TTS_VOICE = "en+m2"  # espeak voice

# Offline / canned responses (fallback when Wi-Fi fails)
CANNED_RESPONSES = {
    "startup": "System armed and listening",
    "event_detected": "Interesting event detected",
    "analyzing": "Analyzing...",
    "glass_break": "Glass breaking detected!",
    "clapping": "Applause detected",
    "dog_bark": "Dog barking detected",
    "unknown": "Heard something interesting",
    "error": "System error"
}

# Paths
DATA_DIR = Path("./data")
LOG_DIR = Path("./logs")
PHOTO_DIR = Path("./logs/photos")
AUDIO_DIR = Path("./logs/audio")

# Ensure directories exist
for d in [DATA_DIR, LOG_DIR, PHOTO_DIR, AUDIO_DIR, Path(TTS_CACHED_DIR)]:
    d.mkdir(parents=True, exist_ok=True)

def load_config_file(path="config.yaml"):
    """Load config overrides from YAML file (optional)."""
    try:
        with open(path, 'r') as f:
            overrides = yaml.safe_load(f) or {}
        # Apply to module globals
        for key, val in overrides.items():
            if key.isupper() and hasattr(globals(), '__contains__'):
                globals()[key] = val
    except FileNotFoundError:
        pass

# Load on import
load_config_file()
