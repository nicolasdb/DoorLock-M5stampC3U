# Copy this file to credentials.py and fill in real values.
# credentials.py is gitignored - never commit it.

# WiFi
WIFI_SSID = ""
WIFI_PASSWORD = ""

# Backend pairing
# DOOR_SERVER_URL is the backend this controller is paired with (no
# trailing slash). DEVICE_ID and DEVICE_SECRET are issued once, by whoever
# runs that backend, when this specific piece of hardware is registered
# with it - the backend must have the same DEVICE_ID -> DEVICE_SECRET
# mapping for pairing to work. The secret is used to verify /check
# responses (see url_client.py); it is never sent over the wire.
DOOR_SERVER_URL = "https://door.example.org"
DEVICE_ID = "front-door-01"
DEVICE_SECRET = ""
