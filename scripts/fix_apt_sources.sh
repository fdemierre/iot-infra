#!/bin/bash
echo "🔧 Désactivation temporaire des dépôts tiers problématiques (ex: InfluxDB pour noble)"

# Désactive le dépôt InfluxDB si présent
if [ -f /etc/apt/sources.list.d/influxdb.list ]; then
    sudo mv /etc/apt/sources.list.d/influxdb.list /etc/apt/sources.list.d/influxdb.list.disabled
    echo "✔️  Dépôt InfluxDB désactivé"
fi

# Recharge proprement les sources APT
sudo apt update
