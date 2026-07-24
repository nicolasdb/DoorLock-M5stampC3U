# pins.py
# Single source of truth for GPIO assignments. Imported by boot.py (fail-closed
# safety line) and door_control.py (runtime driver) so the two never drift.

RELAY_PIN = 5
BUTTON_PIN = 9
NEOPIXEL_PIN = 2
# RELAY2_PIN = 6  # reserved for a planned second relay, not wired/used yet
