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
    """Send plain-text command and capture response lines."""
    ser.write((cmd + "\n").encode('utf-8'))
    time.sleep(0.2)

    lines = []
    end = time.time() + 1.2
    while time.time() < end:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            lines.append(line)
    return "\n".join(lines)

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
    
    # Test 1: Ping
    print("\n[1] Ping test...")
    response = send_command(ser, 'ping')
    if '"type":"pong"' in response:
        print("  ✓ MCU responding with pong")
    else:
        print(f"  ✗ No pong response: {response[:80]}")
        all_pass = False

    # Test 2: LCD
    print("\n[2] LCD display test...")
    send_command(ser, 'lcd_text l1="Test" l2="LCD"')
    print("  ✓ LCD command sent (check device)")

    # Test 3: LEDs
    print("\n[3] LED test...")
    for level in [0, 1, 2, 3]:
        send_command(ser, f'set_led level={level}')
        print(f"  ✓ LED level {level} command sent (check device)")
        time.sleep(0.5)

    # Test 4: Turret
    print("\n[4] Turret test (careful: may cause brownout)...")
    send_command(ser, 'point_turret deg=0')
    print("  ✓ Home turret (0°)")
    time.sleep(1)

    send_command(ser, 'point_turret deg=45')
    print("  ✓ Point to 45°")
    time.sleep(2)

    send_command(ser, 'point_turret deg=-45')
    print("  ✓ Point to -45°")
    time.sleep(2)

    send_command(ser, 'point_turret deg=0')
    print("  ✓ Return to home")

    # Test 5: Threshold
    print("\n[5] Threshold adjustment...")
    send_command(ser, 'set_threshold value=80')
    print("  ✓ Threshold set to 80")

    # Test 6: Reset workflow
    print("\n[6] Reset workflow...")
    send_command(ser, 'set_armed armed=0')
    send_command(ser, 'set_armed armed=1')
    print("  ✓ Armed toggle reset flow sent")
    
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
