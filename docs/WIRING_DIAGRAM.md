# Audio-Localizing AI Monitor - Wiring Diagram

## System Overview (Block Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                   AUDIO-LOCALIZING AI MONITOR ARCHITECTURE                  │
│                                                                             │
│  ┌──────────────────────────┐              ┌──────────────────────────┐   │
│  │   MCU SIDE                │              │   LINUX SIDE             │   │
│  │   (STM32U585)             │              │   (Qualcomm QRB2210)     │   │
│  │                           │              │                          │   │
│  │  • Audio Sampling (1kHz)  │  ┌────────┐ │  • LLM API calls         │   │
│  │  • Bearing Estimation     │──│ RPC    │──  • Photo/Audio capture   │   │
│  │  • Motor Control          │  │ Bridge │ │  • TTS playback          │   │
│  │  • LED/LCD Display        │  └────────┘ │  • State machine         │   │
│  │  • Button inputs          │  (JSON/USB) │  • Orchestration         │   │
│  │                           │              │                          │   │
│  └──────────────────────────┘              └──────────────────────────┘   │
│                                                                             │
│           Cloud API (Anthropic Claude) ←→ (if Wi-Fi available)            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Wiring Diagram (Top View)

```
                         ┌─────────────────────────────────────┐
                         │   ARDUINO UNO Q 2GB                 │
                         │   (STM32U585 + Qualcomm QRB2210)    │
                         │                                     │
        ANALOG INPUT      │    DIGITAL I/O                     │
        (0-5V / 10-bit)   │                                    │
                          │ 13 12 11 10 A3 A2 A1 A0           │
        ┌──────────────┐  │  └──┘ └──┘ └──┘ └──┘ └──┘ └──┘    │
        │   MIC #1     │──┤A0                                  │
        │ (LM393, 0°)  │  │                                    │
        └──────────────┘  │ ┌──────────────────────────────┐  │
                          │ │       POWER RAILS            │  │
        ┌──────────────┐  │ │  GND (all components)        │  │
        │   MIC #2     │──┤A1 5V  (sensors, LEDs, LCD)     │  │
        │(LM393, 120°) │  │ 7.4V (stepper motor only)      │  │
        └──────────────┘  │ └──────────────────────────────┘  │
                          │                                    │
        ┌──────────────┐  │                                    │
        │   MIC #3     │──┤A2                                  │
        │(LM393, 240°) │  │                                    │
        └──────────────┘  │                                    │
                          │  6  7  8  9 (STEPPER PINS)        │
                          └─────────────────────────────────────┘
                                      ▼
                   ┌──────────────────────────────────┐
                   │   ULN2003 STEPPER DRIVER         │
                   │   (4-phase coil sequencer)       │
                   │                                  │
                   │  IN1 → Pin 6                     │
                   │  IN2 → Pin 7                     │
                   │  IN3 → Pin 8                     │
                   │  IN4 → Pin 9                     │
                   │                                  │
                   │  [Motor coils: A, B, C, D]       │
                   │                                  │
                   │  VMOT → +7.4V (direct)           │
                   │  GND  → Common GND               │
                   └──────────────────────────────────┘
                                      ▼
                          ┌────────────────────┐
                          │  28BYJ-48 Stepper  │
                          │  Motor + Turret    │
                          │  (Rotates camera)  │
                          └────────────────────┘


             DIGITAL OUTPUT (3.3V logic)
             ┌─────────────────────┐
             │  Pin 10 → Blue LED #1 ────[330Ω]──→ GND
             │  Pin A3 → Blue LED #2 ────[330Ω]──→ GND
             │  Pin A4 → Red LED #1 ─────[330Ω]──→ GND
             │  Pin A5 → Red LED #2 ─────[330Ω]──→ GND
             │                                     
             │  Pin 11 → LCD EN (parallel mode)
             │  Pin 12 → LCD RS (parallel mode)
             │   (or I2C: SDA/SCL if I2C mode)
             └─────────────────────┘

             DIGITAL INPUT (buttons, pullup)
             ┌─────────────────────┐
             │  Pin 13 → [Button: Arm/Standby] ──┐
             │  Pin A6 → [Button: Reset]         │
             │                                    └──→ GND
             │  (Internal pullups enabled)
             └─────────────────────┘

             I2C/SERIAL (fixed pins)
             ┌─────────────────────┐
             │  SDA → LCD I2C (0x27)
             │  SCL → LCD I2C (0x27)
             │                    
             │  TX → Debug (optional)
             │  RX → Debug (optional)
             └─────────────────────┘

             USB-C OTG HUB (single port)
             ┌─────────────────────────────┐
             │  USB-A → Logitech C270 cam  │
             │  USB-A → USB Speaker        │
             │  USB Micro → MCU Serial     │
             └─────────────────────────────┘


                         ┌──────────────────┐
                         │  POWER SUPPLY    │
                         │                  │
                         │  2S LiPo Battery │
                         │  7.4V (charged)  │
                         │  2000-3000 mAh   │
                         │                  │
                         │  +7.4V ──→ Stepper VMOT
                         │  GND ───→ Common GND
                         │                  │
                         │  (USB provides   │
                         │   5V logic rail) │
                         └──────────────────┘
```

