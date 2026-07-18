# How to flash and install a door controller

Goal: from a blank ESP32-C3 board (M5Stamp-C3U or generic ESP32-C3 Super
Mini — same SoC) to a device polling your backend. You need a USB-C cable
and `esptool` + `mpremote` on your computer.

**Don't use the MicroPico VS Code extension for this.** It was tried and
is a dead end on native-USB ESP32-C3 boards (Super Mini):
even after fixing its `udevadm` dependency inside the VS Code Flatpak
sandbox, its board-connect handshake (built around the RP2040/Pico reset
sequence) never completes on this chip, while a plain MicroPython REPL on
the same port works fine. `esptool` (flashing) and `mpremote` (REPL, file
upload) are the proven working path — use those instead.

## 0. Isolation note (Fedora Kinoite / other immutable hosts)

`pip install` doesn't work on an immutable host. Run the install and every
command below inside a distrobox/toolbox container instead — the
container shares `/dev` with the host, so the board's serial port is
visible from inside it with no extra setup.

## 1. Install the tools

```bash
python3 -m venv ~/.venvs/esp32 && source ~/.venvs/esp32/bin/activate
pip install esptool==4.8.1 mpremote
```

## 2. Find the serial port

Plug the board in (no button held — this is a normal power-on, not
download mode), then:

```bash
ls /dev/tty.*        # macOS — e.g. /dev/tty.usbmodem101
ls /dev/ttyACM*       # Linux — e.g. /dev/ttyACM0
```

Use your port in place of `/dev/ttyACM0` below.

## 3. Flash MicroPython (once per device)

Put the board in download mode: hold the **BOOT** button and tap
**RESET** (or hold BOOT while plugging in), then:

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

## 5. Configure credentials

```bash
cp credentials.example.py credentials.py
```

Edit `credentials.py`: WiFi SSID/password, `DOOR_SERVER_URL`, and the
`DEVICE_ID` / `DEVICE_SECRET` issued when you
[registered the device on the backend](https://github.com/nicolasdb/door/blob/main/docs/how-to/pair-a-device.md).
Never commit this file (it's gitignored).

## 6. Upload the firmware scripts

```bash
python3 install.py /dev/ttyACM0
```

This uploads every `.py` file, including your `credentials.py`.

## 7. Verify

Power-cycle the device — it starts by itself (`boot.py` → `main.py`):

- LED pulses blue while connecting to WiFi, then turns red (door closed).
- The backend's `/status` page lists the device as online within seconds.
- To watch the logs live: `mpremote connect /dev/ttyACM0` (quit:
  `Ctrl-]`). You should see a `/check` poll every 3s.

## Updating an already-installed device

Repeat steps 6–7 only (no re-flash needed). There is no over-the-air
update: you need the USB cable each time.
