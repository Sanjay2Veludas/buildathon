import base64
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import requests

_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


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


def _api_headers() -> Dict[str, str]:
    return {
        "x-goog-api-key": os.getenv("GEMINI_API_KEY", ""),
        "content-type": "application/json",
    }


def _endpoint(model: str) -> str:
    return f"{_GEMINI_BASE}/{model}:generateContent"


def _extract_text(response_json: Dict[str, Any]) -> str:
    candidates = response_json.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(p.get("text", "") for p in parts if "text" in p).strip()


def _strip_json_fences(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned)
    return cleaned.strip()


def _fallback_unavailable() -> BrainResult:
    return BrainResult(
        event_type="unknown",
        severity="notable",
        spoken_response="I heard something, but cloud analysis is unavailable right now.",
        action_tag="analysis_unavailable",
        raw={},
    )


def transcribe_audio(audio_path: str, model: str, timeout_s: int) -> str:
    """Send a WAV file to Gemini and return a transcription or sound description.

    Returns an empty string on any failure so callers can proceed without audio context.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key or not os.path.exists(audio_path):
        return ""

    body = {
        "contents": [{
            "parts": [
                {
                    "inline_data": {
                        "mime_type": "audio/wav",
                        "data": _read_b64(audio_path),
                    }
                },
                {
                    "text": (
                        "Transcribe this audio. If speech is present, return the exact words. "
                        "If no speech, describe the sounds heard (e.g. 'loud bang', 'glass breaking', "
                        "'footsteps on hard floor'). Return only the transcription or sound description, nothing else."
                    )
                },
            ]
        }],
    }

    try:
        resp = requests.post(
            _endpoint(model),
            headers=_api_headers(),
            data=json.dumps(body),
            timeout=timeout_s,
        )
        if resp.status_code != 200:
            return ""
        return _extract_text(resp.json())
    except Exception:
        return ""


def analyze_event(
    images: List[str],
    transcription: str,
    model: str,
    timeout_s: int,
    max_tokens: int,
    temperature: float,
    retry_count: int,
) -> BrainResult:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return _fallback_unavailable()

    parts: List[Dict[str, Any]] = []
    for path in images[:2]:
        if not os.path.exists(path):
            continue
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": _read_b64(path),
            }
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
    parts.append({"text": prompt})

    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }

    attempts = retry_count + 1
    for _ in range(attempts):
        try:
            resp = requests.post(
                _endpoint(model),
                headers=_api_headers(),
                data=json.dumps(body),
                timeout=timeout_s,
            )
            if resp.status_code != 200:
                time.sleep(0.2)
                continue

            text = _extract_text(resp.json())
            parsed = json.loads(_strip_json_fences(text))

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
