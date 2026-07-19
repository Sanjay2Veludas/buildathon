/*
 * Display Module: LCD + LEDs + 7-segment (optional)
 */

#ifndef DISPLAY_H
#define DISPLAY_H

#include "config.h"

enum LEDState {
  LED_IDLE,      // Blue
  LED_EVENT,     // Blue + brief pulse
  LED_ALERT,     // Red blink
  LED_ALARM      // Red fast blink
};

class DisplayModule {
public:
  DisplayModule();
  void setup();
  
  // LCD text
  void lcdLine1(const char* text);
  void lcdLine2(const char* text);
  void lcdClear();
  
  // LED state
  void setLEDState(LEDState state);
  void tick();  // Call from main loop for blink patterns
  
  // 7-segment display (if enabled)
  void show7Seg(uint8_t digit);  // 0-9 or 0xF for blank
  
private:
  LEDState currentLEDState;
  uint32_t lastBlinkTime;
  bool blinkOn;
  
  void updateLEDs();
};

extern DisplayModule display;

#endif // DISPLAY_H
