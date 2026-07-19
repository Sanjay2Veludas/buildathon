# Detailed Hardware Wiring Guide (Aligned to Current Code)

This document matches the active implementation in:
- `mcu/main.ino`
- `mcu/sensors.h`
- `mcu/turret.h`
- `mcu/display.h`

## 1) Pin map used by firmware

### Sound sensors (fixed base)
- `A0` -> Sensor S0 (0°)
- `A1` -> Sensor S1 (120°)
- `A2` -> Sensor S2 (240°)
- Sensor power: **3.3V + GND** (common ground)

### Stepper driver pins
The code supports two profiles; selected in `mcu/main.ino`:
- `STEPPER_USE_STEP_DIR = true` (default)

#### STEP/DIR profile (default)
- `D2` -> STEP
- `D3` -> DIR
- `D4` -> EN (optional, active-low assumed)
- Driver VMOT -> battery motor rail
- Driver logic -> 3.3V compatible

#### ULN2003 profile (optional)
- `D2` -> IN1
- `D3` -> IN2
- `D4` -> IN3
- `D5` -> IN4

### LEDs
- `D6` -> RED1
- `D7` -> RED2
- `D8` -> BLUE1
- `D9` -> BLUE2

Use series resistors (220–330 ohm) on each LED line.

### Buttons
- `D10` -> ARM/STANDBY button (INPUT_PULLUP, switch to GND)
- `D11` -> RESET button (INPUT_PULLUP, switch to GND)

### LCD
Default path in code:
- `LCD_USE_I2C = true`
- Connect LCD I2C backpack to board SDA/SCL, VCC, GND
- Typical address: `0x27`

Parallel LCD pins are present in constructor mapping but I2C is the expected demo configuration.

---

## 2) Power wiring

- 2S Li-ion battery (7.4V nominal) -> UNO Q VIN and motor VMOT rail.
- All grounds common: MCU GND, motor driver GND, sensors, LCD, buttons.
- Keep motor current path separate from signal ground where possible (star ground near battery negative).
- Add bulk capacitor near motor driver VMOT (470–1000 uF recommended).

---

## 3) USB topology (Linux side)

`UNO Q USB-C -> OTG hub -> Logitech C270 + USB speaker`

Verify before demo:
- `lsusb`
- `v4l2-ctl --list-devices`
- `arecord -l`
- `aplay -l`

---

## 4) Wiring sanity checklist

1. No shorts between adjacent breadboard rows.
2. Sensor outputs on A0/A1/A2 only.
3. Stepper driver logic pins match selected profile (STEP/DIR vs ULN2003).
4. Button pins pull to GND when pressed.
5. LCD visible and responsive to `lcd_text` command.
6. Turret soft movement verified with `tests/test_turret.py`.

---

## 5) Important constraints

- Use only maker headers (JDIGITAL / JANALOG).
- Do not use 1.8V processor headers.
- Turret rotation is software-limited to ±180°.
- Triggering is muted during turret motion and a 300 ms post-motion window.

This wiring guide intentionally reflects the current repository behavior and avoids legacy references to removed files.