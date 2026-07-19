#!/usr/bin/env python3
import json
import serial
import time


def wait_motion_complete(ser, timeout=4.0):
    end = time.time() + timeout
    while time.time() < end:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get('type') == 'motion_complete':
            return True
    return False


def main() -> int:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.2)
    for deg in [45, -45, 0]:
        ser.write(f'point_turret deg={deg}\n'.encode('utf-8'))
        ok = wait_motion_complete(ser, timeout=5.0)
        print(f'deg={deg} complete={ok}')
        if not ok:
            print('FAIL: motion timeout')
            return 1
    print('PASS: turret command path')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