---

## Detailed Component Connections Table

### Microphone Array (Fixed Base, 120° Apart)

```
Component: 3x LM393 Sound Sensor Modules

Layout (top-down view):

          MIC #2 (120°)
                |
                |
   MIC #3 ──────●────── MIC #1
   (240°)     CENTER    (0°)
              POINT


Wiring:
┌─────────────┬────────────────┬─────────────────────┐
│ Sensor      │ Arduino Pin    │ Notes               │
├─────────────┼────────────────┼─────────────────────┤
│ MIC#1 OUT   │ A0             │ Bearing 0° (front)  │
│ MIC#1 VCC   │ 5V             │                     │
│ MIC#1 GND   │ GND            │ Common ground       │
├─────────────┼────────────────┼─────────────────────┤
│ MIC#2 OUT   │ A1             │ Bearing 120°        │
│ MIC#2 VCC   │ 5V             │                     │
│ MIC#2 GND   │ GND            │                     │
├─────────────┼────────────────┼─────────────────────┤
│ MIC#3 OUT   │ A2             │ Bearing 240°        │
│ MIC#3 VCC   │ 5V             │                     │
│ MIC#3 GND   │ GND            │                     │
└─────────────┴────────────────┴─────────────────────┘
```

### Stepper Motor System

```
ULN2003 Driver Pin Connections:

┌──────────────────────────────────────────────────┐
│         ULN2003 Stepper Driver                   │
│                                                  │
│  [VCC]      ──→  5V                              │
│  [GND]      ──→  GND (common)                    │
│                                                  │
│  [IN1]      ──→  Arduino Pin 6                   │
│  [IN2]      ──→  Arduino Pin 7                   │
│  [IN3]      ──→  Arduino Pin 8                   │
│  [IN4]      ──→  Arduino Pin 9                   │
│                                                  │
│  [+MOTOR]   ──→  +7.4V (direct from LiPo)       │
│  [GND]      ──→  GND (battery return)            │
│                                                  │
│  [COIL-A]   ──→  28BYJ-48 Wire 1 (Red)           │
│  [COIL-B]   ──→  28BYJ-48 Wire 2 (Pink)          │
│  [COIL-C]   ──→  28BYJ-48 Wire 3 (Orange)        │
│  [COIL-D]   ──→  28BYJ-48 Wire 4 (Yellow)        │
│                                                  │
└──────────────────────────────────────────────────┘

Power Rail Decoupling (CRITICAL for brownout prevention):

    +7.4V ──────[100µF Electrolytic]──┬──[10µF Ceramic]── GND
                                      │
                                    [VMOT]
                                      │
                            ULN2003 Motor Driver
```

### Display & Buttons

