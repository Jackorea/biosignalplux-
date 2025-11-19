import json

INPUT_PATH = "/Users/jackahn/Desktop/traitementMedi/SeongjagMarche (1)_segment_600_5800.txt"
OUTPUT_PATH = "/Users/jackahn/Desktop/traitementMedi/segment_600_5800_all_calibrated.json"

# Calibration fixe ACC
ACC_CAL = {
    "CH1": {"Cmin": 27584, "Cmax": 37720},  # axe X
    "CH2": {"Cmin": 27468, "Cmax": 37767},  # axe Y
}
ACC_FULL_SCALE_G = 3.6

# Métadonnées fixes
DEVICE_ID = "00:07:80:65:DF:99"
STUDENT_ID = "65923K"
SESSION_ID = "S1"
SEQUENCE_ID = 1
SEQUENCE_DATETIME = "2024-09-16 10:56:24"
SEQUENCE_CONTEXT = "MARCHE"
SEQUENCE_DESCRIPTION = "Prise de mesures effectuée au cours d'une marche à la rue de la l'ESIEE"


def lire_entete(path):
    """Lit l'en-tête OpenSignals et extrait les métadonnées.
    
    Retourne (fs, bits, device_id, datetime_str).
    """
    import json as _json
    fs = None
    bits = 16
    device_id = None
    datetime_str = None
    
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                if 'sampling rate' in line:
                    try:
                        obj = _json.loads(line.lstrip('#').strip())
                        # Le premier key est le device ID
                        first_key = next(iter(obj))
                        device_id = first_key
                        
                        inner = obj[first_key]
                        fs = float(inner.get('sampling rate'))
                        res = inner.get('resolution')
                        if isinstance(res, list) and res:
                            bits = int(res[0])
                        
                        # Extraire date et time
                        date = inner.get('date')
                        time = inner.get('time')
                        if date and time:
                            # Formater: "2025-9-19" + "9:48:37.952" -> "2025-09-19 09:48:37"
                            # Standardiser le format
                            try:
                                date_parts = date.split('-')
                                if len(date_parts) == 3:
                                    year, month, day = date_parts
                                    date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                
                                # Garder seulement HH:MM:SS (enlever millisecondes)
                                time_base = time.split('.')[0]
                                time_parts = time_base.split(':')
                                if len(time_parts) == 3:
                                    hour, minute, second = time_parts
                                    time_base = f"{hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}"
                                
                                datetime_str = f"{date} {time_base}"
                            except Exception:
                                datetime_str = f"{date} {time}" if date and time else None
                    except Exception:
                        pass
                if '# EndOfHeader' in line:
                    break
            else:
                break
    return fs, bits, device_id, datetime_str


def charger_colonne(path, ch):
    mapping = {"CH1": 2, "CH2": 3, "CH3": 4, "CH4": 5}
    idx = mapping[ch]
    vals = []
    with open(path, 'r') as f:
        in_data = False
        for line in f:
            if not in_data:
                if '# EndOfHeader' in line:
                    in_data = True
                continue
            if not line.strip():
                continue
            parts = line.rstrip('\n').split('\t')
            if len(parts) <= idx:
                continue
            try:
                vals.append(int(parts[idx]))
            except ValueError:
                continue
    return vals


def to_rip_percent(adc, bits):
    full = 2 ** bits
    return (adc / full - 0.5) * 100.0


def to_acc_g(adc, cmin, cmax, full_scale_g):
    if cmax == cmin:
        return 0.0
    return (((adc - cmin) / (cmax - cmin)) * 2.0 - 1.0) * full_scale_g


def main():
    # Lire les métadonnées du fichier
    fs, bits, device_id, datetime_str = lire_entete(INPUT_PATH)
    
    # Utiliser les valeurs extraites ou les valeurs par défaut si non trouvées
    final_device_id = device_id if device_id else DEVICE_ID
    final_datetime = datetime_str if datetime_str else SEQUENCE_DATETIME

    ch1_adc = charger_colonne(INPUT_PATH, "CH1")
    ch2_adc = charger_colonne(INPUT_PATH, "CH2")
    ch3_adc = charger_colonne(INPUT_PATH, "CH3")
    ch4_adc = charger_colonne(INPUT_PATH, "CH4")

    ch1_g = [to_acc_g(v, ACC_CAL['CH1']['Cmin'], ACC_CAL['CH1']['Cmax'], ACC_FULL_SCALE_G) for v in ch1_adc]
    ch2_g = [to_acc_g(v, ACC_CAL['CH2']['Cmin'], ACC_CAL['CH2']['Cmax'], ACC_FULL_SCALE_G) for v in ch2_adc]
    ch3_rip = [to_rip_percent(v, bits) for v in ch3_adc]
    ch4_rip = [to_rip_percent(v, bits) for v in ch4_adc]

    n = min(len(ch1_g), len(ch2_g), len(ch3_rip), len(ch4_rip))
    acc_vertical = ch1_g[:n]
    acc_horizontal = ch2_g[:n]
    resp_thorax = ch3_rip[:n]
    resp_abdomen = ch4_rip[:n]

    data_rows = []
    for i in range(n):
        data_rows.append([i, acc_vertical[i], acc_horizontal[i], resp_thorax[i], resp_abdomen[i]])

    out = {
        "deviceId": final_device_id,
        "studentId": STUDENT_ID,
        "sessionId": SESSION_ID,
        "sequenceId": SEQUENCE_ID,
        "sequenceStartDateTime": final_datetime,
        "sequenceContext": SEQUENCE_CONTEXT,
        "sequenceDescription": SEQUENCE_DESCRIPTION,
        "sequenceStructure": [
            "INDEX",
            "ACC_VERTICAL",
            "ACC_HORIZONTAL",
            "RESP_ABDOMEN",
            "RESP_THORAX"
        ],
        "sequenceSamplingRate": int(fs) if fs is not None else None,
        "sequenceResolution": bits,
        "data": data_rows
    }

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(out, f, ensure_ascii=False)

    print(f"Écrit: {OUTPUT_PATH} (échantillons: {n})")


if __name__ == '__main__':
    main()


