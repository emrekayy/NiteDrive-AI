import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils import resample
import joblib

from features import ML_FEATURE_COLUMNS, apply_rolling_ear_features_df

# =========================
# 1️⃣ DATASET OKU
# =========================
df = pd.read_csv("clean_data.csv")

print("İlk veri:")
print(df.head())

print("\nToplam veri:", len(df))

# =========================
# 2️⃣ FEATURE ENGINEERING (features.py ile aynı rolling)
# =========================
df = apply_rolling_ear_features_df(df)
df = df.fillna(0)

print("\nFeature engineering tamam")
print("Kalan veri:", len(df))

# =========================
# 3️⃣ FEATURE / LABEL
# =========================
X = df[ML_FEATURE_COLUMNS]
y = df["Label"]

# =========================
# 4️⃣ TRAIN / TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("\nTrain/Test split tamam")

# =========================
# 5️⃣ BALANCE (SADECE TRAIN)
# =========================
train_df = pd.concat([X_train, y_train], axis=1)

df_major = train_df[train_df.Label == 0]
df_minor = train_df[train_df.Label == 1]

df_minor_up = resample(
    df_minor,
    replace=True,
    n_samples=len(df_major),
    random_state=42
)

train_balanced = pd.concat([df_major, df_minor_up])

X_train = train_balanced.drop("Label", axis=1)
y_train = train_balanced["Label"]

print("\nBalanced train dağılım:")
print(y_train.value_counts())

# =========================
# 6️⃣ PIPELINE (SCALER + MODEL)
# =========================
pipeline = Pipeline(
    [
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
    ]
)
pipeline.fit(X_train, y_train)

print("Pipeline eğitildi")

# =========================
# 7️⃣ TEST
# =========================
y_pred = pipeline.predict(X_test)

print("\n🔥 Accuracy:", accuracy_score(y_test, y_pred))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# =========================
# 8️⃣ CROSS VALIDATION
# =========================
scores = cross_val_score(pipeline, X, y, cv=5)
print("\n🔥 Cross-validation accuracy:", scores.mean())

# =========================
# 9️⃣ PIPELINE KAYDET
# =========================
joblib.dump(pipeline, "drowsiness_model.pkl")

print("\nPipeline kaydedildi (drowsiness_model.pkl)")