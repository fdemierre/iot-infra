#!/bin/bash
set -e

echo "📦 Installation d'InfluxDB 2 via APT (dépôt jammy utilisé)"

# Crée le dossier de clé s'il n'existe pas
sudo mkdir -p /etc/apt/keyrings

# Télécharge et installe correctement la clé GPG
curl -fsSL https://repos.influxdata.com/influxdb.key | gpg --dearmor | sudo tee /etc/apt/keyrings/influxdb.gpg > /dev/null

# Ajoute le dépôt jammy en pointant vers la clé correcte
echo "deb [signed-by=/etc/apt/keyrings/influxdb.gpg] https://repos.influxdata.com/ubuntu jammy stable" | \
  sudo tee /etc/apt/sources.list.d/influxdb.list > /dev/null

# Met à jour les paquets
sudo apt update

# Installe InfluxDB
sudo apt install -y influxdb2

# Active et démarre le service
sudo systemctl enable influxdb
sudo systemctl start influxdb

echo "✅ InfluxDB installé et lancé"
