#!/usr/bin/env python3
import json
import serial
import time


def main() -> int:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.3)
    deadline = time.time() + 12
    print('Listening for MCU event JSON... clap near each sensor.')
    found = 0
    while time.time() < deadline:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get('type') == 'event':
            print('EVENT:', msg)
            found += 1
            if found >= 2:
                print('PASS: sound trigger pipeline alive')
                return 0
    print('FAIL: no event seen')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
