# M5stamp-C3U MicroPython Project

## Goals
1. Control a relay from a button, using a NeoPixel to indicate the relay state (green for open, red for closed).
2. Implement WiFi connectivity, using the NeoPixel to slowly pulse blue while attempting to connect, then switch to the relay state color once connected.
3. Implement MQTT communication to remotely control the relay and publish its state when triggered by the hardware button.
4. Add a third method of door control via periodic server status checks.

## Features
- Button-based relay control
- NeoPixel state indication
- WiFi connectivity with auto-reconnect
- MQTT remote control and state publishing
- Server-based URL check for door opening
- Robust error handling and logging
- Configurable automatic door closing timer

## Credentials Setup
To set up your credentials, create a `src/credentials.py` file with the following template:

```python
# WiFi Configuration
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"

# Adafruit IO MQTT Configuration
ADAFRUIT_IO_URL = "io.adafruit.com"
ADAFRUIT_IO_USERNAME = "your_adafruit_username"
ADAFRUIT_IO_KEY = "your_adafruit_io_key"

# MQTT Feed Names
MQTT_STATUS_FEED = "doorlock-status"
MQTT_COMMAND_FEED = "doorlock-command"

# Server URL for Door Control (Optional)
SERVER_CHECK_URL = "https://your-server.com/check"
```

### Important Security Notes
- NEVER commit `credentials.py` to version control
- Keep your credentials file private and secure
- Use a `.gitignore` file to prevent accidental commits of sensitive information

## New Additions
1. WiFi Manager (`wifi_manager.py`)
   - Automatic WiFi connection and reconnection
   - Configurable connection attempts
   - Background thread for maintaining connectivity

2. URL Client (`url_client.py`)
   - Periodic server status checks
   - Automatic door opening based on server response
   - Configurable check interval and timeout
   - Independent background thread for server checks

## Instructions
1. Ensure you have MicroPython installed and configured on your M5stamp-C3U device.
2. Copy the following files to the device:
   - `src/main.py`
   - `src/credentials.py`
   - `src/wifi_manager.py`
   - `src/url_client.py`
   screen /dev/ttyUSB0 115200
   - `src/door_control.py`

3. Create and update `src/credentials.py` with your specific credentials
   - Replace placeholders with your actual WiFi, MQTT, and server details
   - Ensure the file is not tracked by version control

4. Run the `main.py` script:
   ```
   micropython src/main.py
   ```

## Door Control Methods
1. Physical Button: Press to toggle relay state
2. MQTT Commands: Remote control via Adafruit IO
3. Server URL Check: Periodic status checks to automatically open door

### Door Timer Configuration
The door automatically closes after a configurable duration. This can be adjusted by modifying the `DOOR_OPEN_DURATION` constant in `src/door_control.py`:
```python
# Door timeout configuration (in milliseconds)
DOOR_OPEN_DURATION = 3000  # Default: 3 seconds
```
Common configurations:
- 3 seconds: `DOOR_OPEN_DURATION = 3000`
- 5 seconds: `DOOR_OPEN_DURATION = 5000`
- 10 seconds: `DOOR_OPEN_DURATION = 10000`
- 1 minute: `DOOR_OPEN_DURATION = 60000`

The system checks the door timer every 100ms for precise timing and includes detailed logging of door open/close events.

## NeoPixel Indicators
- Blue (pulsing): Connecting to WiFi
- Green: Door Open
- Red: Door Closed
- Flashing Red: Error state

## Troubleshooting
- Verify WiFi and MQTT credentials
- Check server URL accessibility
- Monitor console output for connection and error messages
- Check door timing logs for precise open/close timing information

## Security Recommendations
- Use strong, unique passwords
- Regularly rotate credentials
- Avoid sharing sensitive configuration files
- Use environment variables or secure credential management in production

## Dependencies
- MicroPython
- umqtt library
- urequests library

Let me know if you have any questions or need further assistance!
