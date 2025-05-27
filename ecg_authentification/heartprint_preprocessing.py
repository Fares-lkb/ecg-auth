import os
import numpy as np
import pandas as pd
import scipy.signal
from scipy.signal import butter, filtfilt

# === Étape 1 : Paramètres ===
fs = 250  # Fréquence d’échantillonnage Heartprint
lowcut = 0.5
highcut = 40

# === Étape 2 : Fonction de filtrage passe-bande ===
def butter_bandpass_filter(signal, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, signal)

# === Étape 3 : Traitement des signaux ===
def process_ecg_folder(base_path, session_name):
    session_path = os.path.join(base_path, session_name)
    users = sorted(os.listdir(session_path))
    data = []

    for user in users:
        user_path = os.path.join(session_path, user)
        if not os.path.isdir(user_path):
            continue

        ecg_files = sorted(f for f in os.listdir(user_path) if f.endswith(".txt"))
        for file in ecg_files:
            file_path = os.path.join(user_path, file)
            try:
                raw_signal = np.loadtxt(file_path)
                if len(raw_signal) < 10:
                    continue

                filtered = butter_bandpass_filter(raw_signal, lowcut, highcut, fs)

                # Détection des pics R
                peaks, _ = scipy.signal.find_peaks(
                    filtered,
                    height=np.mean(filtered) * 1.2,
                    distance=int(0.6 * fs)
                )
                rr_intervals = np.diff(peaks) / fs

                for i in range(len(rr_intervals)):
                    beat = filtered[peaks[i]:peaks[i+1]]
                    if len(beat) < 10:
                        continue
                    data.append({
                        "user": user,
                        "session": session_name,
                        "file": file,
                        "RR": float(rr_intervals[i]),
                        "mean": float(np.mean(beat)),
                        "std": float(np.std(beat)),
                        "var": float(np.var(beat)),
                        "median": float(np.median(beat)),
                        "length": int(len(beat))
                    })
            except Exception as e:
                print(f"Erreur fichier {file_path}: {e}")
    return pd.DataFrame(data)

# === Étape 4 : Appliquer sur Session-1 et Session-2 ===
base_dir = "/home/yacine-kr/ecg_authentification/Heartprint"  # 🔁 À modifier selon ton PC
df_train = process_ecg_folder(base_dir, "Session-1")
df_test = process_ecg_folder(base_dir, "Session-2")

# === Étape 5 : Forcer types numériques et sauvegarde ===
for df in [df_train, df_test]:
    df["RR"] = pd.to_numeric(df["RR"], errors="coerce")
    df["mean"] = pd.to_numeric(df["mean"], errors="coerce")
    df["std"] = pd.to_numeric(df["std"], errors="coerce")
    df["var"] = pd.to_numeric(df["var"], errors="coerce")
    df["median"] = pd.to_numeric(df["median"], errors="coerce")
    df["length"] = pd.to_numeric(df["length"], errors="coerce")

df_train.to_csv("heartprint_train.csv", index=False)
df_test.to_csv("heartprint_test.csv", index=False)

print("✔️ Traitement terminé avec succès.")
