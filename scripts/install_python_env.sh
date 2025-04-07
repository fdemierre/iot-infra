#!/bin/bash
set -e

echo "📦 Installation des dépendances Python"

# Ne pas laisser échouer si un dépôt tiers est mal configuré
sudo apt update -o Dir::Etc::sourcelist="sources.list" \
                -o Dir::Etc::sourceparts="-" \
                -o APT::Get::List-Cleanup="0"

sudo apt install -y python3 python3-pip python3-venv

echo "🧪 Création de l'environnement virtuel"
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install paho-mqtt influxdb-client python-dotenv

echo "✅ Environnement Python prêt"
