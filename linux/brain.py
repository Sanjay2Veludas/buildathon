import base64
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict

import requests


@dataclass
class BrainResult:
    event_type: str
    severity: str
    spoken_response: str
    action_tag: str
    raw: Dict[str, Any]


def _read_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned)
    return cleaned.strip()


def _parse_response_text(text: str) -> Dict[str, Any]:
    payload = _strip_json_fences(text)
    return json.loads(payload)


def _fallback_unavailable() -> BrainResult:
    return BrainResult(
        event_type="unknown",
        severity="notable",
        spoken_response="I heard something, but cloud analysis is unavailable right now.",
        action_tag="analysis_unavailable",
        raw={},
    )


def _api_headers() -> Dict[str, str]:
    return {
        "x-api-key": os.getenv("ANTHROPIC_API_KEY", ""),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }


def transcribe_audio(audio_path: str, model: str, timeout_s: int) -> str:
    """Send a WAV file to Claude and return a transcription or sound description.

    Returns an empty string on any failure so callers can proceed without audio context.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or not os.path.exists(audio_path):
        return ""

    body = {
        "model": model,
        "max_tokens": 200,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "audio/wav",
                        "data": _read_b64(audio_path),
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Transcribe this audio. If speech is present, return the exact words. "
                        "If no speech, describe the sounds heard (e.g. 'loud bang', 'glass breaking', "
                        "'footsteps on hard floor'). Return only the transcription or sound description, nothing else."
                    ),
                },
            ],
        }],
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=_api_headers(),
            data=json.dumps(body),
            timeout=timeout_s,
        )
        if resp.status_code != 200:
            return ""
        data = resp.json()
        blocks = data.get("content", [])
        parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
        return "\n".join(parts).strip()
    except Exception:
        return ""


def analyze_event(
    images: list[str],
    transcription: str,
    model: str,
    timeout_s: int,
    max_tokens: int,
    temperature: float,
    retry_count: int,
) -> BrainResult:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_unavailable()

    image_blocks = []
    for path in images[:2]:
        if not os.path.exists(path):
            continue
        image_blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": _read_b64(path),
            },
        })

    audio_context = transcription if transcription else "No audio transcription available."
    prompt = (
        "You are classifying a security-monitor event. "
        "Return STRICT JSON only with keys: event_type, severity, spoken_response, action_tag. "
        "severity must be one of benign|notable|alert. "
        "spoken_response must be one short sentence. "
        "Note: audio was captured at event time; images were captured after the turret repositioned. "
        f"Audio transcription: {audio_context}"
    )

    content = image_blocks + [{"type": "text", "text": prompt}]

    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": content}],
    }

    attempts = retry_count + 1
    for _ in range(attempts):
        try:
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=_api_headers(),
                data=json.dumps(body),
                timeout=timeout_s,
            )
            if resp.status_code != 200:
                time.sleep(0.2)
                continue

            data = resp.json()
            blocks = data.get("content", [])
            text_parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
            joined = "\n".join(text_parts)
            parsed = _parse_response_text(joined)

            event_type = str(parsed.get("event_type", "unknown"))
            severity = str(parsed.get("severity", "notable"))
            spoken = str(parsed.get("spoken_response", "Sound detected."))
            action_tag = str(parsed.get("action_tag", "report"))

            if severity not in {"benign", "notable", "alert"}:
                severity = "notable"

            return BrainResult(
                event_type=event_type,
                severity=severity,
                spoken_response=spoken,
                action_tag=action_tag,
                raw=parsed,
            )
        except Exception:
            time.sleep(0.2)
            continue

    return _fallback_unavailable()
