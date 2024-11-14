# door_control.py
from machine import Pin
import neopixel
import time

# Hardware setup
relay = Pin(1, Pin.OUT)
relay.value(0)  # Start with door closed
button = Pin(9, Pin.IN, Pin.PULL_UP)
np = neopixel.NeoPixel(Pin(2), 1)

# Global state
last_press = 0
door_timer = 0
status_callback = None  # Callback function to update MQTT status

def set_led(r, g, b):
    np[0] = (r, g, b)
    np.write()

def set_status_callback(callback):
    global status_callback
    status_callback = callback

def get_door_state():
    return relay.value()

def open_door():
    global door_timer
    print("[DOOR] Opening door...")
    relay.value(1)  # Open door
    set_led(0, 255, 0)  # Green LED
    door_timer = time.ticks_ms()  # Start door timer
    if status_callback:
        status_callback(1)  # Notify MQTT about door open

def close_door():
    global door_timer
    print("[DOOR] Closing door...")
    relay.value(0)  # Close door
    set_led(255, 0, 0)  # Red LED
    door_timer = 0
    if status_callback:
        status_callback(0)  # Notify MQTT about door closed

def handle_button(pin):
    global last_press
    now = time.ticks_ms()
    if time.ticks_diff(now, last_press) > 300:  # Debounce
        last_press = now
        if relay.value() == 0:  # If door is closed
            open_door()
        else:
            close_door()

def check_door_timeout():
    global door_timer
    if door_timer > 0 and time.ticks_diff(time.ticks_ms(), door_timer) >= 3000:
        print("[DOOR] Door timeout reached, closing door")
        close_door()

def flash_error():
    for _ in range(3):
        set_led(255, 0, 0)
        time.sleep(0.2)
        set_led(0, 0, 0)
        time.sleep(0.2)
    set_led(255, 0, 0) if relay.value() == 0 else set_led(0, 255, 0)

def initialize():
    print("[DOOR] Initializing door control...")
    close_door()  # Ensure door starts closed
    button.irq(trigger=Pin.IRQ_FALLING, handler=handle_button)  # Setup button interrupt
    print("[DOOR] Door initialized to closed state")