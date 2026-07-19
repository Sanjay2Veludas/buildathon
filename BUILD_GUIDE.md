# Audio-Localizing AI Monitor — 5-Hour Buildathon Build Guide

## Quick Reference: Timeline & Deliverables

### Before Buildathon (Pre-flight Check)

- [ ] Clone/download scaffold code
- [ ] Install Arduino IDE + STM32 board support
- [ ] `pip install -r linux/requirements.txt`
- [ ] Verify ANTHROPIC_API_KEY available (or sign up for free tier)
- [ ] Test `arecord` / `aplay` / `espeak-ng` on Linux box

### Hour 0: Hardware Setup & Verification (30 min)

**Team 1 (Hardware):**
- [ ] Assemble breadboard wiring per [WIRING.md](docs/WIRING.md)
- [ ] Verify all connections with multimeter (no shorts)
- [ ] Power on, check no smoke/excessive heat

**Team 2 (MCU):**
- [ ] Flash `mcu/sketch.ino` to STM32U585 via Arduino IDE
- [ ] Verify MCU appears at `/dev/ttyACM0`
- [ ] Run `tests/test_mcu.py` → should PASS all subsystems

**Team 3 (Linux):**
- [ ] Verify `lsusb` shows: Logitech C270, USB speaker, MCU serial
- [ ] Run `tests/smoke_test.py` → should PASS
- [ ] Confirm `arecord -l` and `aplay -l` list devices

**Synchronization point:** All three teams report "ready" before moving on.

### Hour 1: Integration & Calibration (60 min)

**Team 1 + 2 (RPC Bridge):**
- [ ] Verify `test_mcu.py` commands work (turret rotates, LEDs blink, LCD shows text)
- [ ] Adjust MCU pins in `mcu/config.h` if any mismatches
- [ ] Ensure microphone baselines are stable (~500 ADC units)

**Team 3 (Capture):**
- [ ] Test camera: `python3 -c "from linux.capture import *; CaptureModule().capture_photo()"`
- [ ] Test audio: `arecord -d 3 /tmp/test.wav && aplay /tmp/test.wav`
- [ ] Test TTS: `espeak-ng -w /tmp/test.wav "Testing" && aplay /tmp/test.wav`

**Team 2 + 3 (LLM Integration):**
- [ ] Set `export ANTHROPIC_API_KEY="sk-ant-..."`
- [ ] Test brain.py: `python3 -c "from linux.brain import *; b = Brain(); print(b.analyze_event())"`
- [ ] Confirm canned fallback works if API key invalid

**Synchronization point:** All capture + LLM calls working; no silent failures.

### Hour 2: Full Integration & State Machine (60 min)

**All teams (Main loop):**
- [ ] Start `cd linux && python3 main.py` in terminal
- [ ] System should boot and display "Ready / Listening..." on LCD
- [ ] Create test event: clap loudly near a microphone
- [ ] Observe full flow:
  1. MCU detects bearing → LED blinks yellow
  2. Turret rotates to bearing
  3. System captures 2 photos
  4. LLM analyzes (takes 5–10s)
  5. Speaker says verdict (uses cached TTS if available)
  6. LEDs update (blue=idle, red=alert, etc.)
  7. System returns to "Ready"

**Troubleshooting:**
- If turret doesn't move: check battery voltage, verify stepper pins
- If camera doesn't capture: confirm `/dev/video0` exists
- If LLM fails: check API key, confirm internet connectivity
- If system hangs: press Ctrl+C, check logs in `./logs/monitor_*.log`

**Synchronization point:** One complete end-to-end flow with zero errors.

### Hour 3: Threshold Tuning & Rehearsal (60 min)

**Team 1 + 2 (Sensor tuning):**
- [ ] Measure ambient noise in venue
- [ ] Adjust `config.yaml` `threshold_offset_demo` if needed (lower = more sensitive)
- [ ] Test detection with claps, snaps, dog bark audio
- [ ] Confirm bearing estimates are roughly correct (visual check vs. actual source)

**Team 3 (Demo script):**
- [ ] Record a 5-second "demo trigger" audio clip (dog bark, glass break, clapping)
- [ ] Plan where judge stands and where device sits
- [ ] Prepare talking points:
  - "The MCU hears in real-time and localizes the sound"
  - "The Linux brain analyzes what it sees and hears"
  - "All analysis happens on cloud LLM"
  - "But if Wi-Fi dies, the device still detects and points toward sound"

