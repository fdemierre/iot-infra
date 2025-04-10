#!/usr/bin/env python3
import os
import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.exceptions import InfluxDBError
from dotenv import load_dotenv
from importlib import import_module
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Charger les variables d'environnement depuis /opt/iot-infra/.env
load_dotenv("/opt/iot-infra/.env")

MQTT_HOST    = os.getenv("MQTT_HOST")
TTN_USERNAME = os.getenv("TTN_USERNAME")
TTN_PASSWORD = os.getenv("TTN_PASSWORD")

INFLUX_URL    = os.getenv("INFLUX_URL")
INFLUX_TOKEN  = os.getenv("INFLUX_TOKEN")
INFLUX_ORG    = os.getenv("INFLUX_ORG")
# INFLUX_BUCKET n'est plus utilisé, car on crée un bucket par type de capteur

# Charger les devices connus depuis /opt/iot-infra/devices.json
DEVICES_FILE  = "/opt/iot-infra/devices.json"
if os.path.exists(DEVICES_FILE):
    try:
        with open(DEVICES_FILE, "r") as f:
            DEVICES = json.load(f)
        logging.info(f"Devices chargés depuis {DEVICES_FILE}: {DEVICES}")
    except json.JSONDecodeError as e:
        logging.error(f"Erreur lors de la lecture de {DEVICES_FILE}: {e}")
        DEVICES = {}
else:
    logging.warning(f"Fichier de devices non trouvé: {DEVICES_FILE}")
    DEVICES = {}

# Fonction pour obtenir (et créer si nécessaire) un bucket dans InfluxDB pour un type de capteur
def get_or_create_bucket(bucket_name: str):
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            buckets_api = client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(bucket_name)
            if bucket is None:
                bucket = buckets_api.create_bucket(bucket_name=bucket_name, org=INFLUX_ORG)
                logging.info(f"✅ Bucket '{bucket_name}' créé.")
            else:
                logging.info(f"ℹ️ Bucket '{bucket_name}' déjà existant.")
            return bucket.name
    except InfluxDBError as e:
        logging.error(f"❌ Erreur lors de la création/récupération du bucket '{bucket_name}': {e}")
        return None

# Callback de réception MQTT
def on_message(client, userdata, msg):
    try:
        raw_msg = msg.payload.decode()
        logging.info(f"Message MQTT reçu sur le topic '{msg.topic}':\n{raw_msg}")
        payload = json.loads(raw_msg)
        dev_eui = payload["end_device_ids"]["dev_eui"]
        uplink = payload["uplink_message"]
        frm_payload = uplink.get("frm_payload")
        
        # Filtrage par f_port (ici on traite uniquement les messages sur le port 1)
        #fport = uplink.get("f_port", 0)
        #if fport != 1:
        #    logging.info(f"Ignoré message sur le port {fport} pour {dev_eui}")
        #    return
        
        if dev_eui not in DEVICES:
            logging.warning(f"DevEUI inconnu : {dev_eui}")
            return
        
        # Importer dynamiquement le module de décodage correspondant au type de capteur
        decoder_name = DEVICES[dev_eui]
        try:
            decoder_module = import_module(f"decoders.{decoder_name}")
        except ImportError as e:
            logging.error(f"Impossible d'importer le décodeur '{decoder_name}' pour {dev_eui}: {e}")
            return
        
        if not frm_payload:
            logging.warning(f"frm_payload vide ou manquant pour {dev_eui}")
            return
        
        logging.info(f"frm_payload reçu pour {dev_eui}: {frm_payload}")
        
        # Ici, on ne fait **pas** de décodage Base64 : on passe la chaîne directement au décodeur
        try:
            decoded = decoder_module.decode(frm_payload)
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution du décodeur '{decoder_name}' pour {dev_eui}: {e}")
            return
        
        if not decoded:
            logging.warning(f"Aucun champ décodé pour {dev_eui}")
            return
        
        logging.info(f"Données décodées pour {dev_eui} → {decoded}")
        
        # Écrire les données dans InfluxDB dans le bucket associé au type de capteur
        write_points(dev_eui, decoded)
        
    except Exception as e:
        logging.error(f"Erreur dans on_message: {e}")

# Fonction d'écriture dans InfluxDB dans le bucket associé au type de capteur
def write_points(dev_eui, fields):
    sensor_type = DEVICES.get(dev_eui)
    if not sensor_type:
        logging.error(f"Type de capteur non trouvé pour {dev_eui}")
        return
    bucket_name = get_or_create_bucket(sensor_type)
    if not bucket_name:
        logging.error(f"Impossible d'obtenir ou de créer le bucket pour {sensor_type}")
        return
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            write_api = client.write_api(write_options=WriteOptions(batch_size=1))
            point = Point("iot").tag("dev_eui", dev_eui)
            for key, value in fields.items():
                if isinstance(value, (int, float)):
                    point.field(key, float(value))
            write_api.write(bucket=bucket_name, record=point)
            logging.info(f"Données écrites dans le bucket '{bucket_name}' pour {dev_eui}: {fields}")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture dans InfluxDB: {e}")

# Initialisation MQTT
client = mqtt.Client()
client.username_pw_set(TTN_USERNAME, TTN_PASSWORD)
client.on_message = on_message

logging.info(f"Connexion MQTT à {MQTT_HOST}...")
try:
    client.connect(MQTT_HOST, 1883, 60)
except Exception as e:
    logging.error(f"Erreur de connexion MQTT: {e}")
    exit(1)

topic = f"v3/{TTN_USERNAME}/devices/+/up"
logging.info(f"Abonnement au topic: {topic}")
client.subscribe(topic)

client.loop_forever()
