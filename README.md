# M5stamp-C3U Door Controller Firmware

MicroPython firmware for an M5Stamp-C3U (ESP32-C3) wired to a parlophone
relay. This is the canonical source for the door-controller firmware used
by the [door](https://github.com/nicolasdb/door) backend project - the
backend repo no longer vendors a copy of this code, it just links here.

## History

The original prototype (see git history) controlled the relay over MQTT via
Adafruit IO. That approach was dropped in favor of a simpler webhook/polling
model: the device just polls a backend endpoint every few seconds and opens
the relay when told to. MQTT support and its vendored dependencies have been
removed - this repo now only contains the polling-based firmware that is
actually deployed.

## How it works

1. On boot, the device connects to WiFi and starts with the relay closed.
2. A background thread polls `GET {DOOR_SERVER_URL}/check` every 3 seconds.
3. The device authenticates itself as a specific, paired piece of hardware
   and only trusts responses signed by that pairing - see **Backend
   pairing** below.
4. The physical button can also toggle the relay directly, independent of
   the network.
5. The relay auto-closes after `DOOR_OPEN_DURATION` (default 3s).

## Backend pairing

Earlier versions opened the door on any bare `HTTP 200` from the check
endpoint. That's spoofable: MicroPython's TLS stack does not verify
certificates by default, so a DNS hijack, a rogue access point, or a
misconfigured proxy could return a `200` and pop the lock without ever
touching the real backend.

This firmware instead ties each device to one backend with a shared secret:

- Each controller has a `DEVICE_ID` and a `DEVICE_SECRET`, issued once by
  whoever runs the backend it's paired with.
- Every poll sends a fresh random `nonce` along with the `DEVICE_ID`.
- The backend must reply with `{"status": "open"|"closed", "sig": "<hex>"}`
  where `sig = HMAC-SHA256(DEVICE_SECRET, "<nonce>:<status>")`.
- The firmware recomputes that HMAC locally and only calls `open_door()`
  when it matches. A `200` with no valid signature is logged and ignored.

This means a device will only ever be commanded by the backend it was
explicitly paired with (whoever holds the matching `DEVICE_SECRET`), not by
whatever answers on the configured hostname. See the paired backend's docs
for how to register a device (`DEVICE_ID` -> `DEVICE_SECRET` mapping); as of
this writing that reference implementation lives in
[`nicolasdb/door`](https://github.com/nicolasdb/door)'s `/check` route.

## Setup

1. Copy `credentials.example.py` to `credentials.py` and fill in your WiFi,
   `DOOR_SERVER_URL`, `DEVICE_ID`, and `DEVICE_SECRET`. `credentials.py` is
   gitignored - never commit it.
2. Install flashing tools:
   ```bash
   pip install esptool==4.8.1
   pip install adafruit-ampy
   ```
3. Flash MicroPython onto the device:
   ```bash
   python3 firmware/flash.py /dev/tty.usbmodem101
   ```
   (replace the port with the right one for your machine - `ls /dev/tty.*`)
4. Upload the scripts:
   ```bash
   python3 install.py /dev/tty.usbmodem101
   ```
5. The device runs `main.py` automatically via `boot.py` on power-up. To
   watch logs live: `screen /dev/tty.usbmodem101 115200`.

## Files

| File | Purpose |
|---|---|
| `boot.py` | Connects WiFi, then hands off to `main.py` |
| `main.py` | Main loop: watchdog, health checks, door timeout |
| `door_control.py` | Relay + NeoPixel + physical button |
| `wifi_manager.py` | WiFi connect/reconnect with backoff |
| `url_client.py` | Polls the backend, verifies pairing signature |
| `credentials.example.py` | Template for WiFi + pairing secrets |
| `install.py` | Uploads all `.py` files via `ampy` |
| `firmware/flash.py`, `firmware/*.bin` | MicroPython base firmware + flash script |

## Door timer

`DOOR_OPEN_DURATION` in `door_control.py` controls how long the relay stays
open before auto-closing (default `3000` ms).

## NeoPixel indicators

- Blue (pulsing): connecting to WiFi
- Green: door open
- Red: door closed

## Known gaps / ideas for next iteration

- No OTA update path - firmware changes still require a physical USB flash.
- No device-side clock sync, so the pairing scheme uses a per-request nonce
  instead of timestamps (avoids replay without needing NTP).
- Only one device/secret per controller - fine for a single door, would need
  a lightweight rotation story if this scales to many doors.
