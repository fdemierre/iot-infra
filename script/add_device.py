# add_device.py

#!/usr/bin/env python3
import json
import os
from pathlib import Path

devices_path = Path("devices.json")

def load_devices():
    if devices_path.exists():
        with open(devices_path, "r") as f:
            return json.load(f)
    return {}

def save_devices(devices):
    with open(devices_path, "w") as f:
        json.dump(devices, f, indent=4)

print("➕ Ajouter un device")
dev_eui = input("dev_eui (ex: AABBCCDDEEFF0011): ").strip()
type_capteur = input("Type de capteur (ex: adeunis_ftd): ").strip()

devices = load_devices()
devices[dev_eui] = type_capteur
save_devices(devices)

print(f"✅ Device {dev_eui} ajouté comme '{type_capteur}'")
