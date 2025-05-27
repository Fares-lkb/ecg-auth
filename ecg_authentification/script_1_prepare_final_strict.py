
# script_1_prepare_final_strict.py

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# === Étape 1 : Charger les fichiers originaux ===
df_train = pd.read_csv("heartprint_train.csv")
df_test = pd.read_csv("heartprint_test.csv")

# === Étape 2 : Nettoyage ===
df_train.dropna(inplace=True)
df_test.dropna(inplace=True)

# === Étape 3 : Corrélation (facultatif)
corr = df_train[["mean", "std", "var", "median", "RR"]].corr()
sns.heatmap(corr, annot=True, cmap="coolwarm")
plt.title("Corrélation entre caractéristiques")
plt.tight_layout()
plt.savefig("correlation_heatmap.png")

# === Étape 4 : Supprimer 'var' (trop corrélée à 'std')
df_train.drop(columns=["var"], inplace=True)
df_test.drop(columns=["var"], inplace=True)

# === Étape 5 : Construction de X et y ===
X_train = df_train[["mean", "std", "RR", "median"]]
y_train = df_train[["user"]]

X_test = df_test[["mean", "std", "RR", "median"]]
y_test = df_test[["user"]]

# === Étape 6 : Sauvegarde explicite avec affichage
print("✅ Sauvegarde de X_train.csv")
X_train.to_csv("X_train.csv", index=False)
print("✅ Sauvegarde de y_train.csv")
y_train.to_csv("y_train.csv", index=False)
print("✅ Sauvegarde de X_test.csv")
X_test.to_csv("X_test.csv", index=False)
print("✅ Sauvegarde de y_test.csv")
y_test.to_csv("y_test.csv", index=False)

# Affichage résumé
print("\n✔️ Tous les fichiers ont été sauvegardés correctement avec les bonnes colonnes.")
print("X_train colonnes :", X_train.columns.tolist())
print("y_train colonnes :", y_train.columns.tolist())
print("X_test colonnes :", X_test.columns.tolist())
print("y_test colonnes :", y_test.columns.tolist())
