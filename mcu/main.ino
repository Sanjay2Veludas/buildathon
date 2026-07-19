#include <Arduino.h>

#include "display.h"
#include "sensors.h"
#include "turret.h"

// Pin configuration (matches wiring plan).
static const uint8_t PIN_S0 = A0;
static const uint8_t PIN_S1 = A1;
static const uint8_t PIN_S2 = A2;

static const uint8_t PIN_STEP_OR_IN1 = 2U;
static const uint8_t PIN_DIR_OR_IN2 = 3U;
static const uint8_t PIN_EN_OR_IN3 = 4U;
static const uint8_t PIN_IN4 = 5U;

static const uint8_t PIN_RED1 = 6U;
static const uint8_t PIN_RED2 = 7U;
static const uint8_t PIN_BLUE1 = 8U;
static const uint8_t PIN_BLUE2 = 9U;

static const uint8_t PIN_BTN_ARM = 10U;
static const uint8_t PIN_BTN_RESET = 11U;

static const bool LCD_USE_I2C = true;
static const bool STEPPER_USE_STEP_DIR = false;  // 28BYJ-48 + ULN2003

SoundSensors g_sensors(PIN_S0, PIN_S1, PIN_S2);
Turret g_turret(STEPPER_USE_STEP_DIR ? StepperProfile::STEP_DIR : StepperProfile::ULN2003,
                PIN_STEP_OR_IN1, PIN_DIR_OR_IN2, PIN_EN_OR_IN3, PIN_IN4);
DisplayAndIndicators g_display(LCD_USE_I2C,
                               PIN_RED1, PIN_RED2, PIN_BLUE1, PIN_BLUE2,
                               12U, 13U, 14U, 15U, 16U, 17U);

static bool g_armed = true;
static bool g_last_moving = false;
static uint32_t g_last_button_ms = 0U;
static uint32_t g_event_count = 0UL;

static bool g_btn_arm_prev = true;
static bool g_btn_reset_prev = true;

static void publishEvent(const SoundEvent& evt) {
  Serial.print("{\"type\":\"event\",\"bearing_deg\":");
  Serial.print(evt.bearing_deg, 2);
  Serial.print(",\"a0\":");
  Serial.print(evt.amplitudes[0]);
  Serial.print(",\"a1\":");
  Serial.print(evt.amplitudes[1]);
  Serial.print(",\"a2\":");
  Serial.print(evt.amplitudes[2]);
  Serial.print(",\"ts\":");
  Serial.print(evt.timestamp_ms);
  Serial.println("}");
}

static void publishAck(const char* cmd, bool ok) {
  Serial.print("{\"type\":\"ack\",\"cmd\":\"");
  Serial.print(cmd);
  Serial.print("\",\"ok\":");
  Serial.print(ok ? "true" : "false");
  Serial.println("}");
}

static void trimInPlace(String& s) {
  s.trim();
}

static float parseFloatArg(const String& cmd, const String& key, float fallback) {
  const int32_t idx = cmd.indexOf(key + "=");
  if (idx < 0) {
    return fallback;
  }
  const int32_t start = idx + key.length() + 1;
  int32_t end = cmd.indexOf(' ', start);
  if (end < 0) {
    end = cmd.length();
  }
  return cmd.substring(start, end).toFloat();
}

static int32_t parseIntArg(const String& cmd, const String& key, int32_t fallback) {
  const int32_t idx = cmd.indexOf(key + "=");
  if (idx < 0) {
    return fallback;
  }
  const int32_t start = idx + key.length() + 1;
  int32_t end = cmd.indexOf(' ', start);
  if (end < 0) {
    end = cmd.length();
  }
  return cmd.substring(start, end).toInt();
}

static String parseStrArg(const String& cmd, const String& key, const String& fallback) {
  const int32_t idx = cmd.indexOf(key + "=");
  if (idx < 0) {
    return fallback;
  }
  int32_t start = idx + key.length() + 1;
  if ((start < cmd.length()) && (cmd[start] == '"')) {
    start++;
    const int32_t endq = cmd.indexOf('"', start);
    if (endq > start) {
      return cmd.substring(start, endq);
    }
  }
  int32_t end = cmd.indexOf(' ', start);
  if (end < 0) {
    end = cmd.length();
  }
  return cmd.substring(start, end);
}

