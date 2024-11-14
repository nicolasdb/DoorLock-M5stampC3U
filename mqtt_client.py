# mqtt_client.py
from umqtt.simple import MQTTClient
import credentials

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
    client = MQTTClient(
        client_id=b'esp32_door_lock',
        server=credentials.ADAFRUIT_IO_URL,
        user=credentials.ADAFRUIT_IO_USERNAME,
        password=credentials.ADAFRUIT_IO_KEY,
        ssl=False
    )

    client.set_callback(lambda t, m: on_message(t, m, door_control))
    client.connect()
    print("[MQTT] Connected to Adafruit IO MQTT Broker!")
    
    # Subscribe to command feed
    command_feed = f"{credentials.ADAFRUIT_IO_USERNAME}/feeds/{credentials.MQTT_COMMAND_FEED}"
    client.subscribe(command_feed.encode())
    print(f"[MQTT] Subscribed to command feed: {command_feed}")
    
    # Set up status callback in door_control
    door_control.set_status_callback(lambda status: publish_status(client, status))
    
    return client

def publish_status(client, status):
    topic = f"{credentials.ADAFRUIT_IO_USERNAME}/feeds/{credentials.MQTT_STATUS_FEED}"
    client.publish(topic, str(status))
    print(f"[MQTT] Published door status: {status} to {topic}")