# services/mqtt_publisher.py
import paho.mqtt.client as mqtt
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

def publish_command(command: dict):
    client = mqtt.Client(client_id="Backend-Publisher", protocol=mqtt.MQTTv5)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    client.connect(MQTT_BROKER, MQTT_PORT)
    client.loop_start()

    import json
    payload = json.dumps(command)

    result = client.publish("/mesh/commands", payload, qos=1)
    result.wait_for_publish()
    print(f"[MQTT] Published to /mesh/commands: {payload}")
    
    client.loop_stop()
    client.disconnect()
