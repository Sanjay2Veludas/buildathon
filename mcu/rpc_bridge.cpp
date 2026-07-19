/*
 * RPC Bridge: Implementation
 * Handles JSON-based communication with Linux side
 */

#include "rpc_bridge.h"
#include "sensors.h"
#include "turret.h"
#include "display.h"

RPCBridge rpcBridge;

RPCBridge::RPCBridge() : rxBufferIndex(0) {
  memset(rxBuffer, 0, sizeof(rxBuffer));
}

void RPCBridge::setup(uint32_t baudrate) {
  Serial.begin(baudrate);
  delay(100);
  if (SERIAL_DEBUG) {
    Serial.println("[RPC] Bridge initialized");
  }
}

void RPCBridge::publishEvent(float bearing, uint16_t amplitudes[3], uint32_t timestamp) {
  // Format: {"type":"event","bearing_deg":45.2,"amplitudes":[120,150,100],"timestamp":12345}
  char json[256];
  snprintf(json, sizeof(json),
    "{\"type\":\"event\",\"bearing_deg\":%.1f,\"amplitudes\":[%d,%d,%d],\"timestamp\":%u}",
    bearing, amplitudes[0], amplitudes[1], amplitudes[2], timestamp);
  
  sendJSON(json);
}

void RPCBridge::process() {
  // Read available bytes from Serial
  while (Serial.available() > 0 && rxBufferIndex < sizeof(rxBuffer) - 1) {
    char c = Serial.read();
    
    if (c == '\n' || c == '\r') {
      if (rxBufferIndex > 0) {
        rxBuffer[rxBufferIndex] = '\0';
        handleCommand(rxBuffer);
        rxBufferIndex = 0;
      }
    } else if (c == '{') {
      // Start of new JSON
      rxBufferIndex = 0;
      rxBuffer[rxBufferIndex++] = c;
    } else if (rxBufferIndex > 0) {
      rxBuffer[rxBufferIndex++] = c;
    }
  }
}

void RPCBridge::handleCommand(const char* json) {
  if (SERIAL_DEBUG) {
    Serial.print("[RPC] RX: ");
    Serial.println(json);
  }
  
  parseCommand(json);
}

void RPCBridge::parseCommand(const char* json) {
  // Simple JSON parsing (not robust; suitable for trusted input only)
  // Production code would use ArduinoJson library
  
  if (strstr(json, "\"cmd\":\"point_turret\"")) {
    float deg = 0.0;
    sscanf(json, "{\"cmd\":\"point_turret\",\"degrees\":%f", &deg);
    cmd_pointTurret(deg);
  }
  else if (strstr(json, "\"cmd\":\"set_led\"")) {
    const char* level = strstr(json, "\"level\":\"");
    if (level) {
      char levelStr[16];
      sscanf(level, "\"level\":\"%15[^\"]\"", levelStr);
      cmd_setLED(levelStr);
    }
  }
  else if (strstr(json, "\"cmd\":\"lcd_text\"")) {
    char line1[17], line2[17];
    sscanf(json, "{\"cmd\":\"lcd_text\",\"line1\":\"%16[^\"]\",\"line2\":\"%16[^\"]\"", 
           line1, line2);
    cmd_lcdText(line1, line2);
  }
  else if (strstr(json, "\"cmd\":\"set_threshold\"")) {
    uint16_t offset = 100;
    sscanf(json, "{\"cmd\":\"set_threshold\",\"offset\":%hu", &offset);
    cmd_setThreshold(offset);
  }
  else if (strstr(json, "\"cmd\":\"set_armed\"")) {
    bool armed = true;
    if (strstr(json, "\"armed\":false")) armed = false;
    cmd_setArmed(armed);
  }
  else if (strstr(json, "\"cmd\":\"reset\"")) {
    cmd_reset();
  }
}

void RPCBridge::cmd_pointTurret(float deg) {
  turret.pointTo(deg);
  if (SERIAL_DEBUG) {
    Serial.print("[RPC] Point turret to ");
    Serial.print(deg);
    Serial.println("°");
  }
}

void RPCBridge::cmd_setLED(const char* level) {
  LEDState state = LED_IDLE;
  if (strcmp(level, "event") == 0) state = LED_EVENT;
  else if (strcmp(level, "alert") == 0) state = LED_ALERT;
  else if (strcmp(level, "alarm") == 0) state = LED_ALARM;
  
  display.setLEDState(state);
  if (SERIAL_DEBUG) {
    Serial.print("[RPC] Set LED: ");
    Serial.println(level);
  }
}

void RPCBridge::cmd_lcdText(const char* line1, const char* line2) {
  display.lcdLine1(line1);
  display.lcdLine2(line2);
  if (SERIAL_DEBUG) {
    Serial.print("[RPC] LCD: '");
    Serial.print(line1);
    Serial.print("' / '");
    Serial.print(line2);
    Serial.println("'");
  }
}

void RPCBridge::cmd_setThreshold(uint16_t offset) {
  sensors.setThreshold(offset);
  if (SERIAL_DEBUG) {
    Serial.print("[RPC] Threshold offset: ");
    Serial.println(offset);
  }
}

void RPCBridge::cmd_setArmed(bool armedFlag) {
  // This would set a global or module state; stub for now
  if (SERIAL_DEBUG) {
    Serial.print("[RPC] Armed: ");
    Serial.println(armedFlag ? "yes" : "no");
  }
}

void RPCBridge::cmd_reset() {
  turret.home();
  sensors.resetBaseline();
  display.lcdClear();
  display.setLEDState(LED_IDLE);
  if (SERIAL_DEBUG) {
    Serial.println("[RPC] System reset");
  }
}

void RPCBridge::sendJSON(const char* json) {
  Serial.println(json);
}
