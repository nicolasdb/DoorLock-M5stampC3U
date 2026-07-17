# How to flash and install a door controller

Goal: from a blank M5Stamp-C3U to a device polling your backend. You need a
USB-C cable and Python 3 on your computer.

## 1. Install the tools

```bash
pip install esptool==4.8.1
pip install adafruit-ampy
```

## 2. Find the serial port

Plug the device in, then:

```bash
ls /dev/tty.*        # macOS — e.g. /dev/tty.usbmodem101
ls /dev/ttyACM*      # Linux — e.g. /dev/ttyACM0
```

Use your port in place of `/dev/tty.usbmodem101` below. If nothing shows
up, hold the device's center button while plugging in (download mode).

## 3. Flash MicroPython (once per device)

```bash
python3 firmware/flash.py /dev/tty.usbmodem101
```

This erases the flash and writes the MicroPython image bundled in
`firmware/`.

## 4. Configure credentials

```bash
cp credentials.example.py credentials.py
```

Edit `credentials.py`: WiFi SSID/password, `DOOR_SERVER_URL`, and the
`DEVICE_ID` / `DEVICE_SECRET` issued when you
[registered the device on the backend](https://github.com/nicolasdb/door/blob/main/docs/how-to/pair-a-device.md).
Never commit this file (it's gitignored).

## 5. Upload the firmware scripts

```bash
python3 install.py /dev/tty.usbmodem101
```

This uploads every `.py` file, including your `credentials.py`.

## 6. Verify

Power-cycle the device — it starts by itself (`boot.py` → `main.py`):

- LED pulses blue while connecting to WiFi, then turns red (door closed).
- The backend's `/status` page lists the device as online within seconds.
- To watch the logs live: `screen /dev/tty.usbmodem101 115200`
  (quit: `Ctrl-A` then `k`). You should see a `/check` poll every 3s.

## Updating an already-installed device

Repeat steps 5–6 only (no re-flash needed). There is no over-the-air
update: you need the USB cable each time.
