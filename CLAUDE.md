# CLAUDE.md

Guidance for AI assistants (and new contributors) working on this repo.

## What this is

MicroPython firmware for an M5Stamp-C3U (ESP32-C3) door controller. It
polls its paired backend (`nicolasdb/door`) and fires the door relay on a
cryptographically verified "open". The backend holds all policy; this
device is deliberately dumb — see `docs/explanation/design.md`.

## Hard rules

- **Fail closed.** Every failure path (WiFi loss, exceptions, watchdog,
  reboot) must force the relay closed before anything else. Never add a
  code path that can leave the relay open unattended.
- **The pairing scheme is a cross-repo contract.** The `/check` request
  (`device_id` + `nonce`) and response verification
  (`HMAC-SHA256(DEVICE_SECRET, "<nonce>:<status>")`) must stay in lockstep
  with `server/routes/check/` in nicolasdb/door. Never open the relay on
  an unverified response — a bare HTTP 200 is not proof of anything here
  (MicroPython does not verify TLS certificates by default).
- **No MQTT.** It was removed on purpose; don't reintroduce it or other
  persistent-connection dependencies.
- `credentials.py` is gitignored; never commit real WiFi passwords, device
  secrets, or backend URLs of a live deployment.

## Constraints of the platform

- This is MicroPython, not CPython: no `hmac` module (hence the manual
  implementation in `url_client.py`), `uhashlib`/`ubinascii`/`urequests`
  instead of the stdlib, `_thread` for background work, and tight RAM.
  Test changes on a real board — there is no emulator step in this repo.
- `install.py` uploads every `*.py` in the repo root to the device; keep
  the root clean of anything that shouldn't land on the board.

## Documentation

Follows the Divio system (https://docs.divio.com/documentation-system/):
README = short orientation only; procedures in `docs/how-to/`; tables and
protocol in `docs/reference/firmware.md`; rationale in
`docs/explanation/design.md`. Update the reference tables when changing
pins, timings, or the wire protocol.
