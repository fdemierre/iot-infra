#!/bin/bash
source .env

# Supprimer le bucket
echo "🗑️ Suppression du bucket InfluxDB: $INFLUX_BUCKET"
influx bucket delete \
  --name "$INFLUX_BUCKET" \
  --org "$INFLUX_ORG" \
  --token "$INFLUX_TOKEN"

# Recréer le bucket (optionnel)
echo "➕ Recréation du bucket"
influx bucket create \
  --name "$INFLUX_BUCKET" \
  --org "$INFLUX_ORG" \
  --token "$INFLUX_TOKEN"
