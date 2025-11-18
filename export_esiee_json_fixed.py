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
    import json as _json
    meta = None
    fs = None
    bits = 16
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                if 'sampling rate' in line:
                    try:
                        obj = _json.loads(line.lstrip('#').strip())
                        first_key = next(iter(obj))
                        inner = obj[first_key]
                        fs = float(inner.get('sampling rate'))
                        res = inner.get('resolution')
                        if isinstance(res, list) and res:
                            bits = int(res[0])
                    except Exception:
                        pass
                if '# EndOfHeader' in line:
                    break
            else:
                break
    return fs, bits


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
    fs, bits = lire_entete(INPUT_PATH)

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
        "deviceId": DEVICE_ID,
        "studentId": STUDENT_ID,
        "sessionId": SESSION_ID,
        "sequenceId": SEQUENCE_ID,
        "sequenceStartDateTime": SEQUENCE_DATETIME,
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


