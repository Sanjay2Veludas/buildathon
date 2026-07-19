/*
 * Sensor Module: 3-channel audio sensor acquisition + bearing estimation
 */

#ifndef SENSORS_H
#define SENSORS_H

#include "config.h"

// Circular buffer for rolling baseline + peak detection
struct SensorChannel {
  uint16_t adcBuffer[ADC_BUFFER_SIZE];
  uint16_t bufferIndex;
  uint16_t baseline;
  uint16_t peakRecent;  // peak in last event window
  bool triggered;
};

class SensorModule {
public:
  SensorModule();
  void setup();
  void adcInterrupt();  // Called from ISR at ~1 kHz
  
  // Poll for trigger; returns true + populates bearing if event detected
  bool checkTrigger(float& bearing, uint16_t peaks[3], uint32_t& timestamp);
  
  // Runtime config
  void setThreshold(uint16_t offset) { thresholdOffset = offset; }
  void resetBaseline();
  
  // Query state
  uint16_t getBaseline(uint8_t ch) { return channels[ch].baseline; }
  uint16_t getPeak(uint8_t ch)     { return channels[ch].peakRecent; }
  bool isTriggered()               { return triggered; }
  
private:
  SensorChannel channels[MIC_CHANNELS];
  uint8_t sensorPins[MIC_CHANNELS] = {MIC_PIN_0, MIC_PIN_1, MIC_PIN_2};
  float sensorBearings[MIC_CHANNELS] = {MIC_BEARING_0, MIC_BEARING_1, MIC_BEARING_2};
  
  uint16_t thresholdOffset;
  bool triggered;
  uint32_t triggerTime;
  uint32_t captureWindowStartTime;
  
  void updateBaseline(uint8_t ch);
  float estimateBearing();
  float interpBearing(float b1, float b2, uint16_t amp1, uint16_t amp2);
};

// Global instance + ISR handler
extern SensorModule sensors;
void timerISR();

#endif // SENSORS_H
