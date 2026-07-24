import os
import sys

if len(sys.argv) < 2:
    print("Please provide the port as an argument")
    print("Example: python install.py /dev/ttyACM0")
    sys.exit(1)

port = sys.argv[1]

# Upload all Python files except install.py
python_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'install.py']
for file in python_files:
    os.system(f"mpremote connect {port} cp {file} :{file}")
