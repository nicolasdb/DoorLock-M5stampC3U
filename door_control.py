# door_control.py
from machine import Pin
import neopixel
import time
import _thread
from pins import RELAY_PIN, RELAY2_PIN, BUTTON_PIN, NEOPIXEL_PIN

# Hardware setup
RELAY_ACTIVE_LOW = False  # these relay modules trigger on GPIO HIGH

# chan1 (office door) shares RELAY_PIN with the RFID badge-reader input:
# the reader's own relay holds the line high for ~30s on an accepted badge,
# which is plenty of margin for a polled (not IRQ) read. RELAY_PIN must
# spend almost all its life as Pin.OUT driven LOW (fail-closed rest state)
# and only flip to Pin.IN for the instant of a badge sample - see
# poll_badge(). pin1_lock serializes every touch of RELAY_PIN's mode/value
# across the main loop (badge poll, button) and the url_client background
# thread (backend-triggered opens), since MicroPython does not guarantee
# safe concurrent access to a Pin's mode from two threads.
pin1_lock = _thread.allocate_lock()

relay1 = Pin(RELAY_PIN, Pin.OUT)
relay2 = Pin(RELAY2_PIN, Pin.OUT)
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
np = neopixel.NeoPixel(Pin(NEOPIXEL_PIN), 1)

# Global state
last_press = 0
door1_timer = 0
door2_timer = 0
_relay1_active = False  # logical state: True = office door open / relay energized
_relay2_active = False  # logical state: True = gate open / relay energized
_badge_line_was_high = False  # edge-detect state for poll_badge()

CHANNELS = ("office", "gate")


def _drive(pin, active):
    if RELAY_ACTIVE_LOW:
        pin.value(0 if active else 1)
    else:
        pin.value(1 if active else 0)


def _set_relay1(active):
    """Drive chan1. Always re-asserts Pin.OUT first, since RELAY_PIN may
    currently be configured Pin.IN from a badge sample."""
    global _relay1_active
    relay1.init(Pin.OUT)
    _relay1_active = active
    _drive(relay1, active)


def _set_relay2(active):
    global _relay2_active
    _relay2_active = active
    _drive(relay2, active)


with pin1_lock:
    _set_relay1(False)  # Start with office door closed
_set_relay2(False)  # Start with gate closed

# Door timeout configuration
DOOR_OPEN_DURATION = 3000  # 3 seconds door open timeout


def set_led(r, g, b):
    np[0] = (r, g, b)
    np.write()


def set_wifi_status_led(is_connected):
    """
    Set LED color based on WiFi connection status
    Blue: Disconnected or connecting
    Green: Any door/gate open
    Red: Both closed
    """
    if not is_connected:
        # Pulsing blue when WiFi is disconnected
        for brightness in range(0, 256, 5):
            set_led(0, 0, min(brightness, 255))
            time.sleep(0.01)
        for brightness in range(255, -1, -5):
            set_led(0, 0, max(brightness, 0))
            time.sleep(0.01)
    elif _relay1_active or _relay2_active:
        set_led(0, 255, 0)  # Green for open
    else:
        set_led(255, 0, 0)  # Red for closed


def get_door_state(channel="office"):
    active = _relay1_active if channel == "office" else _relay2_active
    return 1 if active else 0


def open_channel(channel):
    global door1_timer, door2_timer
    if channel == "office":
        if _relay1_active:
            # Already open: ignore repeats, DOOR_OPEN_DURATION stays the
            # one source of truth for how long the relay stays energized.
            return
        print("[DOOR] Opening office door...")
        with pin1_lock:
            _set_relay1(True)
        door1_timer = time.ticks_ms()
    elif channel == "gate":
        if _relay2_active:
            return
        print("[DOOR] Opening gate...")
        _set_relay2(True)
        door2_timer = time.ticks_ms()
    else:
        raise ValueError("unknown channel: {}".format(channel))
    set_led(0, 255, 0)


def close_channel(channel):
    global door1_timer, door2_timer
    if channel == "office":
        print("[DOOR] Closing office door...")
        with pin1_lock:
            _set_relay1(False)
        door1_timer = 0
    elif channel == "gate":
        print("[DOOR] Closing gate...")
        _set_relay2(False)
        door2_timer = 0
    else:
        raise ValueError("unknown channel: {}".format(channel))
    if not _relay1_active and not _relay2_active:
        set_led(255, 0, 0)


# Back-compat wrappers: existing callers (url_client, button) mean chan1/office.
def open_door():
    open_channel("office")


def close_door():
    close_channel("office")


def handle_button(pin):
    global last_press
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press) > 300:  # Debounce
        last_press = now
        if not _relay1_active:  # If door is closed
            open_door()
        else:
            close_door()


def poll_badge():
    """Sample the badge-reader line on RELAY_PIN and open the gate on a
    rising edge. Must be called from the main loop only (not from a
    background thread) at a rate well under the reader's ~30s hold time.

    Skipped whenever chan1 is already driven open (Discord/backend
    request or badge itself): RELAY_PIN is an output for the whole
    duration of that hold, and must not be interrupted by a mode switch.
    """
    global _badge_line_was_high
    if _relay1_active:
        return
    with pin1_lock:
        relay1.init(Pin.IN, Pin.PULL_DOWN)
        line_high = bool(relay1.value())
        relay1.init(Pin.OUT)
        _drive(relay1, False)  # rest state: OUT, LOW

    if line_high and not _badge_line_was_high:
        print("[DOOR] Badge accepted (RFID module) - opening gate")
        open_channel("gate")
    _badge_line_was_high = line_high


def check_door_timeout():
    global door1_timer, door2_timer
    now = time.ticks_ms()
    if door1_timer > 0 and time.ticks_diff(now, door1_timer) >= DOOR_OPEN_DURATION:
        print("[DOOR] Office door timeout reached.")
        close_channel("office")
    if door2_timer > 0 and time.ticks_diff(now, door2_timer) >= DOOR_OPEN_DURATION:
        print("[DOOR] Gate timeout reached.")
        close_channel("gate")


def flash_error():
    for _ in range(3):
        set_led(255, 0, 0)
        time.sleep(0.2)
        set_led(0, 0, 0)
        time.sleep(0.2)
    set_led(0, 255, 0) if (_relay1_active or _relay2_active) else set_led(255, 0, 0)


def initialize():
    print("[DOOR] Initializing door control...")
    close_door()  # Ensure office door starts closed
    close_channel("gate")  # Ensure gate starts closed
    button.irq(trigger=Pin.IRQ_FALLING, handler=handle_button)  # Setup button interrupt
    print("[DOOR] Door initialized to closed state")
