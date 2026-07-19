# Detailed Hardware Wiring Guide (Aligned to Current Code)

This document matches the active implementation in:
- `mcu/main.ino`
- `mcu/sensors.h`
- `mcu/turret.h`
- `mcu/display.h`

## 1) Pin map used by firmware

### Sound sensors — passive condenser mic bias circuit
One circuit per mic, built on breadboard. Wire the output to A0 / A1 / A2.

```
3.3V ──┬── 330K ──┬── 330K ── GND
       │          │
      n/a       22nF (DC block)
                  │
                6.8K ── mic(+)
                          mic(–) ── GND
                  │
                470pF ── GND
                  │
               A0 / A1 / A2
```

| Pin | Mic / bearing |
|-----|---------------|
| `A0` | Mic S0 — 0° |
| `A1` | Mic S1 — 120° |
| `A2` | Mic S2 — 240° |

- Mic power: **3.3V + GND** shared rail on breadboard
- Twist the two mic leads when extending with jumper wires to reduce noise pickup
- Do not run mic leads parallel to motor wires

### Stepper driver pins
Profile selected in `mcu/main.ino` via `STEPPER_USE_STEP_DIR`.

#### ULN2003 profile — **active** (`STEPPER_USE_STEP_DIR = false`, 28BYJ-48)
- `D2` -> IN1
- `D3` -> IN2
- `D4` -> IN3
- `D5` -> IN4
- ULN2003 VCC -> 5V, GND -> GND

#### STEP/DIR profile — inactive (`STEPPER_USE_STEP_DIR = true`)
- `D2` -> STEP
- `D3` -> DIR
- `D4` -> EN (active-low)
- Driver VMOT -> motor power rail

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