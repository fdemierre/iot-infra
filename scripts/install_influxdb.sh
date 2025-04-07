#!/bin/bash
set -e

echo "📦 Installation d'InfluxDB 2 via APT (dépôt jammy utilisé)"

# Ajout de la clé GPG et du dépôt (version Ubuntu 22.04 jammy compatible)
sudo mkdir -p /etc/apt/keyrings
curl -s https://repos.influxdata.com/influxdb.key | sudo gpg --dearmor -o /etc/apt/keyrings/influxdb-archive-keyring.gpg

echo "deb [signed-by=/etc/apt/keyrings/influxdb-archive-keyring.gpg] https://repos.influxdata.com/ubuntu jammy stable" | \
  sudo tee /etc/apt/sources.list.d/influxdb.list

sudo apt update
sudo apt install -y influxdb2

sudo systemctl enable influxdb
sudo systemctl start influxdb

echo "✅ InfluxDB installé et lancé"

