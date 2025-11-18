import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# Paramètres du signal
fs = 200.0  # fréquence d'échantillonnage (Hz)
fc = 2.0    # fréquence de coupure (Hz) pour respiration
order = 4   # ordre du filtre

# Conception du filtre passe-bas
b, a = butter(order, fc / (fs / 2), btype='low')

# Exemple de signal : respiration (~0.3 Hz) + bruit
t = np.linspace(0, 20, int(fs*20))  # 20 secondes
signal = np.sin(2*np.pi*0.3*t) + 0.3*np.random.randn(len(t))  

# Filtrage
signal_filtre = filtfilt(b, a, signal)

# --- FFT du signal ---
def compute_fft(sig, fs):
    N = len(sig)                    # nombre d'échantillons
    freqs = np.fft.rfftfreq(N, 1/fs)  # axe fréquentiel (positif)
    fft_vals = np.fft.rfft(sig)       # FFT réelle
    amplitude = np.abs(fft_vals) / N  # amplitude normalisée
    return freqs, amplitude

freqs, amp_raw = compute_fft(signal, fs)
freqs, amp_filt = compute_fft(signal_filtre, fs)

# --- Visualisation ---
plt.figure(figsize=(12,5))

plt.subplot(1,2,1)
plt.plot(t, signal, label="Signal brut", alpha=0.6)
plt.plot(t, signal_filtre, label="Signal filtré", linewidth=2)
plt.xlabel("Temps (s)")
plt.ylabel("Amplitude")
plt.title("Signal temporel")
plt.legend()

plt.subplot(1,2,2)
plt.plot(freqs, amp_raw, label="Brut", alpha=0.6)
plt.plot(freqs, amp_filt, label="Filtré", linewidth=2)
plt.xlim(0, 5)  # zoom sur 0-5 Hz (respiration est <2 Hz)
plt.xlabel("Fréquence (Hz)")
plt.ylabel("Amplitude")
plt.title("Spectre fréquentiel (FFT)")
plt.legend()

plt.tight_layout()
plt.show()