```
LCD 16x2 (I2C Mode - Preferred):

┌─────────────────────────────────────┐
│  LCD I2C Module (addr 0x27)         │
│                                     │
│  [VCC]   ──→  5V                    │
│  [GND]   ──→  GND                   │
│  [SDA]   ──→  Arduino I2C SDA       │
│  [SCL]   ──→  Arduino I2C SCL       │
│  [A]     ──→  5V (backlight)        │
│  [K]     ──→  GND (optional R)      │
│                                     │
└─────────────────────────────────────┘

LED & Button Connections:

┌──────────┬─────────────┬──────────────────────┐
│Component │Pin          │Wiring                │
├──────────┼─────────────┼──────────────────────┤
│Blue LED1 │10           │[+pin]─[330Ω]─[GND]  │
│Blue LED2 │A3           │[+pin]─[330Ω]─[GND]  │
│Red LED1  │A4           │[+pin]─[330Ω]─[GND]  │
│Red LED2  │A5           │[+pin]─[330Ω]─[GND]  │
├──────────┼─────────────┼──────────────────────┤
│Btn Arm   │13           │[Pin]─[GND] (pullup) │
│Btn Reset │A6           │[Pin]─[GND] (pullup) │
└──────────┴─────────────┴──────────────────────┘

```

### USB Peripherals (OTG Hub on USB-C)

```
┌────────────────────────────────────────────┐
│  Arduino UNO Q USB-C Port                  │
│                                            │
│  ↓ USB-C OTG Hub                           │
│                                            │
│  ├─ USB-A Port 1 → Logitech C270 Camera   │
│  │                  (/dev/video0)          │
│  │                  (captures photos)      │
│  │                                         │
│  ├─ USB-A Port 2 → USB Speaker            │
│  │                  (audio playback)       │
│  │                  (ALSA device)          │
│  │                                         │
│  └─ USB Micro    → MCU Serial Bridge       │
│                     (CH340G or similar)    │
│                     (/dev/ttyACM0)         │
│                     (JSON-RPC commands)    │
│                                            │
└────────────────────────────────────────────┘
```

---

## Complete Power Distribution Schematic

```
                    ┌──────────────────┐
                    │  2S LiPo Battery │
                    │  7.4V charged    │
                    │  2000-3000 mAh   │
                    └────────┬──────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              [7.4V Rail]        [GND Rail]
                    │                 │
        ┌───────────┼─────────────────┼──────────────┐
        │           │                 │              │
        │      [ULN2003 VMOT]    (Common)       (Common)
        │      [Stepper Motor]                       │
        │      [100µF || 10µF]                      │
        │      (soft-start, ramping)                 │
        │                                            │
        │      ┌──────────────────┐                 │
        │      │ Arduino VIN/USB  │                 │
        │      │   5V Rail        │                 │
        │      └────────┬─────────┘                 │
        │             │                              │
        └─────────────┼──────────────────────────────┘
                      │
         ┌────────────┼─────────────────┐
         │            │                 │
    [Sensors]    [LEDs+LCD]        [Other]
     (5V, 30mA)  (5V, 60mA)    (5V, 100mA)
         │            │                 │
         └────────────┴─────────────────┴─── GND

Current Budget:
┌─────────────────────┬──────────┬──────┐
│ Component           │ Typical  │ Peak │
├─────────────────────┼──────────┼──────┤
│ MCU (logic)         │ 20 mA    │ 50mA │
│ Qualcomm QRB2210    │ 100mA    │500mA │
│ 3x Sensors (5V)     │ 30 mA    │ 30mA │
│ LCD + backlight     │ 60 mA    │ 60mA │
│ 4x LEDs             │ 40 mA    │ 40mA │
│ ─────────────────   │──────    │──── │
│ TOTAL (steady)      │ 450 mA   │ —    │
│ TOTAL (motor move)  │ 650 mA   │900mA │
├─────────────────────┼──────────┼──────┤
│ 2S LiPo Capacity    │ 2000 mAh │ —    │
│ Runtime (650 mA)    │ 3 hours  │ —    │
└─────────────────────┴──────────┴──────┘
```

---

## Signal Flow Diagram (Data Path)

