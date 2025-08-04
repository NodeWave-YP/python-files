import paho.mqtt.client as mqtt
from services.supabase_client import supabase
import json, ssl, os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MQTT credentials from .env
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# Cache to hold MAC -> node_id mapping
mqtt_mac_cache = {}

# Create the client globally so it's shared
mqtt_client = mqtt.Client(client_id="NodeWave-Backend", protocol=mqtt.MQTTv5)

# ======== CALLBACKS =========

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("nodewave/registration")
    client.subscribe("/mesh/backend")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"[MQTT] Raw payload on {topic}: {payload}")

    try:
        data = json.loads(payload)
        mac_address = data.get("mac", "").upper()

        if not mac_address:
            print("[MQTT] No MAC in payload.")
            return

        # Handle backend metrics from ESP
        if topic == "/mesh/backend":
            # Lookup node_id by MAC
            result = supabase.table("node").select("node_id").eq("mac_address", mac_address).limit(1).execute()
            if not result.data:
                print(f"[MQTT] MAC {mac_address} not recognized.")
                return

            node_id = result.data[0]["node_id"]

            signal = data.get("rssi")
            latency = data.get("latency_ms")
            usage = data.get("data_total")
            timestamp =  data.get("timestamp")
            sent = data.get("data_sent")
            recv = data.get("data_received")

            if None in (signal, latency, usage):
                print(f"[MQTT] Incomplete metrics for {mac_address}. Skipping insert.")
                return

            # Store the performance data
            supabase.table("performance_metrics").insert({
                "node_id": node_id,
                "signal_strength": signal,
                "latency": latency, 
                "data_usage": usage,
                "data_sent" : sent,
                "data_received" : recv,
                "metric_timestamp" : timestamp
            }).execute()

            print(f"[MQTT] Stored data for node {node_id} from MAC {mac_address}")

        # Handle registration messages from ESP nodes
        elif topic == "nodewave/registration":
            is_active = data.get('active', False)
    
    # Lookup MAC in Supabase
            result = supabase.table("node").select("node_id").eq("mac_address", mac_address).limit(1).execute()
    
            if result.data:
                node_id = result.data[0]["node_id"]
                mqtt_mac_cache[mac_address] = node_id  # Cache it
                print(f"[MQTT] MAC {mac_address} linked to node ID {node_id}")
                
                # Update the node's active status
                supabase.table('node').update({
                    "status": "active" if is_active else "inactive"
                }).eq("node_id", node_id).execute()

                print(f"[MQTT] Node {node_id} ({mac_address}) marked as {'active' if is_active else 'inactive'}.")
            else:
                print(f"[MQTT] MAC {mac_address} not found in DB (registration failed)")



           
    except json.JSONDecodeError:
        print("[MQTT ERROR] Payload was not valid JSON.")
    except Exception as e:
        print(f"[MQTT ERROR] {e}")




def start_mqtt_listener():
    try:
        if not all([MQTT_BROKER, MQTT_USERNAME, MQTT_PASSWORD]):
            raise ValueError("Missing required MQTT environment variables")
        
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_disconnect = on_disconnect  # Add this
        
        result = mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
        if result != 0:
            raise ConnectionError(f"Failed to connect to MQTT broker: {result}")
            
        mqtt_client.loop_start()
        print("[MQTT] Client started successfully")
        
    except Exception as e:
        print(f"[MQTT ERROR] Failed to start: {e}")
        raise
def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnected with result code {rc}")
