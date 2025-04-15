import os
import json
import random
import datetime
import paho.mqtt.client as mqtt
from gpiozero import CPUTemperature
import psutil
import time

# MQTT Configuration
# MQTT_BROKER = '192.168.4.62' # Alvaro's home IP
MQTT_BROKER = '192.168.55.107' # IoT's IP
MQTT_PORT = 1883
MQTT_TOPIC_HEALTH = "med_max/system_health"


# MQTT_CLIENT_ID = f'RPI-mqtt'
# MQTT_USERNAME = 'emqx'
# MQTT_PASSWORD = 'public'

def get_system_metrics():
    """Get system health metrics"""
    cpu = CPUTemperature()
    return json.dumps({
        "cpu_temp": cpu.temperature,
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent
    })


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
    # For paho-mqtt 2.0.0, you need to add the properties parameter.
    # def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt.Client()

    # For paho-mqtt 2.0.0, you need to set callback_api_version.
    # client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)

    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT)
    return client

def publish(client):
    try:
        msg_count = 1
        while True:
            time.sleep(1)
            
            data = get_system_metrics()
            result = client.publish(MQTT_TOPIC_HEALTH, data)
            status = result[0]
            if status == 0:
                print(f"Sent to topic `{MQTT_TOPIC_HEALTH}`")
            else:
                print(f"Failed to send message to topic {MQTT_TOPIC_HEALTH}")

            if msg_count > 5000:
                break

    except KeyboardInterrupt:
        print('Exiting from code...')

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    client.loop_stop()

    
if __name__ == '__main__':
    run()