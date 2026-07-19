/*
 * Turret Module: Stepper motor control with acceleration ramping
 */

#ifndef TURRET_H
#define TURRET_H

#include "config.h"

class TurretModule {
public:
  TurretModule();
  void setup();
  
  // Point turret to absolute angle (deg), with acceleration ramp
  void pointTo(float deg);
  
  // Stepper tick (call from main loop ISR, ~kHz rate)
  void tick();
  
  // Queries
  bool isMoving() const { return moving; }
  float getCurrentAngle() const { return currentDegrees; }
  float getTargetAngle() const { return targetDegrees; }
  
  // Emergency stop
  void stop() { targetDegrees = currentDegrees; }
  
  // Home the turret (assumes current position is 0°)
  void home() { currentDegrees = 0.0f; targetDegrees = 0.0f; }
  
private:
  float currentDegrees;
  float targetDegrees;
  bool moving;
  
  // Acceleration ramp state
  float stepFreq;         // current step frequency (steps/sec)
  float maxStepFreq;      // max frequency based on MAX_RPM
  float accelRate;        // steps/sec^2
  uint32_t lastTickTime;  // microseconds
  
  // Stepper coil sequence (for ULN2003 / 28BYJ-48)
  uint8_t coilPattern[8] = {
    0b1000,  // IN1 only
    0b1100,  // IN1 + IN2
    0b0100,  // IN2 only
    0b0110,  // IN2 + IN3
    0b0010,  // IN3 only
    0b0011,  // IN3 + IN4
    0b0001,  // IN4 only
    0b1001   // IN4 + IN1
  };
  uint8_t coilIndex;
  
  void setCoil(uint8_t pattern);
  void stepCW();    // clockwise
  void stepCCW();   // counter-clockwise
};

extern TurretModule turret;

#endif // TURRET_H
