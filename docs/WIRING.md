# Detailed Hardware Wiring Guide

## Arduino UNO Q 2GB Pinout Reference

### Maker Headers (3.3V Logic, Safe for STM32U585)

**Digital Outputs (Drive capacity: ~8mA typical)**
| Pin | Function | Component | Notes |
|-----|----------|-----------|-------|
| 6 | Stepper IN1 | 28BYJ-48 Driver | ULN2003, high-current sink |
| 7 | Stepper IN2 | 28BYJ-48 Driver | ULN2003 |
| 8 | Stepper IN3 | 28BYJ-48 Driver | ULN2003 |
| 9 | Stepper IN4 | 28BYJ-48 Driver | ULN2003 |
| 10 | LED Blue #1 | Blue LED (short pin) | Via 330Ω resistor to GND |
| 11 | LCD EN (parallel mode) | 16x2 LCD | Not used if I2C mode |
| 12 | LCD RS (parallel mode) | 16x2 LCD | Not used if I2C mode |
| 13 | Button (Arm/Standby) | Push button | Pullup → GND when pressed |

**Digital Inputs (Pullup, max 5.5V tolerant)**
| Pin | Function | Component | Notes |
|-----|----------|-----------|-------|
| A6 | Button (Reset) | Push button | Pullup → GND when pressed |

**Analog Inputs (10-bit ADC, 0–5V range)**
| Pin | Function | Component | Notes |
|-----|----------|-----------|-------|
| A0 | Microphone 1 | LM393 sound sensor | OUT pin, ~0–5V |
| A1 | Microphone 2 | LM393 sound sensor | OUT pin, ~0–5V |
| A2 | Microphone 3 | LM393 sound sensor | OUT pin, ~0–5V |
| A3 | LED Blue #2 | Blue LED | Via 330Ω resistor to GND (PWM capable) |
| A4 | LED Red #1 | Red LED | Via 330Ω resistor to GND |
| A5 | LED Red #2 | Red LED | Via 330Ω resistor to GND |

**I2C / Serial (fixed pins)**
| Pin | Function | Component |
|-----|----------|-----------|
| SDA (D20 on QRB2210 header) | I2C Data | LCD 16x2 I2C |
| SCL (D21 on QRB2210 header) | I2C Clock | LCD 16x2 I2C |
| TX (Serial1) | UART TX | MCU debug / future use |
| RX (Serial1) | UART RX | MCU debug / future use |

### Power Rails

**5V Supply (from MCU or USB)**
- Provides: Sensor bias, LCD backlight, LED anodes
- Current budget: ~200mA typical (LEDs + sensors + LCD backlight)
- Source: Arduino VIN or USB rail

**3.3V (MCU logic)**
- Do NOT drive 5V logic here
- Use 3.3V for I2C pull-ups if not built-in on LCD module

**7.4V Motor Rail (2S LiPo direct)**
- Stepper driver VMOT
- Optional DC motors
- **Critical:** Not for logic; separate power rail to avoid brownout

**GND (Common)**
- All components share GND
- Use thick wire to minimize voltage drop (star-ground preferred)

---

## Component-by-Component Wiring

### 1. Microphones (3x LM393 Analog Sound Sensors)

```
Mic Sensor Module (LM393):
[VCC] ──→ 5V
[GND] ──→ GND
[OUT] ──→ A0 (Mic 1), A1 (Mic 2), or A2 (Mic 3)

Physical mounting (fixed base, NOT turret):
  Mic 1 (A0):  bearing 0°   (front-left)
  Mic 2 (A1):  bearing 120° (rear-left)
  Mic 3 (A2):  bearing 240° (right)
  
  Arrange at 120° intervals on a circle.
  Use a cardboard ring or 3D-printed mount.
```

### 2. Stepper Motor & ULN2003 Driver

```
ULN2003 Driver Module:
[+5V]  ──→ 5V
[GND]  ──→ GND
[IN1]  ──→ Pin 6 (STM32)
[IN2]  ──→ Pin 7 (STM32)
[IN3]  ──→ Pin 8 (STM32)
[IN4]  ──→ Pin 9 (STM32)

[+MOTOR]  ──→ +7.4V (2S LiPo)
[GND]     ──→ GND (common)
[COIL A, B, C, D] ──→ Stepper motor 28BYJ-48 leads

Capacitor across motor power rails:
  +7.4V ──[100μF]──┬──[10μF]── GND
                   └── [VMOT]
```

### 3. LCD Display (16x2, I2C mode)

```
I2C Mode (Preferred):
[VCC]  ──→ 5V
[GND]  ──→ GND
[SDA]  ──→ I2C SDA (STM32 SDA pin, typically on header)
[SCL]  ──→ I2C SCL (STM32 SCL pin, typically on header)
[A]    ──→ 5V (backlight anode, optional resistor)

I2C Address: 0x27 (typical; confirm with I2C scanner)

Parallel Mode (If I2C not available):
[VCC]  ──→ 5V
[GND]  ──→ GND
[RS]   ──→ Pin 12 (STM32)
[RW]   ──→ GND (always write mode)
[EN]   ──→ Pin 11 (STM32)
[D4]   ──→ Pin 5  (STM32)
[D5]   ──→ Pin 4  (STM32)
[D6]   ──→ Pin 3  (STM32)
[D7]   ──→ Pin 2  (STM32)
[A]    ──→ 5V (backlight)
```

### 4. LEDs (4x total: 2 blue, 2 red)

