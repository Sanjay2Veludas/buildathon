# Audio-Localizing AI Monitor — 5-Hour Build Guide (Online-Only)

This guide is aligned to the **current merged codebase** on branch `abhijith`.

## Current source of truth
- MCU entry: `mcu/main.ino`
- Linux entry: `linux/main.py`
- Runtime config: `linux/config.yaml`
- Core smoke tests: `tests/test_network.py`, `tests/test_llm.py`, `tests/test_camera.py`, `tests/test_audio_out.py`, `tests/test_mics.py`, `tests/test_turret.py`, `tests/test_mcu.py`, `tests/smoke_test.py`

---

## 0) Pre-flight (before build session)
- Install dependencies:
  - `pip3 install -r linux/requirements.txt`
- Install system tools:
  - `espeak-ng`, `alsa-utils`, `v4l-utils`, `usbutils`
- Export API key:
  - `export ANTHROPIC_API_KEY="..."`
- Confirm board enumerates on serial (`/dev/ttyACM0` expected).

---

## 1) Hour 0 — hardware + power sanity

### Wiring reference
Use `README.md` and `docs/WIRING.md`.

### Must-pass checks
- No shorts, shared common ground, motor VMOT and logic rails correct.
- USB-C OTG hub enumerates camera + speaker.
- Battery voltage in safe range for demo.

### Commands
```bash
python3 tests/smoke_test.py
python3 tests/test_mcu.py
```

---

## 2) Hour 1 — MCU validation

Flash `mcu/main.ino` and validate:
- `ping` returns `{"type":"pong"}`
- `point_turret deg=...` works and emits `motion_complete`
- `set_led level=0..3` updates indicators
- `lcd_text l1="..." l2="..."` updates LCD
- `set_threshold value=...` adjusts detection sensitivity

Run:
```bash
python3 tests/test_mics.py
python3 tests/test_turret.py
python3 tests/test_mcu.py
```

---

## 3) Hour 2 — Linux capture + audio path

Run:
```bash
python3 tests/test_camera.py
python3 tests/test_audio_out.py
```

Verify:
- Camera captures frames under `artifacts/`
- TTS plays through USB speaker
- Audio capture completes with `arecord`

---

## 4) Hour 3 — cloud path (online-only MVP)

Run:
```bash
python3 tests/test_network.py
python3 tests/test_llm.py
```

Then run full app:
```bash
python3 linux/main.py
```

Expected flow:
`IDLE -> EVENT -> POINTING -> CAPTURING -> ANALYZING -> RESPONDING -> ACTION -> IDLE`

If cloud/network fails, system enters FAULT and announces unavailability; no offline inference mode is used in this MVP.

---

## 5) Hour 4 — tune + rehearse

Tune in `linux/config.yaml`:
- `sensors.trigger_threshold`
- `turret.motion_timeout_s`
- `brain.timeout_s`, `brain.retry_count`

Rehearse 2–3 complete trigger cycles and ensure stable timing.

---

## 6) Hour 5 — demo lock

Final checklist:
- `python3 tests/smoke_test.py` passes
- `python3 tests/test_llm.py` passes
- End-to-end flow succeeds twice consecutively
- Spare cable/hub ready
- Battery charged

---

## Known failure handling

- **Camera missing**: check `lsusb`, `v4l2-ctl --list-devices`
- **MCU serial missing**: check `/dev/ttyACM0` and cabling
- **LLM timeout**: verify network and API key, check `brain.timeout_s`
- **Motor-induced false trigger**: ensure motion mute logic active (built into MCU)

This guide intentionally prioritizes demo reliability and deterministic behavior over feature breadth.