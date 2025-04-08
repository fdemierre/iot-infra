from flask import Flask, render_template_string
import subprocess
from influxdb_client import InfluxDBClient
import os
from dotenv import load_dotenv

load_dotenv("/opt/iot-infra/.env")

app = Flask(__name__)

INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")

STATUS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Status Système</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: #007BFF; }
        pre { background: #f0f0f0; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>✨ État du système</h1>
    <h2>🔌 Service MQTT Listener</h2>
    <pre>{{ mqtt_status }}</pre>
    <h2>📊 InfluxDB</h2>
    <pre>{{ influx_status }}</pre>
</body>
</html>
"""

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

            query = f'''from(bucket: "{buckets[0].name}")
              |> range(start: -30d)
              |> count()'''
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
    return render_template_string(STATUS_TEMPLATE, mqtt_status=mqtt_status, influx_status=influx_status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