```
Each LED Module (or discrete LED):
[Anode (+)] ──→ [330Ω resistor] ──→ [GPIO pin]
[Cathode (-)] ──→ GND

Connections:
  Blue LED #1 ──→ Pin 10
  Blue LED #2 ──→ Pin A3
  Red LED #1  ──→ Pin A4
  Red LED #2  ──→ Pin A5
```

### 5. Push Buttons (2x: Arm/Standby, Reset)

```
Button with Built-in Resistor:
[One side] ──→ [GPIO pin]
[Other side] ──→ GND

Arduino will enable internal pullup on these pins.

Connections:
  Arm/Standby Button ──→ Pin 13
  Reset Button       ──→ Pin A6
  
(Both pullups enabled in MCU sketch setup)
```

### 6. USB Peripherals (OTG Hub on USB-C)

```
Arduino UNO Q USB-C Port:
  │
  └──[USB-C OTG Hub]
       ├──[USB-A] Logitech C270 Webcam
       ├──[USB-A] USB Speaker
       └──[USB Micro/Mini] MCU Serial Bridge (CH340G or similar)

Linux enumeration:
  lsusb                           # Verify all 3 devices
  /dev/video0                     # Camera
  lsusb -v | grep Audio           # Speaker
  /dev/ttyACM0 or /dev/ttyUSB0   # MCU serial
```

---

## Power Budget & Brownout Prevention

### Current Draw Estimates

| Component | Typical | Peak |
|-----------|---------|------|
| STM32U585 MCU | 20 mA | 50 mA |
| Qualcomm QRB2210 (idle) | 100 mA | 500 mA (WiFi active) |
| 3x Microphones (LM393) | 30 mA | 30 mA |
| LCD 16x2 (backlight + logic) | 60 mA | 60 mA |
| 4x LEDs (full brightness) | 40 mA | 40 mA |
| Stepper motor (stepping) | 200 mA | 400 mA (brief pulse) |
| **Total (steady)** | ~450 mA | — |
| **Total (with stepper moving)** | ~650 mA | ~900 mA (peak) |

### Battery Sizing

**2S LiPo 18650 pack (7.4V):**
- Typical capacity: 2000–3000 mAh
- With 650 mA draw: ~3–4 hours runtime
- **For 5-hour demo:** Charge before booth setup and once mid-day

### Brownout Prevention Checklist

1. **Motor ramp soft-start:**
   - Start stepper at 5% speed, ramp to full over ~500ms
   - See `turret.cpp::tick()` for acceleration ramp

2. **Voltage smoothing:**
   ```
   Across stepper driver VMOT rail:
   +7.4V ──[100μF electrolytic]──┬──[10μF ceramic]── GND
                                  └── [VMOT]
   ```

3. **Separate power rails:**
   - Logic (5V from USB) and motor (7.4V LiPo) **must not share inductance**
   - Use separate GND returns to battery

4. **Battery voltage monitoring:**
   - Check 2S LiPo voltage with multimeter before demo
   - Should read 8.0–8.4V when charged
   - If below 7.0V, do not demo (risk of brownout)

---

## Calibration & Testing

### Step 1: Microphone Baseline

```
With system armed, no sound:
  Measure ADC values over 5 seconds
  Expected: 400–600 ADC units (mid-range)
  
  If baseline very noisy (range >100 units):
    • Check sensor wiring
    • Ensure GND is good
    • Try moving away from RF interference
```

### Step 2: Trigger Threshold

```
Default threshold: baseline + 100 ADC units

To test sensitivity:
  • Clap once, 1 meter away
  • If MCU detects (LED blinks): ✓
  • If not detected: lower threshold in config.yaml
  • Adjust in-room; restart main.py
```

### Step 3: Stepper Movement

```
With system armed:
  $ python3 -c "from linux.bridge import RPCBridge; rpc = RPCBridge(); rpc.connect(); rpc.point_turret(45); print('Sent 45°')"
  
  Observe turret slowly rotate to 45°.
  If not moving:
    • Check battery voltage
    • Verify pins 6–9 in config.h
    • Use test_mcu.py to isolate stepper
```

### Step 4: Camera Capture

```
$ python3 -c "from linux.capture import CaptureModule; cap = CaptureModule(); cap.open_camera(); cap.capture_photo('test.jpg'); print('Photo saved')"

Check ./logs/photos/test.jpg exists.
If not:
  • lsusb | grep Logitech  (verify device)
  • v4l2-ctl --list-devices
  • chmod 666 /dev/video0
```

### Step 5: Audio Record & Playback

```
Test record:
  $ arecord -d 2 -r 16000 -f S16_LE -c 1 /tmp/test.wav
  $ aplay /tmp/test.wav

If fails:
  • arecord -l  (list capture devices)
  • aplay -l    (list playback devices)
  • Use 'hw:X,Y' if default device is wrong
```

---

## Tuning Checklist for Venue

Before demo, adapt to the venue's acoustic & RF environment:

- [ ] Baseline noise level (clap test)
- [ ] Threshold offset adjusted (config.yaml)
- [ ] Stepper speed appropriate for cable (not too fast = tangling risk)
- [ ] Battery voltage verified (8.0+ V)
- [ ] Microphone mounting secure (no vibration)
- [ ] LCD visible from judge's angle
- [ ] LED colors distinct under venue lighting
- [ ] USB hub stable (no loose connectors)

---

**Ready to wire and build!**
