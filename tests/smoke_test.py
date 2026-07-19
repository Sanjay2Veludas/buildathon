#!/usr/bin/env python3
"""
Smoke Test: Verify all hardware subsystems are functional
Run this first at booth setup (hour 0)
"""

import os
import sys
import subprocess
import time
import cv2
from pathlib import Path

def test_usb_devices():
    """Verify USB camera and speaker are enumerated."""
    print("\n=== USB Device Check ===")
    try:
        result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5)
        output = result.stdout.lower()
        
        camera_found = "logitech" in output or "c270" in output
        print(f"  Camera (Logitech C270): {'✓' if camera_found else '✗'}")
        
        # Check for generic USB hub/audio device
        print(f"  USB devices detected:")
        for line in result.stdout.split('\n'):
            if line and any(x in line.lower() for x in ['logitech', 'audio', 'speaker']):
                print(f"    {line}")
        
        return camera_found
    except Exception as e:
        print(f"  ✗ lsusb failed: {e}")
        return False

def test_audio_devices():
    """Verify ALSA can see audio capture + playback."""
    print("\n=== Audio Device Check ===")
    
    # Capture
    try:
        result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  Capture devices found:")
            for line in result.stdout.split('\n')[:5]:
                if line.strip():
                    print(f"    {line}")
        else:
            print(f"  ✗ No capture devices")
            return False
    except Exception as e:
        print(f"  ✗ arecord -l failed: {e}")
        return False
    
    # Playback
    try:
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"  Playback devices found:")
            for line in result.stdout.split('\n')[:5]:
                if line.strip():
                    print(f"    {line}")
        else:
            print(f"  ✗ No playback devices")
            return False
    except Exception as e:
        print(f"  ✗ aplay -l failed: {e}")
        return False
    
    return True

def test_camera():
    """Capture frame from camera."""
    print("\n=== Camera Capture Test ===")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print(f"  ✗ Cannot open camera at /dev/video0")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            print(f"  ✓ Frame captured: {frame.shape}")
            # Save test frame
            test_dir = Path("./logs/photos")
            test_dir.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(test_dir / "test_frame.jpg"), frame)
            print(f"  ✓ Test frame saved to {test_dir / 'test_frame.jpg'}")
            return True
        else:
            print(f"  ✗ Failed to capture frame")
            return False
    except Exception as e:
        print(f"  ✗ Camera test failed: {e}")
        return False

def test_audio_record():
    """Record 2-second audio clip."""
    print("\n=== Audio Record Test ===")
    try:
        test_file = Path("./logs/audio/test_record.wav")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            "arecord",
            "-c", "1",
            "-r", "16000",
            "-f", "S16_LE",
            "-d", "2",
            str(test_file)
        ]
        
        print(f"  Recording 2 seconds...")
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        
        if result.returncode == 0 and test_file.exists():
            size_kb = test_file.stat().st_size / 1024
            print(f"  ✓ Audio recorded: {size_kb:.1f} KB saved to {test_file}")
            return True
        else:
            print(f"  ✗ Recording failed")
            return False
    except Exception as e:
        print(f"  ✗ Audio record test failed: {e}")
        return False

def test_audio_playback():
    """Play back test audio."""
    print("\n=== Audio Playback Test ===")
    try:
        # Generate test tone with espeak
        test_file = Path("/tmp/test_tone.wav")
        
        cmd = [
            "espeak-ng",
            "-v", "en+m2",
            "-w", str(test_file),
            "System test"
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        if result.returncode != 0:
            print(f"  ✗ espeak-ng failed")
            return False
        
        # Play it back
        cmd = ["aplay", str(test_file)]
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        
        if result.returncode == 0:
            print(f"  ✓ Audio playback successful")
            return True
        else:
            print(f"  ✗ Playback failed")
            return False
    except Exception as e:
        print(f"  ✗ Playback test failed: {e}")
        return False

def test_python_deps():
    """Check Python dependencies."""
    print("\n=== Python Dependencies ===")
    
    deps = {
        "cv2": "opencv-python",
        "anthropic": "anthropic",
        "serial": "pyserial",
        "yaml": "pyyaml"
    }
    
    missing = []
    for module, package in deps.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    return len(missing) == 0

def test_mcu_connection():
    """Check MCU serial connection."""
    print("\n=== MCU Serial Connection ===")
    try:
        import serial
        
        # Try common ports
        ports = ["/dev/ttyACM0", "/dev/ttyUSB0", "COM3"]
        
        for port in ports:
            try:
                ser = serial.Serial(port, 115200, timeout=1)
                print(f"  ✓ Connected to {port}")
                
                # Send heartbeat command
                ser.write(b'{"cmd":"heartbeat"}\n')
                time.sleep(0.1)
                
                response = ser.read(100)
                ser.close()
                
                if response:
                    print(f"    Response: {response.decode('utf-8', errors='ignore')[:50]}")
                return True
            except (serial.SerialException, FileNotFoundError):
                pass
        
        print(f"  ✗ No MCU found on common ports")
        print(f"    Try: dmesg | grep tty")
        return False
    except ImportError:
        print(f"  ✗ pyserial not installed")
        return False
    except Exception as e:
        print(f"  ✗ MCU test failed: {e}")
        return False

def main():
    """Run all smoke tests."""
    print("\n" + "="*60)
    print("HARDWARE SMOKE TEST SUITE")
    print("="*60)
    
    tests = [
        ("USB Devices", test_usb_devices),
        ("Audio Devices", test_audio_devices),
        ("Camera Capture", test_camera),
        ("Audio Record", test_audio_record),
        ("Audio Playback", test_audio_playback),
        ("Python Deps", test_python_deps),
        ("MCU Connection", test_mcu_connection)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status:8} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All systems nominal. Ready to demo!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. See above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
