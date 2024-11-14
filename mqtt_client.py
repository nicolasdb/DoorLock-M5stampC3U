# mqtt_client.py
from umqtt.simple import MQTTClient
import credentials
import time

# Global variable to track last successful connection
last_mqtt_connection = 0

# MQTT Configuration
MQTT_KEEPALIVE = 120  # Keepalive timeout in seconds
MQTT_CHECK_INTERVAL = 45000  # Check every 45 seconds (in milliseconds)

def on_message(topic, msg, door_control):
    try:
        command = int(msg)
        current_state = door_control.get_door_state()
        
        if command == 1 and current_state == 0:
            print("[MQTT] Received command to open door")
            door_control.open_door()
        elif command == 0 and current_state == 1:
            print("[MQTT] Received command to close door")
            door_control.close_door()
        else:
            print(f"[MQTT] Door already in requested state: {command}")
    except Exception as e:
        print("[MQTT] Error processing message:", e)
        door_control.flash_error()

def connect_mqtt(door_control):
    global last_mqtt_connection
    
    client = MQTTClient(
        client_id=b'esp32_door_lock',
        server=credentials.ADAFRUIT_IO_URL,
        user=credentials.ADAFRUIT_IO_USERNAME,
        password=credentials.ADAFRUIT_IO_KEY,
        ssl=False,
        keepalive=MQTT_KEEPALIVE  # Broker will expect ping every 120 seconds
    )

    client.set_callback(lambda t, m: on_message(t, m, door_control))
    client.connect()
    last_mqtt_connection = time.time()
    print(f"[MQTT] Connected to Adafruit IO MQTT Broker! (keepalive: {MQTT_KEEPALIVE}s, check interval: {MQTT_CHECK_INTERVAL/1000}s)")
    
    # Subscribe to command feed
    command_feed = f"{credentials.ADAFRUIT_IO_USERNAME}/feeds/{credentials.MQTT_COMMAND_FEED}"
    client.subscribe(command_feed.encode())
    print(f"[MQTT] Subscribed to command feed: {command_feed}")
    
    # Set up status callback in door_control
    door_control.set_status_callback(lambda status: publish_status(client, status))
    
    return client

def check_mqtt_connection(client):
    """Check MQTT connection and reconnect if necessary"""
    global last_mqtt_connection
    
    try:
        # Try to ping the broker
        client.ping()
        last_mqtt_connection = time.time()
        return True
    except:
        print("[MQTT] Connection lost, attempting to reconnect...")
        try:
            client.disconnect()
        except:
            pass
        
        try:
            client.connect()
            last_mqtt_connection = time.time()
            print("[MQTT] Successfully reconnected to broker")
            return True
        except Exception as e:
            print(f"[MQTT] Reconnection failed: {e}")
            return False

def publish_status(client, status):
    try:
        topic = f"{credentials.ADAFRUIT_IO_USERNAME}/feeds/{credentials.MQTT_STATUS_FEED}"
        client.publish(topic, str(status))
        print(f"[MQTT] Published door status: {status} to {topic}")
    except Exception as e:
        print(f"[MQTT] Error publishing status: {e}")
        # Connection might be lost, trigger reconnect on next check
        global last_mqtt_connection
        last_mqtt_connection = 0
