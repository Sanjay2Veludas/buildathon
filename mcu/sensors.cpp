/*
 * Sensor Module: Implementation
 */

#include "sensors.h"

SensorModule sensors;

SensorModule::SensorModule() 
  : triggered(false), triggerTime(0), thresholdOffset(TRIGGER_THRESHOLD_OFFSET) {
  for (int i = 0; i < MIC_CHANNELS; i++) {
    channels[i].bufferIndex = 0;
    channels[i].baseline = 512;  // mid-range ADC
    channels[i].peakRecent = 0;
    channels[i].triggered = false;
  }
}

void SensorModule::setup() {
  for (int i = 0; i < MIC_CHANNELS; i++) {
    pinMode(sensorPins[i], INPUT);
  }
  resetBaseline();
}

void SensorModule::adcInterrupt() {
  // Called from ISR at ~1 kHz
  for (int i = 0; i < MIC_CHANNELS; i++) {
    uint16_t sample = analogRead(sensorPins[i]);
    channels[i].adcBuffer[channels[i].bufferIndex] = sample;
    channels[i].bufferIndex = (channels[i].bufferIndex + 1) % ADC_BUFFER_SIZE;
    
    // Track peak in recent window
    if (sample > channels[i].peakRecent) {
      channels[i].peakRecent = sample;
    }
  }
  
  // Update baseline every ~BASELINE_WINDOW_MS
  static uint32_t lastBaselineUpdate = 0;
  if (millis() - lastBaselineUpdate > BASELINE_WINDOW_MS) {
    for (int i = 0; i < MIC_CHANNELS; i++) {
      updateBaseline(i);
    }
    lastBaselineUpdate = millis();
  }
}

void SensorModule::updateBaseline(uint8_t ch) {
  // Simple low-pass filter on baseline
  uint32_t sum = 0;
  for (int i = 0; i < ADC_BUFFER_SIZE; i++) {
    sum += channels[ch].adcBuffer[i];
  }
  uint16_t mean = sum / ADC_BUFFER_SIZE;
  channels[ch].baseline = (channels[ch].baseline * 3 + mean) / 4;  // IIR filter
}

bool SensorModule::checkTrigger(float& bearing, uint16_t peaks[3], uint32_t& timestamp) {
  if (triggered) {
    // Already in event window; capture peaks
    if (millis() - triggerTime < EVENT_CAPTURE_WINDOW_MS) {
      return false;  // Still capturing
    } else {
      // Event window closed; report final result
      for (int i = 0; i < MIC_CHANNELS; i++) {
        peaks[i] = channels[i].peakRecent;
      }
      bearing = estimateBearing();
      timestamp = triggerTime;
      
      triggered = false;
      return true;
    }
  }
  
  // Check for new trigger
  for (int i = 0; i < MIC_CHANNELS; i++) {
    if (channels[i].peakRecent > (channels[i].baseline + thresholdOffset)) {
      // Trigger detected
      triggered = true;
      triggerTime = millis();
      captureWindowStartTime = millis();
      
      // Reset peaks for next window
      for (int j = 0; j < MIC_CHANNELS; j++) {
        channels[j].peakRecent = channels[j].baseline;
      }
      
      return false;  // Event capture in progress, call again later
    }
  }
  
  return false;
}

float SensorModule::estimateBearing() {
  // Find two loudest channels
  uint16_t peaks[3] = {channels[0].peakRecent, channels[1].peakRecent, channels[2].peakRecent};
  
  uint8_t max1_idx = 0, max2_idx = 1;
  if (peaks[1] > peaks[max1_idx]) max1_idx = 1;
  if (peaks[2] > peaks[max1_idx]) { max2_idx = max1_idx; max1_idx = 2; }
  else if (peaks[2] > peaks[max2_idx]) max2_idx = 2;
  
  float b1 = sensorBearings[max1_idx];
  float b2 = sensorBearings[max2_idx];
  uint16_t amp1 = peaks[max1_idx];
  uint16_t amp2 = peaks[max2_idx];
  
  return interpBearing(b1, b2, amp1, amp2);
}

float SensorModule::interpBearing(float b1, float b2, uint16_t amp1, uint16_t amp2) {
  // Weighted average of the two loudest sensors
  if (amp1 + amp2 == 0) return 0.0;
  
  float result = (b1 * amp1 + b2 * amp2) / (amp1 + amp2);
  
  // Normalize to [-180, 180]
  while (result > 180.0) result -= 360.0;
  while (result < -180.0) result += 360.0;
  
  return result;
}

void SensorModule::resetBaseline() {
  for (int i = 0; i < MIC_CHANNELS; i++) {
    channels[i].baseline = 512;
    channels[i].peakRecent = 0;
  }
}
