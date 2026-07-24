# Design and its reasons

## Why polling instead of MQTT

The first prototype (still visible in git history) controlled the relay
over MQTT via Adafruit IO. That meant a persistent broker connection to
keep alive, a third-party cloud dependency, keepalive/reconnection edge
cases, and two vendored libraries — for a device whose job is one bit of
information. Polling `GET /check` every 3 seconds is crude but has no
state to corrupt: each request either succeeds or doesn't, and a missed
poll costs at most 3 seconds of latency. For a front door, robustness
beats elegance; the MQTT path was dropped entirely.

## Why the device is "dumb" on purpose

All policy — who may open, at which hours, audit logging — lives in the
backend. The firmware only knows how to ask "should the door be open?"
and how to fire a relay. This keeps the part that's hard to update (code
on a board inside a wall, reachable only by USB) as small and stable as
possible, while the part that changes often (community rules) lives where
deploys are cheap.

## Why backend pairing exists

MicroPython's TLS stack does not verify certificates by default, so
`https://` in the server URL proves nothing about who answered: a spoofed
DNS record, a rogue access point, or a captive portal could return
`HTTP 200` and open the door without ever reaching the real backend —
which is exactly what earlier firmware trusted.

Instead of chasing full TLS validation on a microcontroller, the pairing
scheme authenticates the *content* of the response: the device sends a
fresh random nonce with every poll, and the backend must answer with an
HMAC-SHA256 over `nonce:status`, keyed with a secret only that
device/backend pair holds. Consequences:

- the device obeys exactly one backend — whoever holds its secret;
- replaying a captured "open" response fails (the nonce changed);
- there is no clock dependency: a nonce needs no NTP, unlike
  timestamp-based schemes on a board with no battery-backed clock.

What pairing does *not* hide: the polls themselves are readable to a
network observer (door open/closed status). It protects the *actuation*,
not confidentiality.

## Why it fails closed

Every failure path — WiFi loss, main-loop exception, watchdog timeout,
reboot — forces the relay closed first. A door that occasionally needs a
button press because the network blipped is annoying; a door standing
open because the firmware crashed is a security incident. The physical
button remains as the offline override, deliberately independent of all
network code.

## Known gaps

- **No OTA updates** — changing firmware means USB access to the board.
  Accepted for now: one device, physically reachable, and OTA would grow
  the attack surface the pairing scheme just shrank.
- **No secret rotation story** — rotating `DEVICE_SECRET` requires editing
  `credentials.py` over USB. Fine for a handful of doors.
- **Polling latency** — worst case ~3 s between "open" granted and relay
  firing. Acceptable for a front door; lower the interval if not.
