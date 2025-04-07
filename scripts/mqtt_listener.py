#!/usr/bin/env python3

import json
import base64
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os
from influxdb_client import InfluxDBClient, Point
from datetime import datetime
import importlib

load_dotenv()

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_USERNAME = os.getenv("TTN_USERNAME")
MQTT_PASSWORD = os.getenv("TTN_PASSWORD")
MQTT_TOPIC = f"v3/{MQTT_USERNAME}/devices/+/up"

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")
INFLUX_ORG = os.getenv("INFLUX_ORG")

def load_devices():
    with open("devices.json", "r") as f:
        return json.load(f)

def decode(dev_eui, payload):
    devices = load_devices()
    capteur_type = devices.get(dev_eui)
    if not capteur_type:
        print(f"❌ Capteur non reconnu : {dev_eui}")
        return None
    try:
        module = importlib.import_module(f"decoders.{capteur_type}")
        return module.decode(payload)
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
    except Exception as e:
        print(f"❌ Erreur réception MQTT : {e}")

def send_to_influx(dev_eui, data, timestamp):
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = client.write_api()
    for key, value in data.items():
        point = Point(key).tag("dev_eui", dev_eui).field("value", value).time(timestamp)
        write_api.write(bucket=INFLUX_BUCKET, record=point)

client = mqtt.Client()
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.on_message = on_message

print(f"📡 Connexion MQTT à {MQTT_HOST}...")
client.connect(MQTT_HOST, 1883, 60)
client.subscribe(MQTT_TOPIC)
client.loop_forever()