**Full rehearsal:**
- [ ] Arm device
- [ ] Play demo trigger clip
- [ ] Watch full flow twice (aim for <15 seconds total time)
- [ ] Make notes on timing, any glitches

**Synchronization point:** Rehearsal runs smoothly 2+ times in a row.

### Hour 4: Stretch Goals & Polish (60 min, optional)

**If time permits (choose one or more):**

1. **DC Motor Drive-Toward-Event:**
   - Add 2× DC motors + L298N driver to chassis
   - Uncomment drive logic in `main.py`
   - Test ultrasonic range finder to stop at safe distance

2. **7-Segment Event Counter:**
   - Enable `SEVENSEG_ENABLED` in `mcu/config.h`
   - Increment on each analysis (track in `main.py`)

3. **Advanced Prompting:**
   - Enhance LLM prompt to ask for pose, object detection, etc.
   - Store analysis results in JSON log for demo replay

4. **Visual Improvements:**
   - Add indicator LED that blinks during LLM analysis
   - Show event count on 7-segment display
   - Smooth turret motion with visual feedback on LCD

**No stretch goals?** → Use time for final polish, rehearsal, battery charge, cable tidying.

### Hour 5: Final Checks & Demo Prep (60 min)

**Team 1 (Hardware):**
- [ ] Verify all connectors are seated firmly
- [ ] Check no exposed wires touching wrong pins (shorts)
- [ ] 2S LiPo battery: measure voltage (should be 8.0–8.4V)
- [ ] Charge battery fully
- [ ] Secure all wiring with zip ties or tape

**Team 2 (MCU):**
- [ ] Confirm `/dev/ttyACM0` visible
- [ ] Run `tests/test_mcu.py` one final time → all PASS
- [ ] Ensure MCU sketch is latest (no accidental rollback)

**Team 3 (Linux):**
- [ ] Verify `lsusb` shows all 3 USB devices
- [ ] Confirm `arecord -l` and `aplay -l` work
- [ ] Run `tests/smoke_test.py` one final time → all PASS
- [ ] Audio cache populated: `ls audio_cache/*.wav`
- [ ] API key set: `echo $ANTHROPIC_API_KEY`

**All teams (Demo Walkthrough):**
- [ ] Do one final end-to-end run
- [ ] Judge should see/hear: sound detected → turret moves → photo → spoken analysis
- [ ] Prepare 2-minute elevator pitch
- [ ] Set up in demo area (power, Wi-Fi, microphone placement)
- [ ] Charge 2S LiPo one last time

**Synchronization point:** Device sits in demo area, armed, ready for judge.

---

## File Manifest

After build, you should have:

### MCU (`mcu/`)
```
mcu/
├── sketch.ino               [200 lines] Main entry point
├── config.h                 [80 lines]  Pin map & constants
├── sensors.h / sensors.cpp  [150 lines] Audio acquisition + bearing
├── turret.h / turret.cpp    [120 lines] Stepper motor control
├── display.h / display.cpp  [100 lines] LCD + LED drivers
└── rpc_bridge.h / rpc_bridge.cpp [150 lines] JSON-RPC bridge
```

### Linux (`linux/`)
```
linux/
├── main.py                  [250 lines] State machine (core logic)
├── config.py                [150 lines] Configuration + environment
├── bridge.py                [150 lines] RPC client (MCU comm)
├── capture.py               [150 lines] Camera + audio capture
├── brain.py                 [120 lines] LLM integration + prompts
├── speak.py                 [100 lines] TTS + audio playback
└── requirements.txt         [6 lines]   Python dependencies
```

### Tests (`tests/`)
```
tests/
├── smoke_test.py            [200 lines] Full hardware verification
└── test_mcu.py              [100 lines] MCU subsystem tester
```

### Config & Docs
```
config/
├── config.yaml              [70 lines]  External runtime config
docs/
├── WIRING.md                [300 lines] Detailed pin map + calibration
└── README.md                [500 lines] Full project guide
```

**Total:** ~2500 lines of production-quality, documented code (scaffolded for 5 hours)

---

## Failure Recovery

### "Turret motor draws too much current"
- Stop immediately; unplug battery
- Check for shorts in stepper pins or driver
- Verify ULN2003 connections
- Try lower `STEPPER_MAX_RPM` in config.h

