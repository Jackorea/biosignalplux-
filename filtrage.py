import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, spectrogram
from scipy.fft import fft, fftfreq

def charger_signal(path, channel: str | None):
    """
    Charge un signal depuis:
      - un fichier mono-colonne (une valeur par ligne), ou
      - un fichier OpenSignals-like tabulé (avec en-tête '#', colonnes: nSeq, DI, CH1..CH4).

    channel: 'CH1' | 'CH2' | 'CH3' | 'CH4' (insensible à la casse) si fichier tabulé. Ignoré pour mono-colonne.
    Retourne (signal: np.ndarray, fs: float)
    """
    # Valeur par défaut si non détecté dans l'en-tête
    fs_detecte = 100.0

    # D'abord, essayer mono-colonne simple
    try:
        sig = np.loadtxt(path)
        if sig.ndim == 1:
            return sig, fs_detecte
        elif sig.ndim == 2 and sig.shape[1] == 1:
            return sig[:, 0], fs_detecte
    except Exception:
        pass

    # Ensuite, essayer OpenSignals-like (avec '	') et sélectionner la colonne
    if channel is None:
        raise ValueError("Pour un fichier tabulé, spécifiez --channel CH1/CH2/CH3/CH4")
    ch = channel.strip().upper()
    if ch not in {"CH1", "CH2", "CH3", "CH4"}:
        raise ValueError("channel doit être CH1, CH2, CH3 ou CH4")

    # Mapping d'après l'en-tête OpenSignals: ["nSeq","DI","CH1","CH2","CH3","CH4"]
    channel_to_col = {"CH1": 2, "CH2": 3, "CH3": 4, "CH4": 5}
    usecols = channel_to_col[ch]

    # Extraire fréquence d'échantillonnage dans l'en-tête si possible
    try:
        with open(path, 'r') as f:
            for line in f:
                if line.startswith('#') and 'sampling rate' in line:
                    # ligne JSON en commentaire
                    try:
                        # extraire nombre après 'sampling rate": '
                        import json
                        meta_str = line.lstrip('#').strip()
                        meta = json.loads(meta_str)
                        # structure: {"deviceId": { "sampling rate": 100, ... }}
                        # prendre le premier dict interne
                        if isinstance(meta, dict) and meta:
                            first_key = next(iter(meta))
                            inner = meta[first_key]
                            if isinstance(inner, dict) and 'sampling rate' in inner:
                                fs_detecte = float(inner['sampling rate'])
                    except Exception:
                        pass
                if '# EndOfHeader' in line:
                    break
    except FileNotFoundError:
        raise

    # Charger colonne CH3/CH4 (tab-delimited), en ignorant les lignes '#'
    sig = np.loadtxt(path, delimiter='\t', usecols=usecols, comments='#')
    if sig.ndim == 0:
        sig = np.array([float(sig)])
    return sig, fs_detecte


parser = argparse.ArgumentParser(description="Analyse respiration: brut vs filtré (temps/FFT/spectrogramme)")
parser.add_argument('-i', '--input', default="respiration.txt", help='Chemin du fichier d\'entrée')
parser.add_argument('-c', '--channel', choices=['CH1','CH2','CH3','CH4','ch1','ch2','ch3','ch4'], help='Canal à charger si fichier tabulé')
args = parser.parse_args()

# 1. Charger le signal
signal, fs = charger_signal(args.input, args.channel)
t = np.linspace(0, len(signal) / fs, len(signal))

# 2. Filtrage: Compression douce (Soft Clipping) vers [19000, 50000]
# On utilise une fonction tanh pour contraindre le signal dans l'intervalle
# tout en préservant la forme sinusoïdale (arrondie) aux extrêmes, plutôt qu'une coupure nette.
target_min = 19000
target_max = 50000
center = (target_min + target_max) / 2  # 34500
span = (target_max - target_min) / 2    # 15500

# Formule: center + span * tanh((x - center) / span)
# Les valeurs proches du centre sont peu modifiées. Les valeurs extrêmes sont "tassées" doucement vers les bornes.
signal_soft_clipped = center + span * np.tanh((signal - center) / span)

# 3. Filtrage Butterworth (0.1 - 2 Hz) APRES le soft clipping
# Cela permet de lisser les artefacts créés par la compression et de ne garder que la composante respiratoire.
lowcut = 0.2
highcut = 0.6  # Ajusté à 2.0 Hz car la respiration dépasse rarement 60 BPM, 3Hz est un peu large pour juste respirer
order = 4
nyq = 0.5 * fs
low = lowcut / nyq
high = highcut / nyq
b, a = butter(order, [low, high], btype='band')

# On applique le filtre sur le signal déjà "soft clipped"
signal_filtre = filtfilt(b, a, signal_soft_clipped)

# 3. Transformée de Fourier (brut et filtré)
N = len(signal)
frequencies = fftfreq(N, d=1/fs)

# FFT du signal brut
fft_values_raw = fft(signal)
fft_magnitude_raw = np.abs(fft_values_raw) / N

# FFT du signal filtré
fft_values_filt = fft(signal_filtre)
fft_magnitude_filt = np.abs(fft_values_filt) / N

# 4. Créer la figure avec 3 sous-graphiques
fig, axs = plt.subplots(3, 1, figsize=(12, 10))

# === 1. Signal brut et filtré ===
axs[0].plot(t, signal, label="Signal brut", alpha=0.3)
axs[0].plot(t, signal_soft_clipped, label="Soft Clipped", alpha=0.5, linestyle='--')
axs[0].plot(t, signal_filtre, label="Final (Clip + Filter)", linewidth=2, color='red')
axs[0].set_title("Filtrage Hybride : Soft Clip -> Butterworth")
axs[0].set_xlabel("Temps (s)")
axs[0].set_ylabel("Amplitude")
# Optionnel: forcer l'affichage pour bien voir la compression
# axs[0].set_ylim(15000, 55000)
axs[0].legend()
axs[0].grid(True)

# === 2. Spectrogramme ===
f, t_spec, Sxx = spectrogram(signal, fs=fs, nperseg=256, noverlap=128)
pcm = axs[1].pcolormesh(t_spec, f, 10 * np.log10(Sxx), shading='gouraud', cmap='viridis')
axs[1].set_title("Spectrogramme du signal brut")
axs[1].set_ylabel("Fréquence (Hz)")
axs[1].set_xlabel("Temps (s)")
axs[1].set_ylim(0, 5)  # zoom sur les basses fréquences
fig.colorbar(pcm, ax=axs[1], label='Intensité (dB)')

# === 3. Spectre de Fourier (comparaison brut vs filtré) ===
axs[2].plot(frequencies[:N // 2], fft_magnitude_raw[:N // 2], label="Brut", color='darkred', alpha=0.6)
axs[2].plot(frequencies[:N // 2], fft_magnitude_filt[:N // 2], label="Filtré", color='tab:blue', linewidth=2)
axs[2].set_title("Transformée de Fourier: brut vs filtré")
axs[2].set_xlabel("Fréquence (Hz)")
axs[2].set_ylabel("Amplitude")
axs[2].set_xlim(0, 1)
axs[2].grid(True)
axs[2].legend()

# Affichage final
plt.tight_layout()
plt.show()
