#!/bin/bash
set -e

echo "📦 Installation d'InfluxDB 2 via APT (dépôt jammy utilisé)"

# Crée les répertoires nécessaires
sudo mkdir -p /etc/apt/keyrings

# Télécharger la clé publique officielle d'InfluxData (clé actuelle D8FF8E1F7DF8B07E)
curl -fsSL https://repos.influxdata.com/influxdata-archive_compat.key | \
  gpg --dearmor | sudo tee /etc/apt/keyrings/influxdb-archive-keyring.gpg > /dev/null

# Ajouter le dépôt pour Ubuntu 22.04 (jammy)
echo "deb [signed-by=/etc/apt/keyrings/influxdb-archive-keyring.gpg] https://repos.influxdata.com/ubuntu jammy stable" | \
  sudo tee /etc/apt/sources.list.d/influxdb.list > /dev/null

# Mise à jour + installation
sudo apt update
sudo apt install -y influxdb2

# Activer et démarrer le service
sudo systemctl enable influxdb
sudo systemctl start influxdb

echo "✅ InfluxDB installé et lancé"
