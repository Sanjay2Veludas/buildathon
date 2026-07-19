/*
 * Turret Module: Implementation
 */

#include "turret.h"

TurretModule turret;

TurretModule::TurretModule()
  : currentDegrees(0.0), targetDegrees(0.0), moving(false), 
    stepFreq(0.0), coilIndex(0), lastTickTime(0) {
  maxStepFreq = (STEPPER_MAX_RPM / 60.0) * STEPPER_STEPS_PER_REV;
  accelRate = STEPPER_ACCEL_STEPS_PER_SEC_SQ;
}

void TurretModule::setup() {
  pinMode(STEPPER_PIN_IN1, OUTPUT);
  pinMode(STEPPER_PIN_IN2, OUTPUT);
  pinMode(STEPPER_PIN_IN3, OUTPUT);
  pinMode(STEPPER_PIN_IN4, OUTPUT);
  
  setCoil(0);
  home();
}

void TurretModule::pointTo(float deg) {
  // Clamp to turret limits
  if (deg > STEPPER_MAX_DEG) deg = STEPPER_MAX_DEG;
  if (deg < STEPPER_MIN_DEG) deg = STEPPER_MIN_DEG;
  
  targetDegrees = deg;
  
  if (fabs(targetDegrees - currentDegrees) > 0.5) {
    moving = true;
    stepFreq = 1.0;  // Start slow
    lastTickTime = micros();
  }
}

void TurretModule::tick() {
  if (!moving) return;
  
  uint32_t now = micros();
  float dtSec = (now - lastTickTime) / 1e6;
  lastTickTime = now;
  
  // Acceleration ramp
  float distDeg = targetDegrees - currentDegrees;
  float distSteps = distDeg / STEPPER_DEGREES_PER_STEP;
  
  if (distSteps != 0) {
    // Accelerate up to max speed
    if (stepFreq < maxStepFreq) {
      stepFreq += accelRate * dtSec;
      if (stepFreq > maxStepFreq) stepFreq = maxStepFreq;
    }
    
    // Decelerate as we approach target
    float stepsToDecel = (stepFreq * stepFreq) / (2.0 * accelRate);
    if (fabs(distSteps) < stepsToDecel) {
      stepFreq -= accelRate * dtSec;
      if (stepFreq < 1.0) stepFreq = 1.0;
    }
    
    // Step if enough time has passed
    float secondsPerStep = 1.0 / stepFreq;
    static float stepAccum = 0;
    stepAccum += dtSec / secondsPerStep;
    
    if (stepAccum >= 1.0) {
      stepAccum -= 1.0;
      
      if (distSteps > 0) {
        stepCW();
      } else {
        stepCCW();
      }
    }
  } else {
    moving = false;
    stepFreq = 0.0;
  }
}

void TurretModule::stepCW() {
  coilIndex = (coilIndex + 1) % 8;
  setCoil(coilPattern[coilIndex]);
  currentDegrees += STEPPER_DEGREES_PER_STEP;
}

void TurretModule::stepCCW() {
  coilIndex = (coilIndex + 7) % 8;  // -1 mod 8 = 7
  setCoil(coilPattern[coilIndex]);
  currentDegrees -= STEPPER_DEGREES_PER_STEP;
}

void TurretModule::setCoil(uint8_t pattern) {
  digitalWrite(STEPPER_PIN_IN1, (pattern >> 3) & 1);
  digitalWrite(STEPPER_PIN_IN2, (pattern >> 2) & 1);
  digitalWrite(STEPPER_PIN_IN3, (pattern >> 1) & 1);
  digitalWrite(STEPPER_PIN_IN4, (pattern >> 0) & 1);
}
