"""
Eğitim veri setini temizler ve clean_data_v2.csv olarak kaydeder.
Orijinal clean_data.csv / new_data.csv dosyalarini degistirmez.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

EXPECTED_COLS = [
    "EAR",
    "Blink",
    "Duration",
    "PERCLOS",
    "EAR_mean",
    "EAR_std",
    "Head_drop",
    "Label",
]

INPUT_FILES = ["clean_data.csv", "new_data.csv"]
OUTPUT_FILE = "clean_data_v2.csv"


def main() -> None:
    parts: list[pd.DataFrame] = []
    for name in INPUT_FILES:
        p = Path(name)
        if p.exists():
            parts.append(pd.read_csv(p))
            print(f"Yuklendi: {name}  ({len(parts[-1])} satir)")
        else:
            print(f"Atlandi (yok): {name}")

    if not parts:
        raise SystemExit("Giris CSV bulunamadi (clean_data.csv veya new_data.csv).")

    df = pd.concat(parts, ignore_index=True)
    n_total = len(df)
    print(f"\nBirlesik satir: {n_total}")

    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        raise SystemExit(f"Eksik sutunlar: {missing}")

    df = df[EXPECTED_COLS].copy()

    for c in EXPECTED_COLS[:-1]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Label"] = pd.to_numeric(df["Label"], errors="coerce")

    eps = 1e-9
    zero_dur = df["Duration"].abs() < eps
    zero_p = df["PERCLOS"].abs() < eps
    zero_b = df["Blink"].abs() < eps

    finite_mask = np.isfinite(df[EXPECTED_COLS[:-1]].to_numpy(dtype=float)).all(axis=1)
    label_ok = df["Label"].isin([0, 1])

    rule_drowsy_no_signal = (df["Label"] == 1) & zero_dur & zero_p
    rule_drowsy_open_eye = (df["Label"] == 1) & (df["EAR"] > 0.30) & zero_dur
    rule_all_temporal_zero = zero_p & zero_b & zero_dur

    remove_mask = (
        ~finite_mask
        | ~label_ok
        | rule_drowsy_no_signal
        | rule_drowsy_open_eye
        | rule_all_temporal_zero
    )

    n_removed = int(remove_mask.sum())
    df_out = df.loc[~remove_mask].copy()
    df_out["Label"] = df_out["Label"].astype(int)
    n_kept = len(df_out)

    pct_kept = 100.0 * n_kept / n_total if n_total else 0.0
    pct_removed = 100.0 * n_removed / n_total if n_total else 0.0

    print("\n--- TEMIZLIK RAPORU ---")
    print(f"Silinen satir:        {n_removed}")
    print(f"Kalan satir:          {n_kept}")
    print(f"Temizlenen oran:      {pct_removed:.2f}%")
    print(f"Korunan veri orani:   {pct_kept:.2f}%")
    print("\nKural bazli eslesen satir sayilari (OR ile birlestirilir; satirlar birden fazla kurala uyabilir):")
    print(f"  NaN/Inf veya Label 0/1 disi: {int((~finite_mask | ~label_ok).sum())}")
    print(f"  Label=1 & Dur=0 & PER=0:   {int(rule_drowsy_no_signal.sum())}")
    print(f"  Label=1 & EAR>0.30 & Dur=0:{int(rule_drowsy_open_eye.sum())}")
    print(f"  PER=Blink=Dur=0:           {int(rule_all_temporal_zero.sum())}")

    if n_kept:
        print("\nLabel dagilimi (v2):")
        print(df_out["Label"].value_counts().sort_index().to_string())

    out_path = Path(OUTPUT_FILE)
    df_out.to_csv(out_path, index=False)
    print(f"\nKaydedildi: {out_path.resolve()}")


if __name__ == "__main__":
    main()
