/*
 * MCU Main Sketch: Audio-Localizing AI Monitor
 * Arduino STM32U585 via Arduino App Lab
 * 
 * Responsibilities:
 * - Continuous ADC sampling of 3 audio sensors
 * - Trigger detection + bearing estimation
 * - Stepper motor control (turret pointing)
 * - LCD + LED display, button handling
 * - RPC communication with Linux side
 */

#include "config.h"
#include "sensors.h"
#include "turret.h"
#include "display.h"
#include "rpc_bridge.h"

#include <Wire.h>
#include <LiquidCrystal_I2C.h>  // or adjust for parallel mode

// ============================================================================
// GLOBALS & STATE
// ============================================================================

// Timer interrupt for ADC sampling
hw_timer_t* adcTimer = NULL;
volatile bool adcSampleFlag = false;

// Button debouncing
volatile uint32_t lastButtonPress[2] = {0, 0};
const uint32_t DEBOUNCE_MS = 20;

// System state
bool armed = true;
bool motionInProgress = false;
uint32_t motionStartTime = 0;

// ============================================================================
// ISR: ADC TIMER (1 kHz)
// ============================================================================
void IRAM_ATTR timerISR() {
  adcSampleFlag = true;
}

// ============================================================================
// ISR: BUTTON HANDLERS
// ============================================================================
void IRAM_ATTR btnArmISR() {
  uint32_t now = millis();
  if (now - lastButtonPress[0] > DEBOUNCE_MS) {
    armed = !armed;
    lastButtonPress[0] = now;
  }
}

void IRAM_ATTR btnResetISR() {
  uint32_t now = millis();
  if (now - lastButtonPress[1] > DEBOUNCE_MS) {
    turret.home();
    display.lcdClear();
    display.lcdLine1("RESET");
    lastButtonPress[1] = now;
  }
}

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  Serial.begin(RPC_BAUDRATE);
  
  if (SERIAL_DEBUG) {
    Serial.println("=== Audio-Localizing AI Monitor ===");
    Serial.println("MCU Startup...");
  }
  
  // Initialize modules
  display.setup();
  sensors.setup();
  turret.setup();
  rpcBridge.setup(RPC_BAUDRATE);
  
  // Button setup
  pinMode(BTN_ARM_STANDBY, INPUT_PULLUP);
  pinMode(BTN_RESET, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BTN_ARM_STANDBY), btnArmISR, FALLING);
  attachInterrupt(digitalPinToInterrupt(BTN_RESET), btnResetISR, FALLING);
  
  // ADC Timer: 1 kHz interrupt
  // Note: exact implementation depends on STM32U585 HAL; this is placeholder
  adcTimer = timerBegin(0, 80, true);  // timer 0, prescaler 80 (for 1MHz clock = 1MHz/80 = 12.5kHz)
  timerAttachInterrupt(adcTimer, &timerISR, true);
  timerAlarmWrite(adcTimer, 1000, true);  // 1000 ticks = 1 kHz
  timerAlarmEnable(adcTimer);
  
  // Initial display
  turret.home();
  display.setLEDState(LED_IDLE);
  display.lcdLine1("Ready");
  display.lcdLine2("Listening...");
  
  if (SERIAL_DEBUG) {
    Serial.println("Setup complete.");
  }
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
  // ADC sampling interrupt handler (1 kHz)
  if (adcSampleFlag) {
    adcSampleFlag = false;
    
    // Sample all 3 channels
    for (int i = 0; i < MIC_CHANNELS; i++) {
      uint16_t sample = analogRead(sensorPins[i]);
      // (Implementation detail: update circular buffer in sensors module)
      // This would call sensors.recordSample(i, sample) or similar
    }
  }
  
  // Stepper motor tick (smooth ramping)
  turret.tick();
  
  // LED blink animation
  display.tick();
  
  // Check for audio trigger
  if (armed) {
    float bearing;
    uint16_t peaks[3];
    uint32_t timestamp;
    
    if (sensors.checkTrigger(bearing, peaks, timestamp)) {
      if (SERIAL_DEBUG) {
        Serial.print("TRIGGER: bearing=");
        Serial.print(bearing);
        Serial.print("° amps=");
        Serial.print(peaks[0]); Serial.print(",");
        Serial.print(peaks[1]); Serial.print(",");
        Serial.println(peaks[2]);
      }
      
      // Publish to Linux
      rpcBridge.publishEvent(bearing, peaks, timestamp);
      
      // Local UI feedback
      display.setLEDState(LED_EVENT);
      display.lcdLine1("Event detected!");
      display.lcdLine2("Bearing: ");
      
      // Mute trigger during motion
      motionInProgress = true;
      motionStartTime = millis();
    }
  }
  
  // Clear motion mute flag after delay
  if (motionInProgress && (millis() - motionStartTime > TRIGGER_MUTE_DURING_MOTION_MS)) {
    motionInProgress = false;
  }
  
  // Process RPC commands from Linux
  rpcBridge.process();
  
  // Small delay to prevent watchdog reset
  delay(1);
}

// ============================================================================
// HELPER: Map sensor pins array (used in ISR context)
// ============================================================================
const uint8_t sensorPins[MIC_CHANNELS] = {MIC_PIN_0, MIC_PIN_1, MIC_PIN_2};