```
┌─────────────────┐
│  Microphones    │  1 kHz ADC sampling (STM32 ISR)
│   3x LM393      │
└────────┬────────┘
         │ (A0, A1, A2 analog 0-5V)
         ▼
┌─────────────────┐
│ MCU ADC Buffer  │  Circular buffer per channel
│ (Sensors.cpp)   │  Baseline tracking, peak detection
└────────┬────────┘
         │
         ├─ Amplitude comparison ─────┐
         │ (relative strength)         │
         ▼                             ▼
    [Bearing Estimation]         [Trigger Detection]
         │                             │
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌──────────────────────────┐
         │ EVENT: {bearing, amps}   │
         │ Published via RPC Bridge │
         └──────────┬───────────────┘
                    │ (JSON/Serial)
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌─────────────┐    ┌──────────────┐
    │ MCU: Point  │    │ Linux: Main  │
    │ Turret to   │    │ State Machine│
    │ Bearing     │    │ (main.py)    │
    └─────────────┘    └──────────────┘
         │                     │
         │                     ├─→ RPC: turret.pointTo(bearing)
         │                     ├─→ RPC: set_led("event")
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │ Capture Mod  │
         │              │ (Camera+Audio│
         │              └──────┬───────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │ Brain Module │
         │              │ (LLM API)    │
         │              └──────┬───────┘
         │                     │
         │                     ▼
         │              ┌──────────────┐
         │              │ Speak Module │
         │              │ (TTS+Playback│
         │              └──────┬───────┘
         │                     │
         │                     ▼
         └─────────────────────→ RPC: set_led(severity)
                                RPC: lcd_text(response)
```

---

## Assembly Order (Recommended)

```
PHASE 1: Power & Ground (30 min)
  1. Connect battery to breadboard rails
  2. Verify 7.4V on motor rail, 5V on logic rail
  3. Verify no voltage between same-polarity rails (shorts)

PHASE 2: MCU & Sensors (60 min)
  1. Connect 3x microphones to A0, A1, A2
  2. Connect sensor GND to common GND
  3. Flash MCU sketch; verify `/dev/ttyACM0` appears
  4. Run test_mcu.py → PASS (audio baseline should stabilize)

PHASE 3: Motor & Driver (45 min)
  1. Connect stepper pins (6, 7, 8, 9) to ULN2003
  2. Connect ULN2003 motor power (7.4V, GND)
  3. Add 100µF + 10µF capacitors across VMOT
  4. Run test_mcu.py → turret.pointTo(45) should rotate stepper slowly

PHASE 4: Display & Control (45 min)
  1. Connect LCD (I2C or parallel mode)
  2. Connect 4x LEDs via 330Ω resistors
  3. Connect 2x buttons with internal pullups
  4. Run test_mcu.py → LCD text, LED colors, buttons should work

PHASE 5: USB Peripherals (30 min)
  1. Attach USB OTG hub to single USB-C port
  2. Plug in: Camera, Speaker, Serial bridge
  3. Run smoke_test.py → lsusb should show all 3 devices
  4. Verify /dev/video0, aplay -l, /dev/ttyACM0 exist

PHASE 6: Integration & Test (60 min)
  1. Boot Linux side; run main.py
  2. Create test event; observe full flow
  3. Verify RPC commands work
  4. Calibrate thresholds for venue noise
```

---

## Troubleshooting Quick Reference

```
If stepper doesn't move:
  ✓ Check battery: 7.4V+ on motor rail
  ✓ Verify pins 6,7,8,9 connected to ULN2003
  ✓ Check capacitor placement (100µF || 10µF)
  ✓ Try lower STEPPER_MAX_RPM in config.h

If microphone won't trigger:
  ✓ Check A0, A1, A2 connected to sensor OUT
  ✓ Lower THRESHOLD_OFFSET in config.yaml
  ✓ Verify sensor baseline is stable (~500 ADC units)
  ✓ Test each mic individually with clap test

If camera/speaker not found:
  ✓ Verify lsusb shows all 3 devices
  ✓ Try different USB hub (OTG flakiness common)
  ✓ Power cycle MCU + hub
  ✓ Check /dev/video0, aplay -l exist

If LCD not displaying:
  ✓ Check I2C address: run i2c-detect 1 (if I2C)
  ✓ Verify SDA/SCL connected
  ✓ Test with parallel mode if I2C fails

If system hangs:
  ✓ Check battery voltage (should stay >7V under load)
  ✓ Look for shorts (multimeter resistance between rail pairs)
  ✓ Try reflashing MCU (upload latest sketch)
```

---

This wiring diagram and schematic should give you everything needed to wire the system. **Print this page and bring it to the demo!**
