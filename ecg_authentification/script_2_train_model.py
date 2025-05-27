
# script_2_train_model.py

import pandas as pd
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# === 1. Charger les données ===
X_train = pd.read_csv("X_train.csv")
y_train = pd.read_csv("y_train.csv").values.ravel()

X_test = pd.read_csv("X_test.csv")
y_test = pd.read_csv("y_test.csv").values.ravel()

# === 2. Créer et entraîner le modèle SVM ===
model = SVC(kernel="linear", C=1)
model.fit(X_train, y_train)

# === 3. Prédictions ===
y_pred = model.predict(X_test)

# === 4. Évaluation ===
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Précision globale : {accuracy:.4f}\n")
print("=== Rapport de classification ===")
print(classification_report(y_test, y_pred))

# === 5. Matrice de confusion ===
conf_mat = confusion_matrix(y_test, y_pred, labels=sorted(set(y_test)))
plt.figure(figsize=(12, 10))
sns.heatmap(conf_mat, annot=False, cmap="Blues")
plt.title("Matrice de confusion")
plt.xlabel("Prédiction")
plt.ylabel("Réel")
plt.tight_layout()
plt.savefig("confusion_matrix.png")
print("📊 Matrice de confusion sauvegardée dans 'confusion_matrix.png'")
