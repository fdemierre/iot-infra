#!/usr/bin/env python3
import os
import json
import base64
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WriteOptions
from dotenv import load_dotenv
from importlib import import_module

# 📦 Charger les variables d'environnement
load_dotenv("/opt/iot-infra/.env")

MQTT_HOST = os.getenv("MQTT_HOST")
TTN_USERNAME = os.getenv("TTN_USERNAME")
TTN_PASSWORD = os.getenv("TTN_PASSWORD")

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# 📁 Charger les devices connus
DEVICES_FILE = "/opt/iot-infra/devices.json"
if os.path.exists(DEVICES_FILE):
    with open(DEVICES_FILE, "r") as f:
        DEVICES = json.load(f)
else:
    DEVICES = {}

# 📨 Callback de réception MQTT
def on_message(client, userdata, msg):
    try:
        print(f"🔎 Message brut reçu:\n{msg.payload.decode()}")
        payload = json.loads(msg.payload)
        dev_eui = payload["end_device_ids"]["dev_eui"]
        raw = payload["uplink_message"].get("frm_payload")

        if dev_eui not in DEVICES:
            print(f"❌ DevEUI inconnu : {dev_eui}")
            return

        decoder_name = DEVICES[dev_eui]
        decoder_path = f"decoders.{decoder_name}"
        decoder = import_module(decoder_path)

        if not raw:
            print(f"⚠️ frm_payload vide ou manquant pour {dev_eui}")
            return

        print(f"📦 frm_payload reçu pour {dev_eui}: {raw}")

        try:
            # Normaliser base64 en forçant le bon padding
            raw += '=' * (-len(raw) % 4)
            bytes_data = base64.b64decode(raw)
        except Exception as e:
            print(f"❌ Base64 decode failed: {e}")
            return

        decoded = decoder.decode(bytes_data)

        if not decoded:
            print(f"⚠️ Aucun champ décodé pour {dev_eui}")
            return

        print(f"📥 {dev_eui} → {decoded}")

        # Envoi vers InfluxDB
        write_points(dev_eui, decoded)

    except Exception as e:
        print(f"❌ Erreur: {e}")

# 💾 Écriture dans InfluxDB
def write_points(dev_eui, fields):
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            write_api = client.write_api(write_options=WriteOptions(batch_size=1))
            point = Point("iot")
            point.tag("dev_eui", dev_eui)
            for key, value in fields.items():
                if isinstance(value, (int, float)):
                    point.field(key, value)
            write_api.write(bucket=INFLUX_BUCKET, record=point)
    except Exception as e:
        print(f"❌ InfluxDB write error: {e}")

# 🚀 Initialisation MQTT
client = mqtt.Client()
client.username_pw_set(TTN_USERNAME, TTN_PASSWORD)
client.on_message = on_message

print(f"📡 Connexion MQTT à {MQTT_HOST}...")
client.connect(MQTT_HOST, 1883, 60)

topic = f"v3/{TTN_USERNAME}/devices/+/up"
print(f"📡 Abonnement au topic: {topic}")
client.subscribe(topic)

client.loop_forever()
