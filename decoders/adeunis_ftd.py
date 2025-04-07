# decoders/adeunis_ftd.py

def decode(payload_b64):
    import base64
    b = base64.b64decode(payload_b64)
    return {
        "temperature": b[0] + b[1] / 100,
        "rssi": b[2] - 256,
        "latitude": (b[3] << 8 | b[4]) / 100,
        "longitude": (b[5] << 8 | b[6]) / 100
    }
