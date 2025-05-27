import numpy as np
import pywt
import joblib
import neurokit2 as nk
from scipy.signal import butter, filtfilt
from sklearn.preprocessing import StandardScaler
from django.shortcuts import render
from .models import SVMModels
from django.core.files.storage import default_storage
import os

FS = 250
RADIUS = 100
SEUIL = 0.0395


def bandpass_filter(signal, low=0.5, high=40, fs=250, order=5):
    nyq = 0.5 * fs
    b, a = butter(order, [low/nyq, high/nyq], btype='band')
    return filtfilt(b, a, signal)


def extract_dwt_features(signal, wavelet='db4', level=3):
    coeffs = pywt.wavedec(signal, wavelet, level=level)
    A3, D3, D2, D1 = coeffs
    return np.concatenate([A3, D3, D2])


def ecg_authentication_view(request):
    if request.method == "POST":
        user_id = request.POST.get("id")  # ex: "14"
        ecg_file = request.FILES.get("ecg_file")

        if not user_id or not ecg_file:
            return render(request, "auth_form.html", {"error": "ID et fichier requis."})

        # Sauvegarder temporairement le fichier
        ecg_path = default_storage.save("tmp/" + ecg_file.name, ecg_file)
        ecg_path = os.path.join(default_storage.location, ecg_path)

        try:
            signal = np.loadtxt(ecg_path)
            filtered = bandpass_filter(signal)
            _, info = nk.ecg_process(filtered, sampling_rate=FS)
            rpeaks = info["ECG_R_Peaks"]

            r = rpeaks[1]
            start = r - RADIUS
            end = r + (227 - RADIUS)

            if start < 0 or end > len(filtered):
                raise ValueError("Battement hors limites.")

            beat = filtered[start:end]
            beat = (beat - np.mean(beat)) / (np.std(beat) + 1e-8)
            features = extract_dwt_features(beat).reshape(1, -1)

            # Charger le scaler
            scaler_path = os.path.join("scaler_dwt.pkl")
            scaler = joblib.load(scaler_path)
            features_z = scaler.transform(features)

            # Trouver le modèle dans la base Django
            model_name = f"svm_id_{int(user_id) - 1:03d}.pkl"
            model_entry = SVMModels.objects.get(nom=model_name)
            model = joblib.load(model_entry.fichier_svm.path)

            score = model.decision_function(features_z)[0]
            result = "accepté" if score >= SEUIL else "rejeté"

            return render(request, "auth_result.html", {
                "score": score,
                "result": result,
                "seuil": SEUIL
            })

        except Exception as e:
            return render(request, "auth_form.html", {"error": str(e)})

    return render(request, "auth_form.html")
