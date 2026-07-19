#pragma once

#include <Arduino.h>
#include <stdint.h>

struct SoundEvent {
  float bearing_deg;
  uint16_t amplitudes[3];
  uint32_t timestamp_ms;
};

class SoundSensors {
 public:
  SoundSensors(uint8_t pin0, uint8_t pin1, uint8_t pin2)
      : pins_{pin0, pin1, pin2}, trigger_threshold_(120U),
        baseline_alpha_num_(1U), baseline_alpha_den_(64U),
        refractory_ms_(500U), window_ms_(100U),
        last_trigger_ms_(0U), sample_interval_ms_(1U),
        last_sample_ms_(0U), capture_active_(false), capture_start_ms_(0U) {
    for (uint8_t i = 0U; i < 3U; i++) {
      baseline_[i] = 0U;
      current_[i] = 0U;
      peak_[i] = 0U;
    }
  }

  void begin(void) {
    for (uint8_t i = 0U; i < 3U; i++) {
      pinMode(pins_[i], INPUT);
    }
    // Warm-up baseline with deterministic fixed samples.
    const uint16_t warmup_samples = 128U;
    for (uint16_t n = 0U; n < warmup_samples; n++) {
      for (uint8_t i = 0U; i < 3U; i++) {
        uint16_t v = static_cast<uint16_t>(analogRead(pins_[i]));
        baseline_[i] = static_cast<uint16_t>((baseline_[i] + v) / 2U);
      }
      delay(1U);
    }
  }

  void setTriggerThreshold(uint16_t threshold) { trigger_threshold_ = threshold; }
  uint16_t triggerThreshold(void) const { return trigger_threshold_; }

  void setRefractoryMs(uint16_t refractory_ms) { refractory_ms_ = refractory_ms; }

  bool update(bool muted, SoundEvent* out_event) {
    if (out_event == nullptr) {
      return false;
    }

    const uint32_t now = millis();
    if ((now - last_sample_ms_) < sample_interval_ms_) {
      return false;
    }
    last_sample_ms_ = now;

    sampleAndTrack();

    if (muted) {
      capture_active_ = false;
      return false;
    }

    if (capture_active_) {
      if ((now - capture_start_ms_) >= window_ms_) {
        capture_active_ = false;
        out_event->bearing_deg = estimateBearing();
        for (uint8_t i = 0U; i < 3U; i++) {
          out_event->amplitudes[i] = peak_[i];
        }
        out_event->timestamp_ms = now;
        last_trigger_ms_ = now;
        return true;
      }
      return false;
    }

    if ((now - last_trigger_ms_) < refractory_ms_) {
      return false;
    }

    bool triggered = false;
    for (uint8_t i = 0U; i < 3U; i++) {
      if (current_[i] > static_cast<uint16_t>(baseline_[i] + trigger_threshold_)) {
        triggered = true;
      }
    }

    if (triggered) {
      capture_active_ = true;
      capture_start_ms_ = now;
      for (uint8_t i = 0U; i < 3U; i++) {
        peak_[i] = current_[i];
      }
    }

    return false;
  }

 private:
  uint8_t pins_[3];
  uint16_t baseline_[3];
  uint16_t current_[3];
  uint16_t peak_[3];
  uint16_t trigger_threshold_;
  uint16_t baseline_alpha_num_;
  uint16_t baseline_alpha_den_;
  uint16_t refractory_ms_;
  uint16_t window_ms_;
  uint32_t last_trigger_ms_;
  uint8_t sample_interval_ms_;
  uint32_t last_sample_ms_;
  bool capture_active_;
  uint32_t capture_start_ms_;

  void sampleAndTrack(void) {
    for (uint8_t i = 0U; i < 3U; i++) {
      uint16_t v = static_cast<uint16_t>(analogRead(pins_[i]));
      current_[i] = v;
      if (capture_active_ && (v > peak_[i])) {
        peak_[i] = v;
      }
      // IIR baseline update: baseline = baseline*(1-a)+v*a
      // register/intended effect: adaptive ambient tracking.
      uint32_t old_part = static_cast<uint32_t>(baseline_[i]) * (baseline_alpha_den_ - baseline_alpha_num_);
      uint32_t new_part = static_cast<uint32_t>(v) * baseline_alpha_num_;
      baseline_[i] = static_cast<uint16_t>((old_part + new_part) / baseline_alpha_den_);
    }
  }

  float estimateBearing(void) const {
    const float bearings[3] = {0.0F, 120.0F, 240.0F};

    uint8_t max1 = 0U;
    uint8_t max2 = 1U;
    if (peak_[max2] > peak_[max1]) {
      uint8_t t = max1;
      max1 = max2;
      max2 = t;
    }

    for (uint8_t i = 2U; i < 3U; i++) {
      if (peak_[i] > peak_[max1]) {
        max2 = max1;
        max1 = i;
      } else if (peak_[i] > peak_[max2]) {
        max2 = i;
      }
    }

    const float a = static_cast<float>(peak_[max1]);
    const float b = static_cast<float>(peak_[max2]);
    const float denom = a + b + 1.0F;
    const float ratio = b / denom;
    float bearing = bearings[max1] * (1.0F - ratio) + bearings[max2] * ratio;

    if (bearing > 180.0F) {
      bearing -= 360.0F;
    }
    return bearing;
  }
};
