#!/bin/bash
source .env

echo "🧼 Réinitialisation du bucket InfluxDB : $INFLUX_BUCKET"

# Supprimer le bucket si existant
echo "🗑️ Suppression (ignore les erreurs)"
influx bucket delete --name "$INFLUX_BUCKET" --org "$INFLUX_ORG" --token "$INFLUX_TOKEN" 2>/dev/null || true

# Recréation
echo "➕ Recréation"
influx bucket create --name "$INFLUX_BUCKET" --org "$INFLUX_ORG" --token "$INFLUX_TOKEN"

echo "✅ Bucket recréé : $INFLUX_BUCKET"
