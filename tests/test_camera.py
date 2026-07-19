#!/usr/bin/env python3
import os
import subprocess
import time

import cv2


def main() -> int:
    print('== lsusb ==')
    subprocess.run(['lsusb'], check=False)

    print('== v4l2-ctl --list-devices ==')
    subprocess.run(['v4l2-ctl', '--list-devices'], check=False)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('FAIL: camera not opened')
        return 1

    ok, frame = cap.read()
    cap.release()
    if not ok:
        print('FAIL: cannot read frame')
        return 1

    os.makedirs('artifacts', exist_ok=True)
    path = f"artifacts/test_frame_{int(time.time())}.jpg"
    cv2.imwrite(path, frame)
    print('PASS:', path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
