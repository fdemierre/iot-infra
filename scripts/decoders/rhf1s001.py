def decode(payload_b64):
    """
    Décode le payload du capteur rhf1s001.
    
    La fonction s'attend à recevoir une chaîne Base64 (payload_b64) envoyée
    par le listener. Elle effectue le décodage Base64 puis extrait :
      - La température (calculée à partir des octets 1 et 2)
      - L'humidité (octet 3)
      - La période (octets 4-5)
      - La batterie (octet 8)
    
    Retourne:
        Un dictionnaire de la forme :
        {
          "temp": "XX.XX", 
          "hum": "XX.XX",
          "period": "XX sec",
          "battery": "XX.XX"
        }
    
    Remarque: Cette fonction correspond à la logique JavaScript suivante:
    
    function Decoder(bytes, port) {
      var obj = new Object();
      
      //temp
      var tempEncoded = (bytes[2]<<8)|(bytes[1]);
      var tempDecoded = (tempEncoded*175.72/65536)-46.85;
      obj.temp = tempDecoded.toFixed(2);
      
      //humidity
      var humEncoded = bytes[3];
      var humDecoded = (humEncoded*125/256)-6;
      obj.hum = humDecoded.toFixed(2);
      
      //period
      var periodEncoded = (bytes[5]<<8)|(bytes[4]);
      var periodDecoded = periodEncoded * 2;
      obj.period = periodDecoded + " sec";
      
      //battery
      var batteryEncoded = bytes[8];
      var batteryDecoded = (batteryEncoded+150)*0.01;
      obj.battery = batteryDecoded.toFixed(2);
      
      return obj;
    }
    """
    import base64
    try:
        # Décodage de la chaîne base64 en bytes.
        # On ajoute le padding nécessaire si besoin.
        payload_b64 = payload_b64.strip()
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_bytes = base64.b64decode(payload_b64, validate=False)
    except Exception as e:
        raise Exception(f"Erreur lors du décodage Base64: {e}")
    
    # Convertir le payload en une liste d'entiers pour faciliter le traitement
    b = list(payload_bytes)
    decoded = {}
    offset = 0

    if offset + 1 <= len(b):
        status = b[offset]
        offset += 1

        # Température : (bytes[2] << 8) | bytes[1]
        if offset + 1 <= len(b):
            try:
                temp_encoded = (b[2] << 8) | b[1]
            except Exception as e:
                raise Exception(f"Erreur lors du décodage de la température : {e}")
            temp_decoded = (temp_encoded * 175.72 / 65536) - 46.85
            decoded["temp"] = f"{temp_decoded:.2f}"
            offset += 1
        
        # Humidité : octet 3
        if len(b) > 3:
            hum_encoded = b[3]
            hum_decoded = (hum_encoded * 125 / 256) - 6
            decoded["hum"] = f"{hum_decoded:.2f}"
        
        # Période : (bytes[5] << 8) | bytes[4]
        if len(b) >= 6:
            period_encoded = (b[5] << 8) | b[4]
            period_decoded = period_encoded * 2
            decoded["period"] = f"{period_decoded} sec"
        
        # Batterie : octet 8
        if len(b) >= 9:
            battery_encoded = b[8]
            battery_decoded = (battery_encoded + 150) * 0.01
            decoded["battery"] = f"{battery_decoded:.2f}"
    
    return decoded


# Test du décodeur (optionnel)
if __name__ == "__main__":
    # Exemple de payload Base64 (à adapter avec un vrai exemple)
    # Par exemple, avec le payload de ton message:
    # "jhepBhBY" ou "ngdGRDRQAGOVgDceAA+X" – adapte l'exemple suivant
    exemple_payload = "jhepBhBY"
    try:
        result = decode(exemple_payload)
        print("Données décodées:", result)
    except Exception as e:
        print("Erreur lors du décodage:", e)
