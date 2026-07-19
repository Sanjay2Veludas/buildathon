#!/usr/bin/env python3
"""
Audio-Localizing AI Monitor - Main State Machine
Orchestrates the full event detection → analysis → response loop
"""

import time
import logging
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from bridge import RPCBridge
from capture import CaptureModule
from brain import Brain
from speak import SpeechModule
from config import (
    SERIAL_DEBUG, DEMO_MODE, OFFLINE_MODE,
    MOTION_TIMEOUT_SEC, LLM_TIMEOUT_SEC, AUDIO_CAPTURE_SEC,
    LOG_DIR, THRESHOLD_OFFSET_DEMO, THRESHOLD_OFFSET_DEFAULT
)

# Setup logging
log_file = LOG_DIR / f"monitor_{int(time.time())}.log"
logging.basicConfig(
    level=logging.DEBUG if SERIAL_DEBUG else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Monitor")

class State(Enum):
    """System states."""
    IDLE = 0
    EVENT = 1
    POINTING = 2
    CAPTURING = 3
    ANALYZING = 4
    RESPONDING = 5
    ACTION = 6
    ERROR = 7

class Monitor:
    """Main state machine."""
    
    def __init__(self):
        self.state = State.IDLE
        self.prev_state = None
        self.state_entry_time = time.time()
        
        # Modules
        self.rpc = RPCBridge()
        self.capture = CaptureModule()
        self.brain = Brain()
        self.speak = SpeechModule()
        
        # Event data
        self.event_bearing = 0.0
        self.event_amps = [0, 0, 0]
        self.event_time = 0
        self.captured_photos = []
        self.captured_audio = None
        self.analysis_result = None
        
        # Stats
        self.events_processed = 0
        
    def setup(self) -> bool:
        """Initialize all modules."""
        logger.info("=== Audio-Localizing AI Monitor ===")
        logger.info("Initializing modules...")
        
        # RPC bridge
        if not self.rpc.connect():
            logger.error("Failed to connect to MCU")
            return False
        
        # Camera
        if not self.capture.open_camera():
            logger.warning("Camera init failed; continuing...")
        
        # Set initial configuration on MCU
        threshold = THRESHOLD_OFFSET_DEMO if DEMO_MODE else THRESHOLD_OFFSET_DEFAULT
        self.rpc.set_threshold(threshold)
        self.rpc.lcd_text("Ready", "Listening...")
        self.rpc.set_led("idle")
        
        logger.info("Setup complete. System armed.")
        return True
    
    def teardown(self):
        """Cleanup."""
        self.rpc.disconnect()
        self.capture.close_camera()
    
    def run(self):
        """Main event loop."""
        try:
            while True:
                self._process_state()
                time.sleep(0.01)  # 10ms tick
        except KeyboardInterrupt:
            logger.info("Shutdown requested")
        finally:
            self.teardown()
    
    def _process_state(self):
        """Execute current state; transition if needed."""
        time_in_state = time.time() - self.state_entry_time
        
        if self.state == State.IDLE:
            self._state_idle()
        elif self.state == State.EVENT:
            self._state_event()
        elif self.state == State.POINTING:
            self._state_pointing(time_in_state)
        elif self.state == State.CAPTURING:
            self._state_capturing(time_in_state)
        elif self.state == State.ANALYZING:
            self._state_analyzing(time_in_state)
        elif self.state == State.RESPONDING:
            self._state_responding()
        elif self.state == State.ACTION:
            self._state_action()
        elif self.state == State.ERROR:
            self._state_error(time_in_state)
    
    def _set_state(self, new_state: State):
        """Transition to new state."""
        if new_state != self.state:
            logger.info(f"State transition: {self.state.name} → {new_state.name}")
            self.prev_state = self.state
            self.state = new_state
            self.state_entry_time = time.time()
            
            # Update display
            self.rpc.lcd_text(f"State: {new_state.name[:6]}", "")
    
    def _state_idle(self):
        """Waiting for event."""
        # Poll for event from MCU
        event = self.rpc.get_event(timeout=0.01)
        if event and event.get("type") == "event":
            self.event_bearing = event.get("bearing_deg", 0.0)
            self.event_amps = event.get("amplitudes", [0, 0, 0])
            self.event_time = event.get("timestamp", 0)
            
            logger.info(f"Event detected: bearing={self.event_bearing}°, amps={self.event_amps}")
            self.rpc.lcd_text(f"Bearing: {self.event_bearing:.0f}°", "Analyzing...")
            self.rpc.set_led("event")
            
            self._set_state(State.EVENT)
    
    def _state_event(self):
        """Event detected; prepare to point turret."""
        # Immediately transition to pointing
        self._set_state(State.POINTING)
    
    def _state_pointing(self, time_in_state: float):
        """Pointing turret to event bearing."""
        # Send turret command (only on entry)
        if self.prev_state != State.POINTING:
            self.rpc.point_turret(self.event_bearing)
            logger.info(f"Pointing turret to {self.event_bearing}°")
        
        # Wait for turret to settle
        if time_in_state > MOTION_TIMEOUT_SEC:
            logger.warning("Turret motion timeout")
            self._set_state(State.CAPTURING)
        elif time_in_state > 1.0:  # Assume 1 sec is enough for ~180° with ramping
            self._set_state(State.CAPTURING)
    
    def _state_capturing(self, time_in_state: float):
        """Capturing photo + audio."""
        # Start captures on entry
        if self.prev_state != State.CAPTURING:
            self.rpc.lcd_text("Capturing...", "")
            
            # Start audio capture immediately (async)
            audio_proc = self.capture.start_async_record(duration_sec=AUDIO_CAPTURE_SEC)
            
            # Capture 2 photos while audio records
            success, photos = self.capture.capture_photos(count=2, interval_sec=0.2)
            self.captured_photos = photos if success else []
            
            logger.info(f"Captured {len(self.captured_photos)} photo(s)")
        
        # Wait for audio capture to finish (AUDIO_CAPTURE_SEC)
        if time_in_state > AUDIO_CAPTURE_SEC + 1.0:
            self._set_state(State.ANALYZING)
    
    def _state_analyzing(self, time_in_state: float):
        """Sending to LLM for analysis."""
        # Analyze on entry
        if self.prev_state != State.ANALYZING:
            self.rpc.lcd_text("Analyzing...", "LLM...")
            
            # Build audio description (placeholder; ideally transcribe or describe audio envelope)
            audio_desc = f"Sound event detected at bearing {self.event_bearing}°"
            
            # Get first photo
            photo_path = None
            if self.captured_photos:
                # Save temporarily if needed
                photo_path = str(list(Path("./logs/photos").glob("*.jpg"))[-1]) if list(Path("./logs/photos").glob("*.jpg")) else None
            
            # Call brain
            logger.info("Calling LLM for analysis...")
            self.analysis_result = self.brain.analyze_event(
                photo_path=photo_path,
                audio_description=audio_desc
            )
            
            logger.info(f"Analysis result: {self.analysis_result}")
            self._set_state(State.RESPONDING)
        
        # Timeout
        if time_in_state > LLM_TIMEOUT_SEC + 2.0:
            logger.error("Analysis timeout")
            self.analysis_result = self.brain._fallback_response()
            self._set_state(State.RESPONDING)
    
    def _state_responding(self):
        """Speaking response + setting LEDs."""
        if not self.analysis_result:
            self.analysis_result = self.brain._fallback_response()
        
        severity = self.analysis_result.get("severity", "benign")
        response_text = self.analysis_result.get("response", "Event detected")
        action = self.analysis_result.get("action", "log")
        
        # Update LED state based on severity
        if severity == "alert":
            self.rpc.set_led("alert")
        elif severity == "notable":
            self.rpc.set_led("event")
        else:
            self.rpc.set_led("idle")
        
        # Display response
        self.rpc.lcd_text(f"Severity: {severity}", response_text[:16])
        
        # Speak response
        logger.info(f"Speaking: {response_text}")
        self.speak.speak(response_text, use_cache=True)
        
        # Transition to action
        self._set_state(State.ACTION)
    
    def _state_action(self):
        """Execute action based on analysis."""
        if not self.analysis_result:
            self._set_state(State.IDLE)
            return
        
        action = self.analysis_result.get("action", "log")
        
        logger.info(f"Action: {action}")
        
        if action == "alarm":
            self.rpc.set_led("alarm")
            self.rpc.lcd_text("ALARM!", "Check physical area")
            # Optionally drive toward sound (stretch goal)
        elif action == "investigate":
            # Drive toward bearing (requires DC motors + ultrasonic)
            pass
        else:
            # log / idle
            pass
        
        self.events_processed += 1
        logger.info(f"Event #{self.events_processed} complete")
        
        # Return to idle after delay
        time.sleep(2.0)
        self.rpc.set_led("idle")
        self.rpc.lcd_text("Ready", "Listening...")
        self._set_state(State.IDLE)
    
    def _state_error(self, time_in_state: float):
        """Error state."""
        self.rpc.set_led("alarm")
        self.rpc.lcd_text("ERROR", "Check logs")
        
        if time_in_state > 5.0:
            self._set_state(State.IDLE)


def main():
    """Entry point."""
    monitor = Monitor()
    if monitor.setup():
        monitor.run()
    else:
        logger.error("Setup failed")


if __name__ == "__main__":
    main()
