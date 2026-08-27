# pins.py
# Single source of truth for GPIO assignments. Imported by boot.py (fail-closed
# safety line) and door_control.py (runtime driver) so the two never drift.

RELAY_PIN = 5   # chan1 / office door - also doubles as the badge-reader input
RELAY2_PIN = 6  # chan2 / main gate - output only
BUTTON_PIN = 9
NEOPIXEL_PIN = 2
