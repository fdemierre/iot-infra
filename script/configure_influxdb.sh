# configure_influxdb.sh

source .env

influx setup -u "$INFLUX_USER" -p "$INFLUX_PWD" \
  -o "$INFLUX_ORG" -b "$INFLUX_BUCKET" \
  -t "generated-token-placeholder" \
  -f || true

echo "INFLUX_TOKEN=generated-token-placeholder" >> .env
