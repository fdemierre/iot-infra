import base64


def decode(frm_payload):
    """
    Decode Milesight WS301 uplink payload (Base64 encoded LoRaWAN FRM payload).
    Returns a dict with decoded fields.
    """
    try:
        # Decode base64-encoded payload to raw bytes
        payload = base64.b64decode(frm_payload)
        index = 0
        result = {}

        # Iterate through TLV-encoded payload
        while index < len(payload):
            channel_id = payload[index]
            index += 1
            channel_type = payload[index]
            index += 1

            # Battery (0x01, type 0x75)
            if channel_id == 0x01 and channel_type == 0x75:
                result["battery"] = payload[index]
                index += 1

            # Door/Window state (0x03, type 0x00)
            elif channel_id == 0x03 and channel_type == 0x00:
                result["magnet_status"] = "close" if payload[index] == 0 else "open"
                index += 1

            # Install (tamper) state (0x04, type 0x00)
            elif channel_id == 0x04 and channel_type == 0x00:
                result["tamper_status"] = "installed" if payload[index] == 0 else "uninstalled"
                index += 1

            else:
                # Unrecognized channel, stop parsing
                break

        return result

    except Exception as e:
        raise Exception(f"Erreur dans le décodeur WS301: {e}")
