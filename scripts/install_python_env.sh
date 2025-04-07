#!/bin/bash
# install_python_env.sh

set -e

echo "📦 Installation des dépendances Python"

sudo apt update
sudo apt install -y python3 python3-pip python3-venv

echo "🧪 Création de l'environnement virtuel"
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install paho-mqtt influxdb-client python-dotenv

echo "✅ Environnement Python prêt"
