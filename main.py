# main.py
import time
import mqtt_client
import door_control

def run():
    print('[MAIN] Starting...')
    
    # Initialize door control (sets up button interrupt)
    door_control.initialize()
    
    # Connect to MQTT and set up callbacks
    client = mqtt_client.connect_mqtt(door_control)
    
    # Publish initial status
    mqtt_client.publish_status(client, door_control.get_door_state())
    
    print('[MAIN] Setup complete, entering main loop...')
    
    while True:
        try:
            client.check_msg()  # Check for MQTT messages
            door_control.check_door_timeout()  # Check if door needs to close
            time.sleep(0.1)  # Short delay to prevent busy waiting
        except Exception as e:
            print('[MAIN] Error in main loop:', e)
            time.sleep(1)  # Delay before retry

if __name__ == '__main__':
    run()