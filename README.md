# Audio-Localizing AI Monitor (Online-Only MVP)

Hackathon scaffold for **sound -> look -> understand -> act** using:
- **MCU side:** Arduino-style sketch on UNO Q (STM32U585 side)
- **Linux side:** Python state machine on QRB2210 Debian side
- **Cloud side:** Anthropic multimodal analysis (online required)

## Repository layout

- `mcu/`
  - `main.ino`
  - `sensors.h`
  - `turret.h`
  - `display.h`
- `linux/`
  - `main.py`
  - `capture.py`
  - `brain.py`
  - `speak.py`
  - `bridge.py`
  - `config.yaml`
- `tests/`
  - `test_mics.py`
  - `test_turret.py`
  - `test_camera.py`
  - `test_audio_out.py`
  - `test_llm.py`
  - `test_network.py`
  - `test_mcu.py`
  - `smoke_test.py`

---

## Wiring table (default pin map)

### Sound sensors
| Component | UNO Q pin | Notes |
|---|---|---|
| Sensor S0 AO (0 deg) | A0 | Analog output |
| Sensor S1 AO (120 deg) | A1 | Analog output |
| Sensor S2 AO (240 deg) | A2 | Analog output |
| Sensor VCC | 3.3V | Keep logic-safe |
| Sensor GND | GND | Common ground |

### Stepper driver (STEP/DIR mode)
| Driver pin | UNO Q pin |
|---|---|
| STEP | D2 |
| DIR | D3 |
| EN (optional) | D4 |

### Stepper driver (ULN2003 alternate)
| Driver pin | UNO Q pin |
|---|---|
| IN1 | D2 |
| IN2 | D3 |
| IN3 | D4 |
| IN4 | D5 |

### LEDs
| LED | UNO Q pin |
|---|---|
| RED1 | D6 |
| RED2 | D7 |
| BLUE1 | D8 |
| BLUE2 | D9 |

### Buttons
| Button | UNO Q pin | Wiring |
|---|---|---|
| ARM/STANDBY | D10 | INPUT_PULLUP, switch to GND |
| DEMO RESET | D11 | INPUT_PULLUP, switch to GND |

### LCD 16x2
- Recommended: I2C backpack on SDA/SCL
- Alternative parallel pins configured in `main.ino`

### USB topology
`UNO Q USB-C -> OTG hub -> Logitech C270 + USB speaker`

---

## Power and safety

1. 2S Li-ion (+) -> UNO Q VIN and motor VMOT.
2. Battery (-) -> common ground bus.
3. Star-ground motor and logic returns near battery negative.
4. Add 470-1000uF bulk cap near motor driver.
5. Use maker headers only (JDIGITAL/JANALOG), not 1.8V processor headers.

---

## Bring-up order (must follow)

1. Flash MCU sketch and open serial monitor at 115200.
2. Verify button presses and LED/LCD behavior.
3. Run turret test at low speed.
4. Connect OTG hub with camera + speaker.
5. Run smoke tests:
   - `python3 tests/test_network.py`
   - `python3 tests/test_llm.py`
   - `python3 tests/test_camera.py`
   - `python3 tests/test_audio_out.py`
   - `python3 tests/test_mics.py`
   - `python3 tests/test_turret.py`
6. Start Linux state machine:
   - `python3 linux/main.py`

---

## Dependencies (Linux side)

System packages:
- `python3`, `python3-pip`
- `espeak-ng`, `alsa-utils`, `v4l-utils`, `usbutils`

Python packages:
- `pyserial`
- `opencv-python`
- `requests`
- `pyyaml`

Install (quick):
```bash
pip3 install pyserial opencv-python requests pyyaml
```

Install (pinned from requirements):
```bash
pip3 install -r linux/requirements.txt
```

---

## Online-only behavior

- Cloud call is required for event classification.
- If cloud/network/capture fails, system enters FAULT state, announces unavailability, and re-arms.
- No offline inference path in this MVP.

---

## Extended docs

- Build execution guide: `BUILD_GUIDE.md`
- Detailed wiring and power notes: `docs/WIRING.md`

## Demo-day checklist

- Charge battery pack fully.
- Verify camera and speaker enumerate via `lsusb`.
- Export API key:
  - `export GEMINI_API_KEY=...`
- Tune threshold in-room (`trigger_threshold` in `linux/config.yaml` and runtime command support).
- Rehearse 3 event classes and LED/LCD transitions.
- Keep spare OTG hub/cable ready.
