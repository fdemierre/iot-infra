#!/bin/bash
set -e

echo "📦 Installation des dépendances Python (sans dépendre des dépôts tiers)"

# Supprime temporairement le dépôt InfluxDB s’il existe
if grep -q "influxdata" /etc/apt/sources.list.d/influxdb.list 2>/dev/null; then
  echo "🔧 Suppression temporaire du dépôt InfluxDB pour éviter les erreurs apt"
  sudo mv /etc/apt/sources.list.d/influxdb.list /etc/apt/sources.list.d/influxdb.list.disabled
fi

sudo apt update
sudo apt install -y python3 python3-pip python3-venv

echo "🧪 Création de l'environnement virtuel"
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install paho-mqtt influxdb-client python-dotenv

echo "✅ Environnement Python prêt"

# On réactive le dépôt InfluxDB si on l’avait désactivé
if [ -f /etc/apt/sources.list.d/influxdb.list.disabled ]; then
  sudo mv /etc/apt/sources.list.d/influxdb.list.disabled /etc/apt/sources.list.d/influxdb.list
fi
