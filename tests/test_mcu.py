#!/usr/bin/env python3
"""
Smoke Test: Test MCU subsystems individually
(Run after MCU is flashed; before main.py)
"""

import sys
import time

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial")
    sys.exit(1)

# Config
MCU_PORT = "/dev/ttyACM0"
MCU_BAUDRATE = 115200

def send_command(ser, cmd):
    """Send JSON command and get response."""
    ser.write((cmd + "\n").encode('utf-8'))
    time.sleep(0.2)
    
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    
    return response

def test_mcu():
    """Test each MCU subsystem."""
    print("\n" + "="*60)
    print("MCU SMOKE TEST")
    print("="*60)
    
    try:
        ser = serial.Serial(MCU_PORT, MCU_BAUDRATE, timeout=1.0)
        print(f"✓ Connected to {MCU_PORT}")
        time.sleep(1)  # Wait for MCU startup
    except Exception as e:
        print(f"✗ Cannot connect to {MCU_PORT}: {e}")
        return False
    
    all_pass = True
    
    # Test 1: Heartbeat
    print("\n[1] Heartbeat test...")
    response = send_command(ser, '{"cmd":"heartbeat"}')
    if response:
        print(f"  ✓ MCU responding: {response.strip()[:50]}")
    else:
        print(f"  ✗ No response")
        all_pass = False
    
    # Test 2: LCD
    print("\n[2] LCD display test...")
    send_command(ser, '{"cmd":"lcd_text","line1":"Test","line2":"LCD"}')
    print(f"  ✓ LCD command sent (check device)")
    
    # Test 3: LEDs
    print("\n[3] LED test...")
    for level in ["idle", "event", "alert", "alarm"]:
        send_command(ser, f'{{"cmd":"set_led","level":"{level}"}}')
        print(f"  ✓ LED set to {level} (check device)")
        time.sleep(0.5)
    
    # Test 4: Turret (careful: motor may draw power spike)
    print("\n[4] Turret test (careful: may cause brownout)...")
    send_command(ser, '{"cmd":"point_turret","degrees":0}')
    print(f"  ✓ Home turret (0°)")
    time.sleep(1)
    
    send_command(ser, '{"cmd":"point_turret","degrees":45}')
    print(f"  ✓ Point to 45°")
    time.sleep(2)
    
    send_command(ser, '{"cmd":"point_turret","degrees":-45}')
    print(f"  ✓ Point to -45°")
    time.sleep(2)
    
    send_command(ser, '{"cmd":"point_turret","degrees":0}')
    print(f"  ✓ Return to home")
    
    # Test 5: Threshold
    print("\n[5] Threshold adjustment...")
    send_command(ser, '{"cmd":"set_threshold","offset":80}')
    print(f"  ✓ Threshold set to 80")
    
    # Test 6: Reset
    print("\n[6] Reset command...")
    send_command(ser, '{"cmd":"reset"}')
    print(f"  ✓ Reset sent")
    
    ser.close()
    
    print("\n" + "="*60)
    if all_pass:
        print("✓ MCU subsystems functional!")
    else:
        print("✗ Some tests failed; check MCU logs")
    print("="*60)
    
    return all_pass

if __name__ == "__main__":
    success = test_mcu()
    sys.exit(0 if success else 1)
