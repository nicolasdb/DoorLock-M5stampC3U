# How to flash and install a door controller

Goal: from a blank ESP32-C3 board (M5Stamp-C3U or generic ESP32-C3 Super Mini — same SoC) to a device polling your backend. You need a USB-C cable and `esptool` + `mpremote` on your computer.

Each step below gives an **agent prompt** first — hand it to an AI coding agent (e.g. Claude Code) with Bash access and it'll run and verify the step for you — followed by the **manual fallback** commands in case you're doing it by hand or the agent gets stuck. Steps that require physical action (plugging in USB, holding BOOT, wiring) still need a human regardless of approach.

**Don't use the MicroPico VS Code extension for this.** It was tried and is a dead end on native-USB ESP32-C3 boards (Super Mini): even after fixing its `udevadm` dependency inside the VS Code Flatpak sandbox, its board-connect handshake (built around the RP2040/Pico rese sequence) never completes on this chip, while a plain MicroPython REPL on the same port works fine. `esptool` (flashing) and `mpremote` (REPL, file upload) are the proven working path — use those instead.

## 0. Isolation note (Fedora Kinoite / other immutable hosts)

`pip install` doesn't work on an immutable host. Run the install and every
command below inside a distrobox/toolbox container instead — the
container shares `/dev` with the host, so the board's serial port is
visible from inside it with no extra setup.

## 1. Install the tools

> **Agent prompt:** "Set up a Python venv at `~/.venvs/esp32` and install
> `esptool==4.8.1` and `mpremote` in it. If this is an immutable host
> (Fedora Kinoite/Silverblue), do it inside a distrobox/toolbox container
> instead — check `/etc/os-release` or ask me if unsure."

Manual fallback:

```bash
python3 -m venv ~/.venvs/esp32 && source ~/.venvs/esp32/bin/activate
pip install esptool==4.8.1 mpremote
```

## 2. Find the serial port

Plug the board in (no button held — this is a normal power-on, not
download mode).

> **Agent prompt:** "Plug the ESP32-C3 board in via USB (no button
> held) — tell me when done. Then find its serial port
> (`/dev/ttyACM*` on Linux, `/dev/tty.usbmodem*` on macOS) and use it
> for the rest of these steps."

Manual fallback:

```bash
ls /dev/tty.*        # macOS — e.g. /dev/tty.usbmodem101
ls /dev/ttyACM*       # Linux — e.g. /dev/ttyACM0
```

Use your port in place of `/dev/ttyACM0` below.

## 3. Flash MicroPython (once per device)

Put the board in download mode: hold the **BOOT** button and tap
**RESET** (or hold BOOT while plugging in) — this needs a human hand.

> **Agent prompt:** "Once I confirm the board is in download mode, run
> `python3 firmware/flash.py <port>` to flash MicroPython. Then tell me
> to power-cycle the board normally (no BOOT held), and verify it boots
> by running `mpremote connect <port> exec \"print(1+1)\"` — confirm it
> prints `2` before I touch any wiring. Optionally blink the built-in
> LED (GPIO 8) to confirm GPIO control."

Manual fallback:

```bash
python3 firmware/flash.py /dev/ttyACM0
```

This erases the flash and writes the MicroPython image bundled in
`firmware/`. Power-cycle the board normally afterward (no BOOT held) —
this is the only step that needs download mode.

**Verify before wiring anything:** confirm MicroPython actually boots
and responds before touching the relay/button/NeoPixel wiring.

```bash
mpremote connect /dev/ttyACM0 exec "print(1+1)"   # should print 2
```

Optionally blink the board's built-in LED (GPIO 8 on the Super Mini) to
confirm GPIO control works:

```bash
mpremote connect /dev/ttyACM0 exec "
import machine, time
led = machine.Pin(8, machine.Pin.OUT)
for _ in range(4):
    led.value(1); time.sleep(0.3)
    led.value(0); time.sleep(0.3)
"
```

## 4. Wire the board

Relay → GPIO 1, push-button → GPIO 9, NeoPixel → GPIO 2. See
[`docs/reference/firmware.md`](../reference/firmware.md) for details.
GPIO 9 is a strapping pin (boot-mode select) — don't hold the button
down while powering the board on, or it boots into download mode
instead of MicroPython.

This is a physical wiring step — hands only, no agent prompt applies.

**Check your relay module's trigger polarity before wiring it in.** This
firmware assumes an active-high module by default; many cheap relay
boards are active-low and need a full 5V logic HIGH to sit idle, which
the ESP32-C3's 3.3V GPIO can't provide — the relay will appear "stuck
on" no matter what the firmware does. See
[`docs/reference/firmware.md`](../reference/firmware.md#relay-module-polarity)
to test polarity by hand, and
[`docs/reference/active-low-relay-with-5v-trigger.md`](../reference/active-low-relay-with-5v-trigger.md)
if you only have active-low/5V-threshold modules on hand.

## 5. Configure credentials

> **Agent prompt:** "Copy `credentials.example.py` to `credentials.py`
> if it doesn't already exist. Ask me for the WiFi SSID/password,
> `DOOR_SERVER_URL`, and the `DEVICE_ID`/`DEVICE_SECRET` (from pairing
> the device on the backend), then fill them into `credentials.py`.
> Confirm the file is gitignored before finishing — never commit real
> secrets."

Manual fallback:

```bash
cp credentials.example.py credentials.py
```

Edit `credentials.py`: WiFi SSID/password, `DOOR_SERVER_URL`, and the
`DEVICE_ID` / `DEVICE_SECRET` issued when you
[registered the device on the backend](https://github.com/nicolasdb/door/blob/main/docs/how-to/pair-a-device.md).
Never commit this file (it's gitignored).

## 6. Upload the firmware scripts

> **Agent prompt:** "Run `python3 install.py <port>` to upload every
> `.py` file in the repo root, including `credentials.py`, to the
> board."

Manual fallback:

```bash
python3 install.py /dev/ttyACM0
```

This uploads every `.py` file, including your `credentials.py`.

## 7. Verify

Power-cycle the device — it starts by itself (`boot.py` → `main.py`).
This is a physical step — ask a human to power-cycle, then continue.

> **Agent prompt:** "After I power-cycle the device, connect via
> `mpremote connect <port>` and watch the boot log. Confirm you see a
> `/check` poll roughly every 3s and no unhandled exceptions. Ask me to
> confirm the LED behavior (blue pulse → red = door closed) and check
> the backend's `/status` page shows the device online."

Manual fallback:

- LED pulses blue while connecting to WiFi, then turns red (door closed).
- The backend's `/status` page lists the device as online within seconds.
- To watch the logs live: `mpremote connect /dev/ttyACM0` (quit:
  `Ctrl-]`). You should see a `/check` poll every 3s.

## Updating an already-installed device

Repeat steps 6–7 only (no re-flash needed). There is no over-the-air
update: you need the USB cable each time.