### "LLM call times out"
- System automatically falls back to canned response
- Spoken verdict still plays (from cache)
- Check `llm_timeout_sec` in config.yaml

### "Camera not capturing"
- Run `v4l2-ctl --list-devices` to find correct `/dev/video*`
- Update `capture.py` `find_camera()` function
- Or manually set `self.camera_idx = X` where X matches device

### "System hangs on startup"
- Press Ctrl+C
- Check `/dev/ttyACM0` exists: `ls /dev/ttyACM0`
- Try `stty -F /dev/ttyACM0 115200` to manually configure
- If still hangs, MCU may need reflash

### "Microphone not triggering"
- Baseline too high or threshold too high
- Lower `threshold_offset_demo` in config.yaml
- Restart `main.py`
- Clap loudly directly into a sensor

---

## Demo Theater Script

**Opening (30 seconds):**
> "This is an audio-localizing AI monitor. It listens for events and figures out what's happening using computer vision and cloud AI. It's built on a dual-brain platform—the microcontroller handles real-time sensing and motor control, while the Linux side does the thinking."

**Trigger Event (2 minutes):**
> "I'm going to play a dog barking sound. Watch what happens..."
> [Play audio clip near microphone]
> "Did you hear? The device detected it, figured out which direction it came from, and pointed its camera there. Now it's sending a photo and audio recording to our cloud LLM..."
> [Wait 8–10 seconds]
> "And it just recognized it was a dog barking. The speaker is telling us what it heard."

**Q&A (optional):**
> **Judge:** "What if Wi-Fi fails?"
> **You:** "Great question. Even offline, the device still detects the sound, points the camera, and can give a local response using pre-recorded audio. Let me show you..." [Disable Wi-Fi, trigger again]

---

## Success Criteria

✓ **Must-haves (to score points):**
1. Dual-brain architecture visible (MCU + Linux + RPC)
2. Motion (stepper turret rotates toward sound)
3. AI (cloud LLM identifies event)
4. Real-time responsiveness (detect → point → analyze in <20 seconds)
5. Demo doesn't crash during judge observation

✓ **Nice-to-haves (for competitive edge):**
- Offline fallback works (Wi-Fi fails, device still operates)
- Visual/audio feedback polished (LEDs, LCD, TTS clear and responsive)
- Calibration tuned for venue (no false positives)
- Novel use case (judges say "we haven't seen that before")
- Code is modular and well-documented (shows engineering discipline)

---

## Team Roles Summary

| Role | Responsibilities | Deliverables |
|------|------------------|--------------|
| **Hardware + MCU** | Wiring, soldering, MCU firmware, stepper/sensor testing | Functioning MCU + hardware test scripts passing |
| **Linux Integration** | RPC bridge, camera/audio capture, module integration | Capture pipeline + LLM + TTS working end-to-end |
| **Demo + Brain** | LLM integration, state machine orchestration, rehearsal | Working main.py, smooth 5-minute demo flow, talking points |

---

## Final Checklist Before Demo

```
HARDWARE
- [ ] All connectors seated and verified with multimeter
- [ ] 2S LiPo battery charged (8.3+ V)
- [ ] No smoke or unusual heat when powered

MCU
- [ ] /dev/ttyACM0 visible and responding
- [ ] test_mcu.py passes all subsystems
- [ ] LEDs blink, LCD shows text, stepper moves

LINUX
- [ ] lsusb shows camera, speaker, MCU
- [ ] smoke_test.py passes all checks
- [ ] ANTHROPIC_API_KEY set in shell
- [ ] Audio cache populated

DEMO
- [ ] End-to-end flow runs without errors 2+ times
- [ ] Sound trigger works reliably
- [ ] Turret points in roughly correct direction
- [ ] LLM response sensible and spoken
- [ ] Demo takes <2 minutes total
- [ ] Backup: offline mode works (Wi-Fi disabled)

STAGE
- [ ] Device positioned clearly for judge to see/hear
- [ ] Microphone placement optimized (not blocked by moving parts)
- [ ] Power/Wi-Fi cables neatly secured
- [ ] Team ready with talking points
```

---

**Build successfully. Demo confidently. Good luck!** 🚀

*Generated: July 2026 | Arduino UNO Q 2GB Hardware Buildathon*
