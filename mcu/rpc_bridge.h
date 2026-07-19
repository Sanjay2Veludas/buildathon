/*
 * RPC Bridge: Communication with Linux side via Arduino App Lab RPC
 */

#ifndef RPC_BRIDGE_H
#define RPC_BRIDGE_H

#include "config.h"

/*
 * Arduino App Lab RPC uses JSON over serial.
 * MCU publishes events and handles commands.
 * 
 * EVENT (MCU → Linux):
 *   {"type":"event", "bearing_deg":45.2, "amplitudes":[120,150,100], "timestamp":12345}
 * 
 * COMMAND (Linux → MCU):
 *   {"cmd":"point_turret", "degrees":90.0}
 *   {"cmd":"set_led", "level":"alert"}
 *   {"cmd":"lcd_text", "line1":"Hello", "line2":"World"}
 *   {"cmd":"set_threshold", "offset":120}
 */

class RPCBridge {
public:
  RPCBridge();
  void setup(uint32_t baudrate = RPC_BAUDRATE);
  
  // Publish an event to Linux
  void publishEvent(float bearing, uint16_t amplitudes[3], uint32_t timestamp);
  
  // Poll for incoming commands, dispatch to handlers
  void process();
  
  // Utility: send raw JSON (for testing)
  void sendJSON(const char* json);
  
private:
  void handleCommand(const char* json);
  void parseCommand(const char* json);
  
  // Command handlers
  void cmd_pointTurret(float deg);
  void cmd_setLED(const char* level);
  void cmd_lcdText(const char* line1, const char* line2);
  void cmd_setThreshold(uint16_t offset);
  void cmd_setArmed(bool armed);
  void cmd_reset();
  
  char rxBuffer[512];
  uint16_t rxBufferIndex;
};

extern RPCBridge rpcBridge;

#endif // RPC_BRIDGE_H
