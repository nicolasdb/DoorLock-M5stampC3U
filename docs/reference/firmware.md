# Firmware reference

## Hardware (M5Stamp-C3U, or generic ESP32-C3 Super Mini — same SoC)

![pinout](esp32c3-super-mini_pinout.png)

| Peripheral | Pin | Notes |
|---|---|---|
| Relay | GPIO 1 | `1` = door open, `0` = closed; starts closed |
| Push-button | GPIO 9 | Internal pull-up, falling-edge IRQ, 300 ms debounce |
| NeoPixel | GPIO 2 | 1 LED |

## Files

| File | Purpose |
|---|---|
| `boot.py` | Connects WiFi, then hands off to `main.py` |
| `main.py` | Main loop: watchdog, health checks, door timeout |
| `door_control.py` | Relay + NeoPixel + physical button |
| `wifi_manager.py` | WiFi connect/reconnect with exponential backoff |
| `url_client.py` | Polls the backend, verifies the pairing signature |
| `credentials.example.py` | Template for WiFi + pairing settings |
| `install.py` | Uploads all `.py` files via `mpremote` |
| `firmware/flash.py`, `firmware/*.bin` | MicroPython image + flash script |

## `credentials.py` settings

| Setting | Meaning |
|---|---|
| `WIFI_SSID`, `WIFI_PASSWORD` | WiFi network to join |
| `DOOR_SERVER_URL` | Paired backend, no trailing slash (e.g. `https://door.example.org`) |
| `DEVICE_ID` | This device's id as registered on the backend |
| `DEVICE_SECRET` | Shared secret issued at registration; never sent over the wire |

## Wire protocol (`/check` polling)

Request, every 3 s:

```
GET {DOOR_SERVER_URL}/check?device_id={DEVICE_ID}&nonce={16-hex-char random}
User-Agent: CHB Door (ESP32-C3)
```

Expected response (HTTP 200 to open, 403 when closed):

```json
{"status": "open" | "closed", "sig": "<hex>"}
```

where `sig = HMAC-SHA256(DEVICE_SECRET, "<nonce>:<status>")`, hex-encoded.
The relay fires only when `status == "open"` **and** the signature
verifies. A 200 without a valid signature is logged
(`WARNING: got HTTP 200 without a valid signature`) and ignored.

## Timings

| What | Value | Where |
|---|---|---|
| Backend poll interval | 3 s | `url_client.py` `check_interval` |
| Request timeout | 5 s | `url_client.py` `timeout` |
| Door auto-close | 3000 ms | `door_control.py` `DOOR_OPEN_DURATION` |
| Door-timeout check | every 100 ms | `main.py` main loop |
| System health check | every 30 s | `main.py` `HEALTH_CHECK_INTERVAL` |
| Hardware watchdog | 30 s | `main.py` `machine.WDT` |
| Maintenance reboot | every 24 h | `main.py` `SystemManager` |
| WiFi reconnect backoff | 1 s → 60 s, reset after 10 attempts | `wifi_manager.py` |

## NeoPixel codes

| Color | Meaning |
|---|---|
| Blue (pulsing) | Connecting to WiFi |
| Red | Connected, door closed |
| Green | Door open |

## Failure behavior

- WiFi lost → door forced closed, reconnect with backoff; reboot after 5
  failed reconnect cycles.
- Any error in the main loop → door forced closed.
- Watchdog not fed for 30 s → hardware reset.
