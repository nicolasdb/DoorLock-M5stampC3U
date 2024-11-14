import os
import sys
import time

os.system("python3 esptool/esptool.py --chip esp32c3 --port /dev/ttyACM0 erase_flash")

os.system("python3 esptool/esptool.py --chip esp32c3 --port /dev/ttyACM0 --baud 460800 write_flash -z 0x0   ESP32_GENERIC_C3-20240602-v1.23.0.bin")

