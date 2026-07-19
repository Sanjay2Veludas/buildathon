/*
 * MCU Configuration Constants
 * Edit these to match your hardware + calibration
 */

#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// SENSOR CONFIGURATION
// ============================================================================
#define MIC_CHANNELS 3
#define MIC_PIN_0 A0      // Bearing 0°
#define MIC_PIN_1 A1      // Bearing 120°
#define MIC_PIN_2 A2      // Bearing 240°

#define MIC_BEARING_0   0.0
#define MIC_BEARING_1   120.0
#define MIC_BEARING_2   240.0

// ADC sampling: ~1 kHz per channel via timer interrupt
#define ADC_SAMPLE_FREQ_HZ 1000
#define ADC_BUFFER_SIZE    1024     // circular buffer per channel
#define BASELINE_WINDOW_MS 500      // rolling baseline period

// Trigger threshold: amplitude_peak > (baseline + THRESHOLD_OFFSET)
// Runtime tunable via RPC, but seed value here
#define TRIGGER_THRESHOLD_OFFSET 100   // ADC units above baseline

// Event capture window after trigger
#define EVENT_CAPTURE_WINDOW_MS 100
#define TRIGGER_MUTE_DURING_MOTION_MS 500

// ============================================================================
// STEPPER MOTOR CONFIGURATION
// ============================================================================
#define STEPPER_DRIVER_TYPE "ULN2003"  // or "DRV8825" for future support

// ULN2003 28BYJ-48 stepper (5V, 4-phase coil, ~2048 steps/rev)
#define STEPPER_PIN_IN1 6   // IN1
#define STEPPER_PIN_IN2 7   // IN2
#define STEPPER_PIN_IN3 8   // IN3
#define STEPPER_PIN_IN4 9   // IN4

#define STEPPER_STEPS_PER_REV 2048
#define STEPPER_DEGREES_PER_STEP (360.0 / STEPPER_STEPS_PER_REV)
#define STEPPER_MAX_RPM 12
#define STEPPER_ACCEL_STEPS_PER_SEC_SQ 20000  // ramp time

// Turret limits: ±180° from center (webcam cable constraint)
#define STEPPER_HOME_DEG 0.0
#define STEPPER_MIN_DEG -180.0
#define STEPPER_MAX_DEG  180.0

// ============================================================================
// DISPLAY & I/O
// ============================================================================
// LCD 16x2 via I2C (addr 0x27 typical) or parallel (set LCD_I2C to 0 for parallel)
#define LCD_I2C 1
#define LCD_I2C_ADDR 0x27
#define LCD_COLS 16
#define LCD_ROWS 2

// Parallel mode (if LCD_I2C = 0): RS, EN, D4-D7 pins
#define LCD_RS   12
#define LCD_EN   11
#define LCD_D4   5
#define LCD_D5   4
#define LCD_D6   3
#define LCD_D7   2

// LEDs
#define LED_BLUE_1  10
#define LED_BLUE_2  A3
#define LED_RED_1   A4
#define LED_RED_2   A5

// Buttons
#define BTN_ARM_STANDBY  13
#define BTN_RESET        A6

// 7-segment display (optional)
#define SEVENSEG_ENABLED 0
#define SEVENSEG_PINS { 0, 0, 0, 0, 0, 0, 0, 0 }  // {a,b,c,d,e,f,g,dp}

// ============================================================================
// RPC & COMMUNICATION
// ============================================================================
#define RPC_BAUDRATE 115200
#define RPC_HEARTBEAT_INTERVAL_MS 1000

// ============================================================================
// OPERATIONAL FLAGS
// ============================================================================
#define DEMO_MODE 1                    // 1 = lower thresholds, faster timeouts
#define SERIAL_DEBUG 1                 // 1 = debug prints to Serial
#define MOTION_DURING_CAPTURE 1        // 1 = allow camera capture during turret motion

#endif // CONFIG_H
