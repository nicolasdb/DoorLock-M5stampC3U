# boot.py
import machine
import network
import time
from pins import RELAY_PIN, RELAY2_PIN, BUTTON_PIN

# Fail closed before anything else: relays are active-high.
machine.Pin(RELAY_PIN, machine.Pin.OUT).value(0)
machine.Pin(RELAY2_PIN, machine.Pin.OUT).value(0)

# Grace period: gives mpremote a window to interrupt and enter raw REPL
# before the background poll thread starts and starves USB access.
# Safe mode: GPIO9 is a strapping pin, so holding it *during* power-on
# enters ROM download mode instead — press and hold it right *after*
# reset, any time within this window, to skip main.py and keep a clean
# REPL for uploads.
print('[BOOT] Grace period (3s): press door/BOOT button now for safe mode...')
_btn = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
for _ in range(30):
    if _btn.value() == 0:
        print('[BOOT] SAFE MODE: button pressed, skipping main.py (relay closed)')
        raise SystemExit
    time.sleep(0.1)

import credentials

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print('[BOOT] Activating WiFi interface...')
    if not wlan.isconnected():
        print('[BOOT] Connecting to Wi-Fi network:', credentials.WIFI_SSID)
        wlan.connect(credentials.WIFI_SSID, credentials.WIFI_PASSWORD)
        attempt = 1
        while not wlan.isconnected():
            print('[BOOT] Connection attempt {}...'.format(attempt))
            time.sleep(5)
            attempt += 1
    print('[BOOT] WiFi Connected! Network config:', wlan.ifconfig())
    return wlan

# Connect to Wi-Fi on boot
print('[BOOT] Starting boot sequence...')
wlan = connect_wifi()

# Run main.py after setup
try:
    print('[BOOT] WiFi connected, checking main.py...')
    with open('main.py', 'r') as f:
        print('[BOOT] Main.py file found')
    
    print('[BOOT] Importing main module...')
    import main
    print('[BOOT] Main module imported, starting run()...')
    main.run()
except Exception as e:
    print("[BOOT] Error details:", str(e))
    import sys
    sys.print_exception(e)  # This will print the full traceback
