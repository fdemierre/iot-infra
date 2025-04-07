#!/bin/bash
set -e

echo "📦 Installation d'InfluxDB 2 via APT (mode legacy clé GPG)"

# Télécharger la clé GPG classique et l'enregistrer dans trusted.gpg.d
curl -fsSL https://repos.influxdata.com/influxdata-archive_compat.key | \
  gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata.gpg > /dev/null

# Ajouter le dépôt jammy manuellement
echo "deb https://repos.influxdata.com/ubuntu jammy stable" | \
  sudo tee /etc/apt/sources.list.d/influxdb.list > /dev/null

# Update et install
sudo apt update
sudo apt install -y influxdb2

# Activer + lancer
sudo systemctl enable influxdb
sudo systemctl start influxdb

echo "✅ InfluxDB installé et fonctionnel 🎉"
