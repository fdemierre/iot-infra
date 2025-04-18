# -*- coding: utf-8 -*-
# Décoder DL‑IAM (Decentlab Indoor Ambiance Monitor)
import base64
import struct

PROTOCOL_VERSION = 2

# Capteurs selon le constructeur Decentlab
SENSORS = [
    {'length': 1,
     'values': [
         ('battery_voltage',       lambda x: x[0] / 1000)
     ]},
    {'length': 2,
     'values': [
         ('air_temperature',       lambda x: 175 * x[0] / 65535 - 45),
         ('air_humidity',          lambda x: 100 * x[1] / 65535)
     ]},
    {'length': 1,
     'values': [
         ('barometric_pressure',   lambda x: x[0] * 2)
     ]},
    {'length': 2,
     'values': [
         ('ambient_light_visible_infrared', lambda x: x[0]),
         ('ambient_light_infrared',         lambda x: x[1]),
         ('illuminance',                    lambda x: max(
             max(1.0 * x[0] - 1.64 * x[1], 0.59 * x[0] - 0.86 * x[1]),
             0
         ) * 1.5504)
     ]},
    {'length': 3,
     'values': [
         ('co2_concentration',    lambda x: x[0] - 32768),
         ('co2_sensor_status',    lambda x: x[1]),
         ('raw_ir_reading',       lambda x: x[2])
     ]},
    {'length': 1,
     'values': [
         ('activity_counter',     lambda x: x[0])
     ]},
    {'length': 1,
     'values': [
         ('total_voc',            lambda x: x[0])
     ]}
]

def decode(frm_payload):
    """
    :param frm_payload: chaîne Base64 du payload brut
    :return: dict des mesures
    """
    try:
        raw = base64.b64decode(frm_payload)
        # protocole
        version = raw[0]
        if version != PROTOCOL_VERSION:
            raise ValueError(f"Protocol version {version} inattendue, attendu {PROTOCOL_VERSION}")
        # ID appareil + flags
        device_id = struct.unpack('>H', raw[1:3])[0]
        flags     = struct.unpack('>H', raw[3:5])[0]
        # découpés en mots de 16 bits
        words = [
            struct.unpack('>H', raw[i:i+2])[0]
            for i in range(5, len(raw), 2)
        ]
        # lecture conditionnelle via flags
        cursor = 0
        result = {
            'protocol_version': version,
            'device_id':        device_id,
            'flags':            flags
        }
        for bit, sensor in enumerate(SENSORS):
            if not (flags & (1 << bit)):
                continue
            chunk = words[cursor:cursor + sensor['length']]
            cursor += sensor['length']
            for key, conv in sensor['values']:
                try:
                    result[key] = conv(chunk)
                except Exception as e:
                    raise ValueError(f"Erreur conversion {key}: {e}")
        return result

    except Exception as e:
        raise Exception(f"Erreur dans le décodeur DL‑IAM: {e}")
