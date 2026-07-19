#pragma once

#include <Arduino.h>
#include <LiquidCrystal.h>
#include <LiquidCrystal_I2C.h>

enum class LedLevel : uint8_t {
  IDLE = 0U,
  EVENT = 1U,
  ALERT = 2U,
  ALARM = 3U,
};

class DisplayAndIndicators {
 public:
  DisplayAndIndicators(bool use_i2c,
                       uint8_t red1, uint8_t red2,
                       uint8_t blue1, uint8_t blue2,
                       uint8_t lcd_rs, uint8_t lcd_en, uint8_t lcd_d4,
                       uint8_t lcd_d5, uint8_t lcd_d6, uint8_t lcd_d7)
      : use_i2c_(use_i2c),
        red1_(red1), red2_(red2), blue1_(blue1), blue2_(blue2),
        lcd_parallel_(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7),
        lcd_i2c_(0x27, 16, 2), last_blink_ms_(0U), blink_state_(false) {}

  void begin(void) {
    pinMode(red1_, OUTPUT);
    pinMode(red2_, OUTPUT);
    pinMode(blue1_, OUTPUT);
    pinMode(blue2_, OUTPUT);
    setLed(LedLevel::IDLE);

    if (use_i2c_) {
      lcd_i2c_.init();
      lcd_i2c_.backlight();
      lcd_i2c_.clear();
    } else {
      lcd_parallel_.begin(16, 2);
      lcd_parallel_.clear();
    }
  }

  void setLed(LedLevel level) {
    level_ = level;
    applyLedNow();
  }

  void lcdText(const String& line1, const String& line2) {
    if (use_i2c_) {
      lcd_i2c_.clear();
      lcd_i2c_.setCursor(0, 0);
      lcd_i2c_.print(line1.substring(0, 16));
      lcd_i2c_.setCursor(0, 1);
      lcd_i2c_.print(line2.substring(0, 16));
    } else {
      lcd_parallel_.clear();
      lcd_parallel_.setCursor(0, 0);
      lcd_parallel_.print(line1.substring(0, 16));
      lcd_parallel_.setCursor(0, 1);
      lcd_parallel_.print(line2.substring(0, 16));
    }
  }

  void update(void) {
    const uint32_t now = millis();
    if ((level_ == LedLevel::ALERT) || (level_ == LedLevel::ALARM)) {
      const uint16_t period = (level_ == LedLevel::ALARM) ? 120U : 260U;
      if ((now - last_blink_ms_) > period) {
        last_blink_ms_ = now;
        blink_state_ = !blink_state_;
        applyLedNow();
      }
    }
  }

 private:
  bool use_i2c_;
  uint8_t red1_;
  uint8_t red2_;
  uint8_t blue1_;
  uint8_t blue2_;
  LiquidCrystal lcd_parallel_;
  LiquidCrystal_I2C lcd_i2c_;
  LedLevel level_ = LedLevel::IDLE;
  uint32_t last_blink_ms_;
  bool blink_state_;

  void applyLedNow(void) {
    switch (level_) {
      case LedLevel::IDLE:
        digitalWrite(red1_, LOW);
        digitalWrite(red2_, LOW);
        digitalWrite(blue1_, HIGH);
        digitalWrite(blue2_, LOW);
        break;
      case LedLevel::EVENT:
        digitalWrite(red1_, LOW);
        digitalWrite(red2_, LOW);
        digitalWrite(blue1_, HIGH);
        digitalWrite(blue2_, HIGH);
        break;
      case LedLevel::ALERT:
      case LedLevel::ALARM:
        digitalWrite(red1_, blink_state_ ? HIGH : LOW);
        digitalWrite(red2_, blink_state_ ? HIGH : LOW);
        digitalWrite(blue1_, LOW);
        digitalWrite(blue2_, LOW);
        break;
      default:
        break;
    }
  }
};
