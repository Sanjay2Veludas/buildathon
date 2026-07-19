/*
 * Display Module: Implementation
 */

#include "display.h"

DisplayModule display;

// LCD instance (adjust based on LCD_I2C flag)
#if LCD_I2C
  LiquidCrystal_I2C lcd(LCD_I2C_ADDR, LCD_COLS, LCD_ROWS);
#else
  // Placeholder for parallel mode; would use LiquidCrystal instead
  // LiquidCrystal lcd(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7);
#endif

DisplayModule::DisplayModule() 
  : currentLEDState(LED_IDLE), lastBlinkTime(0), blinkOn(true) {
}

void DisplayModule::setup() {
#if LCD_I2C
  lcd.init();
  lcd.backlight();
#else
  // Parallel mode setup
  // lcd.begin(LCD_COLS, LCD_ROWS);
#endif
  
  pinMode(LED_BLUE_1, OUTPUT);
  pinMode(LED_BLUE_2, OUTPUT);
  pinMode(LED_RED_1, OUTPUT);
  pinMode(LED_RED_2, OUTPUT);
  
  if (SEVENSEG_ENABLED) {
    // Initialize 7-segment pins
    // for (int i = 0; i < 8; i++) pinMode(SEVENSEG_PINS[i], OUTPUT);
  }
  
  updateLEDs();
}

void DisplayModule::lcdLine1(const char* text) {
  lcd.setCursor(0, 0);
  lcd.print("                ");  // Clear line
  lcd.setCursor(0, 0);
  lcd.print(text);
}

void DisplayModule::lcdLine2(const char* text) {
  lcd.setCursor(0, 1);
  lcd.print("                ");  // Clear line
  lcd.setCursor(0, 1);
  lcd.print(text);
}

void DisplayModule::lcdClear() {
  lcd.clear();
}

void DisplayModule::setLEDState(LEDState state) {
  currentLEDState = state;
  updateLEDs();
}

void DisplayModule::updateLEDs() {
  // Turn off all LEDs
  digitalWrite(LED_BLUE_1, LOW);
  digitalWrite(LED_BLUE_2, LOW);
  digitalWrite(LED_RED_1, LOW);
  digitalWrite(LED_RED_2, LOW);
  
  switch (currentLEDState) {
    case LED_IDLE:
      digitalWrite(LED_BLUE_1, HIGH);
      digitalWrite(LED_BLUE_2, HIGH);
      break;
    case LED_EVENT:
      digitalWrite(LED_BLUE_1, blinkOn ? HIGH : LOW);
      digitalWrite(LED_BLUE_2, blinkOn ? HIGH : LOW);
      break;
    case LED_ALERT:
      digitalWrite(LED_RED_1, blinkOn ? HIGH : LOW);
      break;
    case LED_ALARM:
      digitalWrite(LED_RED_1, HIGH);
      digitalWrite(LED_RED_2, HIGH);
      break;
  }
}

void DisplayModule::tick() {
  // Blink animation (toggle every 500ms for normal, 200ms for alarm)
  uint32_t blinkInterval = (currentLEDState == LED_ALARM) ? 200 : 500;
  
  if (millis() - lastBlinkTime > blinkInterval) {
    blinkOn = !blinkOn;
    lastBlinkTime = millis();
    updateLEDs();
  }
}

void DisplayModule::show7Seg(uint8_t digit) {
  if (!SEVENSEG_ENABLED) return;
  
  // 7-segment lookup table: {a,b,c,d,e,f,g}
  const uint8_t patterns[10] = {
    0b1110111,  // 0
    0b0100100,  // 1
    0b1011101,  // 2
    0b1101101,  // 3
    0b0101110,  // 4
    0b1101011,  // 5
    0b1111011,  // 6
    0b0100101,  // 7
    0b1111111,  // 8
    0b1101111   // 9
  };
  
  if (digit > 9) {
    // Blank all
    for (int i = 0; i < 7; i++) {
      // digitalWrite(SEVENSEG_PINS[i], LOW);
    }
  } else {
    uint8_t pattern = patterns[digit];
    for (int i = 0; i < 7; i++) {
      // digitalWrite(SEVENSEG_PINS[i], (pattern >> i) & 1);
    }
  }
}
