import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import joblib

from features import ML_FEATURE_COLUMNS

df = pd.read_csv("data.csv")

if all(c in df.columns for c in ML_FEATURE_COLUMNS):
    X = df[ML_FEATURE_COLUMNS]
else:
    X = df[["EAR", "Blink", "Duration", "PERCLOS"]]
y = df["Label"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = LogisticRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_pred))

joblib.dump(model, "model.pkl")
print("MODEL KAYDEDILDI")