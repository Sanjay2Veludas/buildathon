#pragma once

#include <Arduino.h>
#include <stdint.h>

enum class StepperProfile : uint8_t {
  STEP_DIR = 0U,
  ULN2003 = 1U,
};

class Turret {
 public:
  // steps_per_rev: full mechanical steps per output-shaft revolution (before microstep multiply).
  // microstep: subdivisions per step (8 = half-step, matches ULN2003 sequence length).
  // 28BYJ-48 + ULN2003: steps_per_rev=512, microstep=8 → 4096 half-steps/rev.
  // Generic STEP/DIR 1.8° motor at 8x driver microstepping: steps_per_rev=200, microstep=8.
  Turret(StepperProfile profile, uint8_t pin_a, uint8_t pin_b, uint8_t pin_c, uint8_t pin_d,
         uint16_t steps_per_rev = 512U, uint8_t microstep = 8U)
      : profile_(profile), pin_a_(pin_a), pin_b_(pin_b), pin_c_(pin_c), pin_d_(pin_d),
        current_deg_(0.0F), target_deg_(0.0F), min_deg_(-180.0F), max_deg_(180.0F),
        steps_per_rev_(steps_per_rev), microstep_(microstep), current_step_(0L), target_step_(0L),
        moving_(false), move_end_ms_(0U), mute_until_ms_(0U),
        step_interval_us_(1200U), last_step_us_(0U) {}

  void begin(void) {
    pinMode(pin_a_, OUTPUT);
    pinMode(pin_b_, OUTPUT);
    pinMode(pin_c_, OUTPUT);
    pinMode(pin_d_, OUTPUT);
    digitalWrite(pin_a_, LOW);
    digitalWrite(pin_b_, LOW);
    digitalWrite(pin_c_, LOW);
    digitalWrite(pin_d_, LOW);
  }

  void setLimits(float min_deg, float max_deg) {
    min_deg_ = min_deg;
    max_deg_ = max_deg;
  }

  void setSpeedUs(uint16_t step_interval_us) {
    step_interval_us_ = step_interval_us;
  }

  bool pointToDeg(float deg) {
    if (deg < min_deg_) {
      deg = min_deg_;
    }
    if (deg > max_deg_) {
      deg = max_deg_;
    }
    target_deg_ = deg;
    target_step_ = degToStep(target_deg_);
    moving_ = (target_step_ != current_step_);
    if (moving_) {
      mute_until_ms_ = millis() + 300U;
    }
    return moving_;
  }

  void update(void) {
    if (!moving_) {
      return;
    }

    const uint32_t now_us = micros();
    if ((now_us - last_step_us_) < step_interval_us_) {
      return;
    }
    last_step_us_ = now_us;

    int8_t dir = 0;
    if (target_step_ > current_step_) {
      dir = 1;
    } else if (target_step_ < current_step_) {
      dir = -1;
    }

    if (dir == 0) {
      moving_ = false;
      move_end_ms_ = millis();
      mute_until_ms_ = move_end_ms_ + 300U;
      deenergizeIfStepDir();
      return;
    }

    step(dir);
    current_step_ += dir;
    current_deg_ = stepToDeg(current_step_);
  }

  bool isMoving(void) const { return moving_; }

  bool isMutedForSensors(void) const {
    return moving_ || (millis() < mute_until_ms_);
  }

  float currentDeg(void) const { return current_deg_; }

 private:
  StepperProfile profile_;
  uint8_t pin_a_;
  uint8_t pin_b_;
  uint8_t pin_c_;
  uint8_t pin_d_;
  float current_deg_;
  float target_deg_;
  float min_deg_;
  float max_deg_;
  uint16_t steps_per_rev_;
  uint8_t microstep_;
  int32_t current_step_;
  int32_t target_step_;
  bool moving_;
  uint32_t move_end_ms_;
  uint32_t mute_until_ms_;
  uint16_t step_interval_us_;
  uint32_t last_step_us_;

  int32_t degToStep(float deg) const {
    const float steps_per_360 = static_cast<float>(steps_per_rev_) * static_cast<float>(microstep_);
    return static_cast<int32_t>((deg / 360.0F) * steps_per_360);
  }

  float stepToDeg(int32_t step) const {
    const float steps_per_360 = static_cast<float>(steps_per_rev_) * static_cast<float>(microstep_);
    return (static_cast<float>(step) * 360.0F) / steps_per_360;
  }

  void step(int8_t dir) {
    if (profile_ == StepperProfile::STEP_DIR) {
      digitalWrite(pin_b_, (dir > 0) ? HIGH : LOW);
      digitalWrite(pin_c_, LOW); // EN active low
      digitalWrite(pin_a_, HIGH);
      delayMicroseconds(4U);
      digitalWrite(pin_a_, LOW);
      return;
    }

    static const uint8_t seq[8][4] = {
      {1U, 0U, 0U, 0U}, {1U, 1U, 0U, 0U}, {0U, 1U, 0U, 0U}, {0U, 1U, 1U, 0U},
      {0U, 0U, 1U, 0U}, {0U, 0U, 1U, 1U}, {0U, 0U, 0U, 1U}, {1U, 0U, 0U, 1U}
    };
    static int8_t idx = 0;
    idx += dir;
    if (idx > 7) {
      idx = 0;
    }
    if (idx < 0) {
      idx = 7;
    }

    digitalWrite(pin_a_, seq[idx][0] ? HIGH : LOW);
    digitalWrite(pin_b_, seq[idx][1] ? HIGH : LOW);
    digitalWrite(pin_c_, seq[idx][2] ? HIGH : LOW);
    digitalWrite(pin_d_, seq[idx][3] ? HIGH : LOW);
  }

  void deenergizeIfStepDir(void) {
    if (profile_ == StepperProfile::STEP_DIR) {
      digitalWrite(pin_c_, HIGH);
    }
  }
};