static void handleCommand(const String& input) {
  String cmd = input;
  trimInPlace(cmd);

  if (cmd.startsWith("point_turret")) {
    float deg = parseFloatArg(cmd, "deg", 0.0F);
    bool moving = g_turret.pointToDeg(deg);
    publishAck("point_turret", true);
    if (!moving) {
      Serial.println("{\"type\":\"motion_complete\"}");
    }
    return;
  }

  if (cmd.startsWith("set_led")) {
    int32_t level = parseIntArg(cmd, "level", 0);
    if (level <= 0) {
      g_display.setLed(LedLevel::IDLE);
    } else if (level == 1) {
      g_display.setLed(LedLevel::EVENT);
    } else if (level == 2) {
      g_display.setLed(LedLevel::ALERT);
    } else {
      g_display.setLed(LedLevel::ALARM);
    }
    publishAck("set_led", true);
    return;
  }

  if (cmd.startsWith("lcd_text")) {
    const String l1 = parseStrArg(cmd, "l1", "");
    const String l2 = parseStrArg(cmd, "l2", "");
    g_display.lcdText(l1, l2);
    publishAck("lcd_text", true);
    return;
  }

  if (cmd.startsWith("set_armed")) {
    const int32_t armed = parseIntArg(cmd, "armed", 1);
    g_armed = (armed != 0);
    publishAck("set_armed", true);
    return;
  }

  if (cmd.startsWith("set_threshold")) {
    const int32_t th = parseIntArg(cmd, "value", 120);
    g_sensors.setTriggerThreshold(static_cast<uint16_t>(th));
    publishAck("set_threshold", true);
    return;
  }

  if (cmd.startsWith("set_7seg")) {
    publishAck("set_7seg", true);
    return;
  }

  if (cmd.startsWith("ping")) {
    Serial.println("{\"type\":\"pong\"}");
    return;
  }

  publishAck("unknown", false);
}

void setup() {
  Serial.begin(115200U);

  pinMode(PIN_BTN_ARM, INPUT_PULLUP);
  pinMode(PIN_BTN_RESET, INPUT_PULLUP);

  g_display.begin();
  g_display.lcdText("Booting...", "Online mode");
  g_display.setLed(LedLevel::IDLE);

  g_turret.begin();
  g_turret.setLimits(-180.0F, 180.0F);
  g_turret.setSpeedUs(2000U);  // 2ms/half-step — safe for 28BYJ-48 under load

  g_sensors.begin();
  g_sensors.setTriggerThreshold(120U);
  g_sensors.setRefractoryMs(600U);

  Serial.println("{\"type\":\"boot\",\"ok\":true}");
}

void loop() {
  g_turret.update();
  g_display.update();

  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    handleCommand(line);
  }

  if (g_last_moving && !g_turret.isMoving()) {
    Serial.println("{\"type\":\"motion_complete\"}");
  }
  g_last_moving = g_turret.isMoving();

  const uint32_t now = millis();
  if ((now - g_last_button_ms) > 30U) {
    g_last_button_ms = now;
    const bool btn_arm = (digitalRead(PIN_BTN_ARM) != LOW);
    const bool btn_rst = (digitalRead(PIN_BTN_RESET) != LOW);

    if (g_btn_arm_prev && !btn_arm) {
      g_armed = !g_armed;
      Serial.print("{\"type\":\"armed\",\"value\":");
      Serial.print(g_armed ? "true" : "false");
      Serial.println("}");
    }

    if (g_btn_reset_prev && !btn_rst) {
      g_event_count = 0UL;
      g_display.lcdText("Reset", "Counter=0");
      Serial.println("{\"type\":\"reset\"}");
    }

    g_btn_arm_prev = btn_arm;
    g_btn_reset_prev = btn_rst;
  }

  if (g_armed) {
    SoundEvent evt;
    if (g_sensors.update(g_turret.isMutedForSensors(), &evt)) {
      g_event_count++;
      g_display.setLed(LedLevel::EVENT);
      g_display.lcdText("Sound detected", "Publishing...");
      publishEvent(evt);
    }
  }
}
