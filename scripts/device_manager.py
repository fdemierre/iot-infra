from flask import Flask, render_template_string, request, redirect, url_for
import os
import json
import subprocess
from importlib import import_module
from influxdb_client import InfluxDBClient
from dotenv import load_dotenv

load_dotenv("/opt/iot-infra/.env")

app = Flask(__name__)

DEVICES_FILE = "/opt/iot-infra/devices.json"
DECODERS_DIR = "/opt/iot-infra/decoders"
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")

NAVBAR = """
<nav>
  <a href="/">Gérer les capteurs</a> |
  <a href="/status">Etat système</a> |
  <a href="/restart-listener">🔄 Redémarrer listener</a>
</nav>
<hr>
"""

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Gestion des capteurs</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background-color: #f5f5f5; }
        input, select, button { padding: 8px; margin: 4px 0; width: 100%; box-sizing: border-box; }
        form { max-width: 400px; margin-bottom: 30px; }
    </style>
</head>
<body>
    {{ navbar|safe }}
    <h1>🛠️ Gestion des capteurs</h1>
    <form method="post">
        <label for="dev_eui">DevEUI:</label>
        <input type="text" name="dev_eui" required pattern="[A-F0-9]{16}" placeholder="ex: 0018B200000023E6">
        <label for="decoder">Type de capteur:</label>
        <select name="decoder">
            {% for decoder in decoders %}
            <option value="{{ decoder }}">{{ decoder }}</option>
            {% endfor %}
        </select>
        <button type="submit">Ajouter</button>
    </form>
    <h2>Liste des capteurs</h2>
    <table>
        <tr><th>DevEUI</th><th>Type</th><th>Action</th></tr>
        {% for dev_eui, decoder in devices.items() %}
        <tr>
            <td>{{ dev_eui }}</td>
            <td>{{ decoder }}</td>
            <td><a href="/delete/{{ dev_eui }}">Supprimer</a></td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

STATUS_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>État du système</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #007BFF; }
        pre { background: #f0f0f0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    {{ navbar|safe }}
    <h1>✨ État du système</h1>
    <h2>🔌 Service MQTT Listener</h2>
    <pre>{{ mqtt_status }}</pre>
    <h2>📊 InfluxDB</h2>
    <pre>{{ influx_status }}</pre>
</body>
</html>
"""

def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_devices(devices):
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=2)

def get_available_decoders():
    return [f.replace(".py", "") for f in os.listdir(DECODERS_DIR) if f.endswith(".py")]

@app.route("/", methods=["GET", "POST"])
def index():
    devices = load_devices()
    if request.method == "POST":
        dev_eui = request.form["dev_eui"].upper()
        decoder = request.form["decoder"]
        devices[dev_eui] = decoder
        save_devices(devices)
        return redirect(url_for("index"))
    decoders = get_available_decoders()
    return render_template_string(INDEX_TEMPLATE, devices=devices, decoders=decoders, navbar=NAVBAR)

@app.route("/delete/<dev_eui>")
def delete(dev_eui):
    devices = load_devices()
    if dev_eui in devices:
        del devices[dev_eui]
        save_devices(devices)
    return redirect(url_for("index"))

@app.route("/restart-listener")
def restart_listener():
    try:
        subprocess.run(["sudo", "systemctl", "restart", "mqtt_listener"], check=True)
        return redirect(url_for("status"))
    except subprocess.CalledProcessError as e:
        return f"Erreur lors du redémarrage: {e}"

def get_mqtt_status():
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "mqtt_listener"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Erreur: {e}"

def get_influx_status():
    try:
        with InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
            buckets = client.buckets_api().find_buckets().buckets
            bucket_info = [f"{b.name} - {b.retention_rules[0].every_seconds}s - ID: {b.id}" for b in buckets]
            query = f'''from(bucket: "{buckets[0].name}") |> range(start: -30d) |> count()'''
            query_api = client.query_api()
            tables = query_api.query(query, org=INFLUX_ORG)
            total_points = sum(row.get_value() for table in tables for row in table.records)
            return f"Buckets:\n" + "\n".join(bucket_info) + f"\n\nNombre total de points: {total_points}"
    except Exception as e:
        return f"Erreur: {e}"

@app.route("/status")
def status():
    mqtt_status = get_mqtt_status()
    influx_status = get_influx_status()
    return render_template_string(STATUS_TEMPLATE, mqtt_status=mqtt_status, influx_status=influx_status, navbar=NAVBAR)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
