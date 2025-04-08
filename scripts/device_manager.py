from flask import Flask, render_template_string, request, redirect, url_for
import os
import json
import re
import subprocess
from pathlib import Path

app = Flask(__name__)

DEVICES_FILE = Path("devices.json")
DECODER_DIR = Path("decoders")

# Template HTML minimal
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Device Manager</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="p-4">
    <div class="container">
        <h1 class="mb-4">📡 Device Manager</h1>
        <form method="POST" class="row g-3">
            <div class="col-md-6">
                <label for="dev_eui" class="form-label">DevEUI</label>
                <input type="text" class="form-control" id="dev_eui" name="dev_eui" required>
            </div>
            <div class="col-md-6">
                <label for="device_type" class="form-label">Type de capteur</label>
                <select class="form-select" id="device_type" name="device_type" required>
                    {% for d in decoders %}
                    <option value="{{ d }}">{{ d }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="col-12">
                <button type="submit" class="btn btn-primary">Ajouter le capteur</button>
            </div>
        </form>

        <hr>
        <h3>📋 Devices enregistrés</h3>
        <table class="table table-striped">
            <thead><tr><th>DevEUI</th><th>Type</th><th></th></tr></thead>
            <tbody>
            {% for dev, typ in devices.items() %}
            <tr>
                <td>{{ dev }}</td>
                <td>{{ typ }}</td>
                <td><a href="/delete/{{ dev }}" class="btn btn-sm btn-danger">Supprimer</a></td>
            </tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

# Charger les devices

def load_devices():
    if DEVICES_FILE.exists():
        with open(DEVICES_FILE) as f:
            return json.load(f)
    return {}

def save_devices(devices):
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=2)

# Créer un bucket InfluxDB

def create_bucket(bucket_name):
    result = subprocess.run([
        "influx", "bucket", "create",
        "--name", bucket_name,
        "--org", os.getenv("INFLUX_ORG", "iot-org"),
        "--token", os.getenv("INFLUX_TOKEN", "")
    ], capture_output=True)
    return result.returncode == 0

@app.route("/", methods=["GET", "POST"])
def index():
    devices = load_devices()
    decoders = [f.stem for f in DECODER_DIR.glob("*.py") if f.is_file()]

    if request.method == "POST":
        dev_eui = request.form.get("dev_eui", "").strip().upper()
        device_type = request.form.get("device_type", "")

        if not re.fullmatch(r"[0-9A-F]{16}", dev_eui):
            return "<h3>❌ DevEUI invalide (16 caractères hex)</h3><a href='/'>Retour</a>"

        devices[dev_eui] = device_type
        save_devices(devices)
        create_bucket(device_type)

        return redirect(url_for("index"))

    return render_template_string(TEMPLATE, devices=devices, decoders=decoders)

@app.route("/delete/<dev_eui>")
def delete(dev_eui):
    devices = load_devices()
    if dev_eui in devices:
        del devices[dev_eui]
        save_devices(devices)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
