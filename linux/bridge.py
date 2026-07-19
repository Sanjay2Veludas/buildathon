#!/usr/bin/env python3
"""
Audio-Localizing AI Monitor - MCU RPC Bridge
Communication layer with STM32U585 via Arduino App Lab RPC
"""

import json
import serial
import threading
import queue
import time
from typing import Callable, Optional, Dict, Any
from config import MCU_SERIAL_PORT, MCU_BAUDRATE, RPC_HEARTBEAT_INTERVAL_SEC, SERIAL_DEBUG

class RPCBridge:
    """Handles JSON-RPC communication with MCU."""
    
    def __init__(self, port: str = MCU_SERIAL_PORT, baudrate: int = MCU_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.rx_queue = queue.Queue()
        self.command_callbacks = {}
        self.running = False
        self.thread = None
        
    def connect(self) -> bool:
        """Open serial connection to MCU."""
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1.0)
            time.sleep(0.5)  # let MCU settle
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            if SERIAL_DEBUG:
                print(f"[RPC] Connected to {self.port} @ {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"[RPC] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close serial connection."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.serial:
            self.serial.close()
    
    def _read_loop(self):
        """Background thread: read and parse incoming JSON from MCU."""
        buffer = ""
        while self.running:
            try:
                if self.serial.in_waiting > 0:
                    chunk = self.serial.read(self.serial.in_waiting).decode('utf-8', errors='ignore')
                    buffer += chunk
                    
                    # Try to extract complete JSON objects (look for { ... })
                    while True:
                        start = buffer.find('{')
                        if start == -1:
                            buffer = ""
                            break
                        end = buffer.find('}', start)
                        if end == -1:
                            buffer = buffer[start:]
                            break
                        
                        try:
                            obj = json.loads(buffer[start:end+1])
                            self.rx_queue.put(obj)
                            buffer = buffer[end+1:]
                        except json.JSONDecodeError:
                            buffer = buffer[start+1:]
                            break
            except Exception as e:
                if SERIAL_DEBUG:
                    print(f"[RPC] Read error: {e}")
            
            time.sleep(0.01)
    
    def send_command(self, cmd: str, **kwargs) -> bool:
        """Send a command to MCU (JSON format)."""
        try:
            obj = {"cmd": cmd, **kwargs}
            json_str = json.dumps(obj)
            self.serial.write((json_str + "\n").encode('utf-8'))
            if SERIAL_DEBUG:
                print(f"[RPC] TX: {json_str}")
            return True
        except Exception as e:
            print(f"[RPC] Send error: {e}")
            return False
    
    def point_turret(self, degrees: float) -> bool:
        """Command: point turret to absolute angle."""
        return self.send_command("point_turret", degrees=degrees)
    
    def set_led(self, level: str) -> bool:
        """Command: set LED state (idle|event|alert|alarm)."""
        return self.send_command("set_led", level=level)
    
    def lcd_text(self, line1: str, line2: str) -> bool:
        """Command: display text on LCD."""
        line1 = line1[:16]  # clip to 16 chars
        line2 = line2[:16]
        return self.send_command("lcd_text", line1=line1, line2=line2)
    
    def set_threshold(self, offset: int) -> bool:
        """Command: set trigger threshold."""
        return self.send_command("set_threshold", offset=offset)
    
    def set_armed(self, armed: bool) -> bool:
        """Command: enable/disable listening."""
        return self.send_command("set_armed", armed=armed)
    
    def reset_mcu(self) -> bool:
        """Command: reset MCU state."""
        return self.send_command("reset")
    
    def get_event(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """Poll for incoming event from MCU (non-blocking)."""
        try:
            return self.rx_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def wait_for_event(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Block until event arrives or timeout."""
        try:
            return self.rx_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for specific event type."""
        self.command_callbacks[event_type] = callback
    
    def heartbeat(self) -> bool:
        """Send periodic heartbeat to keep connection alive."""
        return self.send_command("heartbeat")
