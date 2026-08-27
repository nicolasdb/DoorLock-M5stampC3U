# M5stamp-C3U Door Controller Firmware

The physical half of a community door: a tiny MicroPython board wired to
the door's relay, which opens when its paired backend says so.

## Why

The [door backend](https://github.com/nicolasdb/door) decides *who* may
open the door; something physical still has to *actually* open it, reliably
and safely. This firmware is that muscle — deliberately simple, so the door
keeps working (or fails closed) no matter what happens upstream.

## How

```
 backend (policy)              this device (muscle)
 ─────────────────    ────────────────────────────────────
 GET /check     ◀──   polls every 3s, with a fresh nonce
 signed answer  ──▶   verifies the signature is from its
                      paired backend, then fires the relay
                      (auto-closes after 3s; button works
                      offline; LED shows the state)
```

It only obeys the one backend it was **paired** with — a bare `HTTP 200`
never opens the door.

## What

- MicroPython on an M5Stamp-C3U (ESP32-C3): two relay channels (office
  door + main gate), push-button, NeoPixel, RFID badge input.
- WiFi auto-reconnect, watchdog, daily maintenance reboot — fails closed.
- HMAC-verified polling against the paired backend.

## Documentation

Organized following the [Divio documentation system](https://docs.divio.com/documentation-system/):

| I want to... | Go to |
|---|---|
| flash and install a device | [docs/how-to/flash-and-install.md](docs/how-to/flash-and-install.md) |
| pair it with a backend | [pair-a-device (backend repo)](https://github.com/nicolasdb/door/blob/main/docs/how-to/pair-a-device.md) |
| look up pins, files, LED codes, timings, the wire protocol | [docs/reference/firmware.md](docs/reference/firmware.md) |
| understand why it works this way | [docs/explanation/design.md](docs/explanation/design.md) |
