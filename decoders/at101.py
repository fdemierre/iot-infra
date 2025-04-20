import base64


def decode(frm_payload):
    """
    Decode Milesight AT101 uplink payload (Base64 encoded LoRaWAN FRM payload).
    Returns a dict with decoded fields.
    """
    try:
        raw = base64.b64decode(frm_payload)
        decoded = {}
        i = 0
        while i < len(raw):
            channel_id = raw[i]
            channel_type = raw[i + 1]
            i += 2

            # Battery voltage (V)
            if channel_id == 0x01 and channel_type == 0x75:
                decoded["battery_voltage"] = raw[i] / 1000.0
                i += 1

            # Temperature (°C)
            elif channel_id == 0x03 and channel_type == 0x67:
                val = int.from_bytes(raw[i : i + 2], byteorder="little", signed=False)
                decoded["temperature"] = val / 10.0
                i += 2

            # Location + motion + geofence
            elif channel_id in (0x04, 0x84) and channel_type == 0x88:
                # Latitude and longitude in microdegrees
                lat_raw = int.from_bytes(raw[i : i + 4], byteorder="little", signed=True)
                lon_raw = int.from_bytes(raw[i + 4 : i + 8], byteorder="little", signed=True)
                status = raw[i + 8]
                decoded["latitude"] = round(lat_raw * 1e-6, 6)
                decoded["longitude"] = round(lon_raw * 1e-6, 6)
                decoded["motion_status"] = ["unknown", "start", "moving", "stop"][status & 0x0F]
                decoded["geofence_status"] = ["inside", "outside", "unset", "unknown"][status >> 4]
                i += 9

            # Tamper status
            elif channel_id == 0x07 and channel_type == 0x00:
                decoded["tamper_status"] = "install" if raw[i] == 0 else "uninstall"
                i += 1

            # Temperature with abnormal flag
            elif channel_id == 0x83 and channel_type == 0x67:
                val = int.from_bytes(raw[i : i + 2], byteorder="little", signed=False)
                decoded["temperature"] = val / 10.0
                decoded["temperature_abnormal"] = "normal" if raw[i + 2] == 0 else "abnormal"
                i += 3

            # Historical location
            elif channel_id == 0x20 and channel_type == 0xCE:
                ts = int.from_bytes(raw[i : i + 4], byteorder="little", signed=False)
                lon_raw = int.from_bytes(raw[i + 4 : i + 8], byteorder="little", signed=True)
                lat_raw = int.from_bytes(raw[i + 8 : i + 12], byteorder="little", signed=True)
                entry = {
                    "timestamp": ts,
                    "longitude": round(lon_raw * 1e-6, 6),
                    "latitude": round(lat_raw * 1e-6, 6),
                }
                decoded.setdefault("history", []).append(entry)
                i += 12

            else:
                # Unknown channel: stop parsing
                break

        return decoded

    except Exception as e:
        raise Exception(f"Erreur dans le décodeur AT101: {e}")
