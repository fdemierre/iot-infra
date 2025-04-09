#!/usr/bin/env python3

import os
import json
import base64
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from datetime import datetime
import importlib

from dotenv import load_dotenv
load_dotenv("/opt/iot-infra/.env")

MQTT_HOST = os.getenv("MQTT_HOST")
# Note : ici on utilise TTN_USERNAME comme MQTT_USERNAME (la variable se nomme TTN_USERNAME)
MQTT_USERNAME = os.getenv("TTN_USERNAME")
MQTT_PASSWORD = os.getenv("TTN_PASSWORD")
MQTT_TOPIC = f"v3/{MQTT_USERNAME}/devices/+/up"

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
INFLUX_ORG = os.getenv("INFLUX_ORG")

def load_devices():
    # Le fichier devices.json doit se trouver dans /opt/iot-infra
    with open("/opt/iot-infra/devices.json", "r") as f:
        return json.load(f)

def decode(dev_eui, payload_b64):
    devices = load_devices()
    capteur_type = devices.get(dev_eui)
    if not capteur_type:
        print(f"❌ Capteur non reconnu : {dev_eui}")
        return None
    try:
        module = importlib.import_module(f"decoders.{capteur_type}")
        return module.decode(payload_b64)
    except Exception as e:
        print(f"❌ Erreur décodage {capteur_type}: {e}")
        return None

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        dev_eui = data["end_device_ids"]["dev_eui"]
        payload_b64 = data["uplink_message"]["frm_payload"]
        timestamp = data["received_at"]

        decoded = decode(dev_eui, payload_b64)
        if decoded:
            print(f"📥 {dev_eui} → {decoded}")
            send_to_influx(dev_eui, decoded, timestamp)
        else:
            print(f"⚠️ Aucun champ décodé pour {dev_eui}")
    except Exception as e:
        print(f"❌ Erreur réception MQTT : {e}")

def send_to_influx(dev_eui, data, timestamp):
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api()
    for key, value in data.items():
        if isinstance(value, (int, float)):
            # Conversion forcée en float pour éviter les conflits de types
            val = float(value)
            # On utilise le timestamp tel quel (format ISO en général)
            point = Point(key).tag("dev_eui", dev_eui).field("value", val).time(timestamp)
            write_api.write(bucket=INFLUX_BUCKET, record=point)

client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_message = on_message

print(f"📡 Connexion MQTT à {MQTT_HOST}...")
client.connect(MQTT_HOST, 1883, 60)
client.subscribe(MQTT_TOPIC)
client.loop_forever()
