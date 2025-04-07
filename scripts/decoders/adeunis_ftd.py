def decode(payload_b64):
    import base64
    b = list(base64.b64decode(payload_b64))
    decoded = {}
    offset = 0

    if offset + 1 <= len(b):
        status = b[offset]
        offset += 1

        if status & 0x80 and offset + 1 <= len(b):
            temperature = b[offset]
            if temperature > 127:
                temperature -= 256
            decoded["temperature"] = temperature
            offset += 1

        if status & 0x40:
            decoded["trigger"] = "accelerometer"
        if status & 0x20:
            decoded["trigger"] = "pushbutton"

        if status & 0x10 and offset + 9 <= len(b):
            latDeg10   = b[offset] >> 4
            latDeg1    = b[offset] & 0x0F
            latMin10   = b[offset+1] >> 4
            latMin1    = b[offset+1] & 0x0F
            latMin01   = b[offset+2] >> 4
            latMin001  = b[offset+2] & 0x0F
            latMin0001 = b[offset+3] >> 4
            latSign    = -1 if (b[offset+3] & 0x01) else 1
            decoded["latitude"] = latSign * (
                latDeg10 * 10 + latDeg1 +
                (latMin10 * 10 + latMin1 + latMin01 * 0.1 + latMin001 * 0.01 + latMin0001 * 0.001) / 60
            )

            lonDeg100  = b[offset+4] >> 4
            lonDeg10   = b[offset+4] & 0x0F
            lonDeg1    = b[offset+5] >> 4
            lonMin10   = b[offset+5] & 0x0F
            lonMin1    = b[offset+6] >> 4
            lonMin01   = b[offset+6] & 0x0F
            lonMin001  = b[offset+7] >> 4
            lonSign    = -1 if (b[offset+7] & 0x01) else 1
            decoded["longitude"] = lonSign * (
                lonDeg100 * 100 + lonDeg10 * 10 + lonDeg1 +
                (lonMin10 * 10 + lonMin1 + lonMin01 * 0.1 + lonMin001 * 0.01) / 60
            )

            decoded["sats"] = b[offset + 8] & 0x0F
            decoded["altitude"] = 0
            offset += 9

        if status & 0x08 and offset + 1 <= len(b):
            decoded["uplink"] = b[offset]
            offset += 1
        if status & 0x04 and offset + 1 <= len(b):
            decoded["downlink"] = b[offset]
            offset += 1

        if status & 0x02 and offset + 2 <= len(b):
            decoded["battery"] = b[offset] << 8 | b[offset + 1]
            offset += 2

        if status & 0x01 and offset + 2 <= len(b):
            decoded["rssi"] = -b[offset]
            snr = b[offset + 1]
            decoded["snr"] = snr - 256 if snr > 127 else snr
            offset += 2

    return decoded
