import os
import cv2
import mediapipe as mp
import pandas as pd
from tqdm import tqdm

from features import static_image_geometry_row

# =========================
# YOLLAR
# =========================
BASE_DIR = "kaggle_data/ddd/Driver Drowsiness Dataset (DDD)"
OUTPUT_CSV = "kaggle_features.csv"

DROWSY_DIR = os.path.join(BASE_DIR, "Drowsy")
NON_DROWSY_DIR = os.path.join(BASE_DIR, "Non Drowsy")

# =========================
# MEDIAPIPE
# =========================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def extract_features_from_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None

    h, w, _ = image.shape
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return None

    landmarks = results.multi_face_landmarks[0].landmark
    g = static_image_geometry_row(landmarks, w, h)

    return {
        "EAR": g["EAR"],
        "Head_drop": g["Head_drop"],
    }


def collect_image_paths(folder):
    paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(VALID_EXTENSIONS):
                paths.append(os.path.join(root, file))
    return sorted(paths)


# =========================
# ANA AKIŞ
# =========================
def main():
    drowsy_paths = collect_image_paths(DROWSY_DIR)
    non_drowsy_paths = collect_image_paths(NON_DROWSY_DIR)

    print(f"Drowsy image sayısı: {len(drowsy_paths)}")
    print(f"Non-Drowsy image sayısı: {len(non_drowsy_paths)}")

    rows = []
    skipped = 0

    # Non-drowsy = 0
    for path in tqdm(non_drowsy_paths, desc="Non-Drowsy işleniyor"):
        feats = extract_features_from_image(path)
        if feats is None:
            skipped += 1
            continue

        rows.append({
            "EAR": feats["EAR"],
            "Blink": 0,
            "Duration": 0.0,
            "PERCLOS": 0.0,
            "EAR_mean": feats["EAR"],
            "EAR_std": 0.0,
            "Head_drop": feats["Head_drop"],
            "Label": 0,
            "Source": "kaggle_ddd"
        })

    # Drowsy = 1
    for path in tqdm(drowsy_paths, desc="Drowsy işleniyor"):
        feats = extract_features_from_image(path)
        if feats is None:
            skipped += 1
            continue

        rows.append({
            "EAR": feats["EAR"],
            "Blink": 0,
            "Duration": 0.0,
            "PERCLOS": 0.0,
            "EAR_mean": feats["EAR"],
            "EAR_std": 0.0,
            "Head_drop": feats["Head_drop"],
            "Label": 1,
            "Source": "kaggle_ddd"
        })

    df = pd.DataFrame(rows)

    print("\nToplam çıkarılan kayıt:", len(df))
    print("Atlanan görsel:", skipped)

    if len(df) == 0:
        print("Hiç feature çıkarılamadı.")
        return

    print("\nLabel dağılımı:")
    print(df["Label"].value_counts())

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nKaydedildi: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
