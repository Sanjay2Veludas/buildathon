#!/usr/bin/env python3
"""
Audio-Localizing AI Monitor - Speech Module
Text-to-speech + audio playback
"""

import subprocess
import os
import time
from pathlib import Path
from typing import Optional
from config import TTS_ENGINE, TTS_CACHED_DIR, TTS_VOICE, SERIAL_DEBUG, CANNED_RESPONSES

class SpeechModule:
    """Handles TTS and audio playback."""
    
    def __init__(self):
        self.cache_dir = Path(TTS_CACHED_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._prebuild_cache()
    
    def _prebuild_cache(self):
        """Pre-generate audio for common responses (Wi-Fi fallback)."""
        common_phrases = [
            "startup",
            "event_detected",
            "analyzing",
            "glass_break",
            "clapping",
            "dog_bark",
            "unknown",
            "error"
        ]
        
        for phrase_key in common_phrases:
            text = CANNED_RESPONSES.get(phrase_key, "")
            if text:
                self._cache_phrase(phrase_key, text)
    
    def _cache_phrase(self, key: str, text: str):
        """Generate and cache audio file for a phrase."""
        cache_file = self.cache_dir / f"{key}.wav"
        if cache_file.exists():
            return  # Already cached
        
        try:
            if TTS_ENGINE == "espeak-ng":
                cmd = [
                    "espeak-ng",
                    "-v", TTS_VOICE,
                    "-w", str(cache_file),
                    text
                ]
                subprocess.run(cmd, capture_output=True, timeout=5)
                if SERIAL_DEBUG:
                    print(f"[SPEECH] Cached: {key}")
        except Exception as e:
            print(f"[SPEECH] Cache failed for '{key}': {e}")
    
    def speak(self, text: str, use_cache: bool = True) -> bool:
        """Speak text via TTS + playback."""
        if use_cache:
            # Check if in canned responses
            for key, cached_text in CANNED_RESPONSES.items():
                if cached_text.lower() == text.lower():
                    cache_file = self.cache_dir / f"{key}.wav"
                    if cache_file.exists():
                        return self._playback(str(cache_file))
        
        # Generate fresh TTS (requires internet / espeak-ng)
        try:
            wav_file = f"/tmp/speech_{int(time.time())}.wav"
            
            if TTS_ENGINE == "espeak-ng":
                cmd = [
                    "espeak-ng",
                    "-v", TTS_VOICE,
                    "-w", wav_file,
                    text
                ]
            else:
                print(f"[SPEECH] Unknown TTS engine: {TTS_ENGINE}")
                return False
            
            result = subprocess.run(cmd, capture_output=True, timeout=5)
            if result.returncode != 0:
                print(f"[SPEECH] TTS failed: {result.stderr.decode()}")
                return False
            
            # Play
            return self._playback(wav_file)
        
        except Exception as e:
            print(f"[SPEECH] Speak failed: {e}")
            return False
    
    def _playback(self, wav_file: str) -> bool:
        """Play audio file via speaker."""
        try:
            # Try aplay (ALSA) first
            cmd = ["aplay", wav_file]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                if SERIAL_DEBUG:
                    print(f"[SPEECH] Playback: {wav_file}")
                return True
            
            # Fallback: pulseaudio
            cmd = ["paplay", wav_file]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            return result.returncode == 0
        
        except Exception as e:
            print(f"[SPEECH] Playback failed: {e}")
            return False
    
    def speak_cached(self, key: str) -> bool:
        """Play pre-cached audio."""
        cache_file = self.cache_dir / f"{key}.wav"
        if cache_file.exists():
            return self._playback(str(cache_file))
        
        print(f"[SPEECH] Cache miss: {key}")
        return False
