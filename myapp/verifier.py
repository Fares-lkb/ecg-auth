import numpy as np
import pywt
import joblib
import neurokit2 as nk
from scipy.signal import butter, filtfilt
from sklearn.preprocessing import StandardScaler
from django.shortcuts import render
from .models import SVMModels, UserDB, ECGRecord
from django.core.files.storage import default_storage
import os
import tempfile
from django.core.files import File

FS = 250
RADIUS = 100
SEUIL = 0.0395


def bandpass_filter(signal, low=0.5, high=40, fs=250, order=5):
    nyq = 0.5 * fs
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    return filtfilt(b, a, signal)


def extract_dwt_features(signal, wavelet="db4", level=3):
    coeffs = pywt.wavedec(signal, wavelet, level=level)
    A3, D3, D2, D1 = coeffs
    return np.concatenate([A3, D3, D2])


def create_ecg(preprocessed_file, user_id, svm_name):
    try:
        matricule = str(user_id).zfill(6)
        user = UserDB.objects.filter(matricule=matricule).first()
        if not user:
            print(f"Utilisateur avec matricule {matricule} introuvable.")
            return

        # Ensure the file has a valid name
        if not hasattr(preprocessed_file, "name") or not preprocessed_file.name:
            preprocessed_file.name = f"ecg_user_{matricule}.txt"

        ecg = ECGRecord.objects.create(user=user, ecg_file=preprocessed_file)

        svm = SVMModels.objects.filter(nom=svm_name).first()
        if svm:
            svm.ecg = ecg
            svm.save()
    except Exception as e:
        print("Erreur lors de l'enregistrement ECG :", e)


def ecg_authentication_view(request):
    if request.method == "POST":
        user_id = request.POST.get("id")
        ecg_file = request.FILES.get("ecg_file")

        if not user_id or not ecg_file:
            return render(
                request, "auth_form.html", {"error": "ID et fichier ECG requis."}
            )

        # Sauvegarder le fichier temporairement
        ecg_path = default_storage.save("tmp/" + ecg_file.name, ecg_file)
        ecg_path = os.path.join(default_storage.location, ecg_path)

        try:
            # Prétraitement du signal
            signal = np.loadtxt(ecg_path)
            filtered = bandpass_filter(signal)
            _, info = nk.ecg_process(filtered, sampling_rate=FS)
            rpeaks = info["ECG_R_Peaks"]

            r = rpeaks[1]
            start = r - RADIUS
            end = r + (227 - RADIUS)
            if start < 0 or end > len(filtered):
                raise ValueError("Battement ECG hors limites.")

            beat = filtered[start:end]
            beat = (beat - np.mean(beat)) / (np.std(beat) + 1e-8)
            features = extract_dwt_features(beat).reshape(1, -1)

            # Standardisation
            scaler = joblib.load("scaler_dwt.pkl")
            features_z = scaler.transform(features)

            # Chargement du modèle SVM
            model_name = f"svm_id_{int(user_id) - 1:03d}.pkl"
            model_entry = SVMModels.objects.get(nom=model_name)
            model = joblib.load(model_entry.fichier_svm.path)

            # Prédiction
            score = model.decision_function(features_z)[0]
            result = "accepté" if score >= SEUIL else "rejeté"

            # Retrieve user info
            matricule = str(user_id).zfill(6)
            user = UserDB.objects.filter(matricule=matricule).first()

            if result == "accepté":
                # Sauvegarder le battement filtré dans MEDIA/tmp/
                filename = f"ecg_filtered_{user_id}.txt"
                media_tmp_path = os.path.join("tmp", filename)
                full_tmp_path = os.path.join(default_storage.location, media_tmp_path)
                os.makedirs(os.path.dirname(full_tmp_path), exist_ok=True)
                np.savetxt(full_tmp_path, beat)

                # Sauvegarder dans la base de données
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".txt", mode="w"
                ) as tmpfile:
                    np.savetxt(tmpfile, beat)
                    tmpfile.flush()
                    tmpfile_path = tmpfile.name

                with open(tmpfile_path, "rb") as f:
                    django_file = File(f)
                    django_file.name = f"ecg_user_{user_id}.txt"
                    create_ecg(django_file, user_id, model_name)

                default_storage.delete(media_tmp_path)

                return render(
                    request,
                    "wlpage/Welcome.html",
                    {
                        "score": score,
                        "result": result,
                        "seuil": SEUIL,
                        "user_matricule": user.matricule if user else "",
                        "user_first_name": user.first_name if user else "",
                        "user_last_name": user.last_name if user else "",
                    },
                )
            else:
                return render(
                    request,
                    "auth_form.html",
                    {
                        "error": f"Authentification rejetée. Score : {score:.4f}, Seuil : {SEUIL}"
                    },
                )

        except Exception as e:
            return render(request, "auth_form.html", {"error": str(e)})

    return render(request, "auth_form.html")
