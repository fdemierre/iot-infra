import base64

def decode(frm_payload):
    try:
        payload = base64.b64decode(frm_payload)
        index = 0
        result = {}

        while index < len(payload) - 1:
            channel_id = payload[index]
            channel_type = payload[index + 1]
            index += 2

            # Batterie (%)
            if channel_id == 0x01 and channel_type == 0x75:
                result["battery"] = payload[index]
                index += 1

            # Température (°C)
            elif channel_id == 0x03 and channel_type == 0x67:
                temp_raw = int.from_bytes(payload[index:index+2], byteorder="little", signed=True)
                result["temperature"] = temp_raw / 10
                index += 2

            # Humidité (%)
            elif channel_id == 0x04 and channel_type == 0x68:
                result["humidity"] = payload[index] / 2
                index += 1

            # CO2 (ppm)
            elif channel_id == 0x05 and channel_type == 0x7D:
                result["co2"] = int.from_bytes(payload[index:index+2], byteorder="little")
                index += 2

            # PIR (occupancy)
            elif channel_id == 0x06 and channel_type == 0x00:
                result["pir"] = payload[index]
                index += 1

            # Lumière (Lux)
            elif channel_id == 0x07 and channel_type == 0xCB:
                result["light"] = int.from_bytes(payload[index:index+2], byteorder="little")
                index += 2

            # TVOC (ppb)
            elif channel_id == 0x08 and channel_type == 0x7D:
                result["tvoc"] = int.from_bytes(payload[index:index+2], byteorder="little")
                index += 2

            else:
                # Canal inconnu, on saute à la valeur suivante
                index += 1

        return result

    except Exception as e:
        raise Exception(f"Erreur dans le décodeur AM100: {e}")
