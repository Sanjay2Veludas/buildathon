#!/usr/bin/env python3
"""
Audio-Localizing AI Monitor - Capture Module
Photo + audio capture from USB peripherals
"""

import cv2
import numpy as np
import subprocess
import os
import time
from pathlib import Path
from typing import Optional, Tuple
from config import AUDIO_CAPTURE_SEC, PHOTO_DIR, AUDIO_DIR, SERIAL_DEBUG

class CaptureModule:
    """Handles webcam + audio capture."""
    
    def __init__(self):
        self.camera = None
        self.camera_idx = None
        
    def find_camera(self) -> Optional[int]:
        """Locate Logitech C270 (or first available camera)."""
        for idx in range(10):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret:
                    self.camera_idx = idx
                    if SERIAL_DEBUG:
                        print(f"[CAPTURE] Found camera at index {idx}")
                    return idx
        print("[CAPTURE] No camera found!")
        return None
    
    def open_camera(self) -> bool:
        """Initialize camera capture."""
        if self.camera_idx is None:
            self.find_camera()
        
        if self.camera_idx is None:
            return False
        
        try:
            self.camera = cv2.VideoCapture(self.camera_idx)
            # Set resolution and FPS
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            # Warm up
            for _ in range(5):
                self.camera.read()
            
            return True
        except Exception as e:
            print(f"[CAPTURE] Camera init failed: {e}")
            return False
    
    def close_camera(self):
        """Release camera."""
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def capture_photo(self, filename: Optional[str] = None) -> Tuple[bool, Optional[np.ndarray]]:
        """Capture single frame."""
        if not self.camera or not self.camera.isOpened():
            if not self.open_camera():
                return False, None
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                return False, None
            
            # Save to disk
            if filename is None:
                filename = f"photo_{int(time.time())}.jpg"
            filepath = PHOTO_DIR / filename
            cv2.imwrite(str(filepath), frame)
            
            if SERIAL_DEBUG:
                print(f"[CAPTURE] Photo saved: {filepath}")
            
            return True, frame
        except Exception as e:
            print(f"[CAPTURE] Capture failed: {e}")
            return False, None
    
    def capture_photos(self, count: int = 2, interval_sec: float = 0.5) -> Tuple[bool, list]:
        """Capture multiple photos."""
        photos = []
        for i in range(count):
            success, frame = self.capture_photo(f"event_{int(time.time())}_{i}.jpg")
            if success:
                photos.append(frame)
            if i < count - 1:
                time.sleep(interval_sec)
        
        return len(photos) > 0, photos
    
    def record_audio(self, duration_sec: float = AUDIO_CAPTURE_SEC, 
                     filename: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Record audio from C270 built-in mic using arecord (ALSA)."""
        if filename is None:
            filename = f"audio_{int(time.time())}.wav"
        filepath = AUDIO_DIR / filename
        
        try:
            # Use ALSA arecord to capture from default device (C270)
            # Adjust hw:X,Y based on your system (use `arecord -l` to find)
            cmd = [
                "arecord",
                "-c", "1",              # mono
                "-r", "16000",          # 16 kHz
                "-f", "S16_LE",         # 16-bit signed
                "-d", str(int(duration_sec)),
                str(filepath)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=duration_sec + 5)
            
            if result.returncode != 0:
                print(f"[CAPTURE] arecord failed: {result.stderr.decode()}")
                return False, None
            
            if SERIAL_DEBUG:
                print(f"[CAPTURE] Audio saved: {filepath}")
            
            return True, str(filepath)
        
        except subprocess.TimeoutExpired:
            print(f"[CAPTURE] Recording timeout")
            return False, None
        except Exception as e:
            print(f"[CAPTURE] Recording failed: {e}")
            return False, None
    
    def start_async_record(self, duration_sec: float = AUDIO_CAPTURE_SEC) -> Optional[subprocess.Popen]:
        """Start recording in background (fire-and-forget)."""
        filename = f"audio_{int(time.time())}.wav"
        filepath = AUDIO_DIR / filename
        
        try:
            cmd = [
                "arecord",
                "-c", "1",
                "-r", "16000",
                "-f", "S16_LE",
                "-d", str(int(duration_sec)),
                str(filepath)
            ]
            
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if SERIAL_DEBUG:
                print(f"[CAPTURE] Audio recording started (async): {filepath}")
            return proc
        
        except Exception as e:
            print(f"[CAPTURE] Async record failed: {e}")
            return None
