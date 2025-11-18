import argparse
import json
from typing import Tuple, Optional


def lire_entete(path: str) -> Tuple[Optional[dict], int]:
    """Lit l'en-tête OpenSignals (ligne JSON après '# ') et retourne (meta, header_lines_count).
    Si non présent, retourne (None, 0).
    """
    meta = None
    header_lines = 0
    try:
        with open(path, 'r') as f:
            for line in f:
                header_lines += 1
                if not line.startswith('#'):
                    # on a dépassé l'en-tête
                    header_lines -= 1
                    break
                if line.startswith('# ') or line.startswith('#{') or line.startswith('# {'):
                    try:
                        meta = json.loads(line.lstrip('#').strip())
                    except Exception:
                        pass
                if '# EndOfHeader' in line:
                    break
    except FileNotFoundError:
        raise
    return meta, header_lines


def extraire_fs_bits(meta: Optional[dict]) -> Tuple[Optional[float], Optional[int]]:
    if not meta or not isinstance(meta, dict) or len(meta) == 0:
        return None, None
    first_key = next(iter(meta))
    inner = meta.get(first_key, {})
    fs = None
    bits = None
    if isinstance(inner, dict):
        if 'sampling rate' in inner:
            fs = float(inner['sampling rate'])
        if 'resolution' in inner and isinstance(inner['resolution'], list) and len(inner['resolution']) > 0:
            # supposons même résolution pour tous les canaux; prendre le premier
            bits = int(inner['resolution'][0])
    return fs, bits


def charger_colonne(path: str, channel: str) -> list:
    """Charge une colonne de données pour un channel CH1..CH4 depuis un fichier tabulé OpenSignals.
    Retourne une liste de valeurs entières (ADC brutes).
    """
    ch = channel.strip().upper()
    mapping = {"CH1": 2, "CH2": 3, "CH3": 4, "CH4": 5}
    if ch not in mapping:
        raise SystemExit("channel doit être CH1, CH2, CH3 ou CH4")
    usecol = mapping[ch]

    valeurs = []
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
            if len(parts) <= usecol:
                continue
            try:
                valeurs.append(int(parts[usecol]))
            except ValueError:
                # ignorer lignes non conformes
                continue
    return valeurs


def rip_from_adc(adc_value: int, num_bits: int) -> float:
    # RIP(%) = (ADC / (2^n) - 1/2) * 100
    full_scale = 2 ** num_bits
    return (adc_value / full_scale - 0.5) * 100.0


def main():
    parser = argparse.ArgumentParser(description="Convertit un fichier segmenté OpenSignals en valeurs RIP(%) (CH3/CH4) et/ou ACC (g) (CH1/CH2) et exporte en JSON")
    parser.add_argument('-i', '--input', required=True, help='Chemin du fichier segmenté OpenSignals (.txt)')
    parser.add_argument('-c', '--channel', choices=['CH1','CH2','CH3','CH4','ch1','ch2','ch3','ch4'], help='Canal unique à convertir (option historique)')
    parser.add_argument('--channels', nargs='+', choices=['CH1','CH2','CH3','CH4','ch1','ch2','ch3','ch4'], help='Un ou plusieurs canaux à convertir (ex: --channels CH3 CH4)')
    parser.add_argument('-o', '--output', required=True, help='Chemin du fichier JSON de sortie')
    # Options ACC (CH1/CH2)
    parser.add_argument('--acc-cmin', type=int, help='Cmin global pour ACC (si omis: min du segment)')
    parser.add_argument('--acc-cmax', type=int, help='Cmax global pour ACC (si omis: max du segment)')
    parser.add_argument('--acc-cmin-x', type=int, help='Cmin spécifique pour CH1 (axe X)')
    parser.add_argument('--acc-cmax-x', type=int, help='Cmax spécifique pour CH1 (axe X)')
    parser.add_argument('--acc-cmin-y', type=int, help='Cmin spécifique pour CH2 (axe Y)')
    parser.add_argument('--acc-cmax-y', type=int, help='Cmax spécifique pour CH2 (axe Y)')
    parser.add_argument('--acc-full-scale', type=float, default=3.6, help='Pleine échelle ACC en g (ex: 3.6)')
    parser.add_argument('--bits', type=int, help='Résolution ADC (bits), si en-tête absent')
    parser.add_argument('--fs', type=float, help='Fréquence échantillonnage (Hz), si en-tête absent')
    args = parser.parse_args()

    # Calibration fixe imposée pour ACC (CH1 = axe X, CH2 = axe Y)
    ACC_CAL_FIXE = {
        "CH1": {"Cmin": 27584, "Cmax": 37720},
        "CH2": {"Cmin": 27468, "Cmax": 37767},
    }

    # Lire métadonnées
    meta, _ = lire_entete(args.input)
    fs_meta, bits_meta = extraire_fs_bits(meta)

    num_bits = args.bits if args.bits is not None else (bits_meta if bits_meta is not None else 16)
    fs = args.fs if args.fs is not None else (fs_meta if fs_meta is not None else None)

    # Déterminer la liste des canaux à traiter
    channels: list[str] = []
    if args.channels:
        channels = [c.upper() for c in args.channels]
    elif args.channel:
        channels = [args.channel.upper()]
    else:
        raise SystemExit("Spécifiez --channels CHx [CHy ...] ou -c CHx")

    # Charger et convertir chaque canal
    data_dict = {}
    per_channel_meta = {}
    for ch in channels:
        valeurs_adc = charger_colonne(args.input, ch)
        if ch in ("CH3", "CH4"):
            # RIP (%) pour voies respiration
            valeurs_conv = [rip_from_adc(v, num_bits) for v in valeurs_adc]
            data_dict[ch] = valeurs_conv
            per_channel_meta[ch] = {
                "type": "RIP",
                "transfer_function": "RIP(%) = (ADC/(2^n) - 0.5) * 100"
            }
        else:
            # ACC (g) pour CH1/CH2 - utiliser calibration fixe
            if ch in ACC_CAL_FIXE:
                cmin = ACC_CAL_FIXE[ch]["Cmin"]
                cmax = ACC_CAL_FIXE[ch]["Cmax"]
            else:
                cmin = (min(valeurs_adc) if valeurs_adc else 0)
                cmax = (max(valeurs_adc) if valeurs_adc else (2 ** num_bits - 1))
            if cmax == cmin:
                # éviter division par zéro, fallback à pleine échelle théorique
                cmin, cmax = 0, (2 ** num_bits) - 1
            scale = args.acc_full_scale
            # ACC(g) = (((ADC - Cmin)/(Cmax - Cmin)) * 2 - 1) * full_scale_g
            valeurs_conv = [((((v - cmin) / (cmax - cmin)) * 2.0) - 1.0) * scale for v in valeurs_adc]
            data_dict[ch] = valeurs_conv
            per_channel_meta[ch] = {
                "type": "ACC",
                "transfer_function": "ACC(g) = (((ADC - Cmin)/(Cmax - Cmin)) * 2 - 1) * full_scale_g",
                "Cmin": cmin,
                "Cmax": cmax,
                "full_scale_g": scale
            }

    # Construire JSON
    sortie = {
        "meta": {
            "channels": channels,
            "bits": num_bits,
            "fs": fs,
            "per_channel": per_channel_meta
        },
        "data": data_dict
    }

    with open(args.output, 'w') as f:
        json.dump(sortie, f, ensure_ascii=False)

    any_series = next(iter(data_dict.values()), [])
    print(f"Écrit: {args.output} (échantillons: {len(any_series)})")


if __name__ == '__main__':
    main()


