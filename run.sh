#!/usr/bin/env bash
# Tek komut: ./run.sh
# Telefon kamerası (sistemde görünüyorsa): ./run.sh phone
# Elle kamera indeksi: ./run.sh camera=1
# Sadece kontrol: ./run.sh --check
# Otomatik 5 kare testi: ./run.sh --test
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
VENV="$ROOT/venv310/bin/activate"

if [[ ! -f "$VENV" ]]; then
  echo "Hata: venv310 bulunamadı. Proje klasöründe olduğunuzdan emin olun."
  exit 1
fi
# shellcheck source=/dev/null
source "$VENV"

# Varsayılan: soru sor (PC otomatik seçilmez). Telefon = PC dışındaki kamera.
while [[ $# -gt 0 ]]; do
  case "$1" in
    phone|telefon)
      if [[ -f "$ROOT/.phone_camera_index" ]]; then
        export DROWSINESS_CAMERA_INDEX="$(tr -d '[:space:]' < "$ROOT/.phone_camera_index")"
      else
        export DROWSINESS_CAMERA_INDEX=1
      fi
      export DROWSINESS_PHONE_CAMERA_INDEX_FILE="$ROOT/.phone_camera_index"
      export DROWSINESS_SKIP_CAMERA_PREFLIGHT=1
      shift
      ;;
    camera=*)
      export DROWSINESS_CAMERA_INDEX="${1#camera=}"
      export DROWSINESS_SKIP_CAMERA_PREFLIGHT=1
      shift
      ;;
    pc|bilgisayar|0)
      export DROWSINESS_CAMERA=pc
      shift
      ;;
    --check)
      exec python preflight.py
      ;;
    --test)
      export DROWSINESS_CAMERA=pc
      export DROWSINESS_MAX_FRAMES=5
      export DROWSINESS_HEADLESS=1
      export DROWSINESS_QUIET=1
      python preflight.py
      exec python ai_live_arduino.py
      ;;
    *)
      echo "Bilinmeyen argüman: $1"
      echo "Kullanım: ./run.sh | ./run.sh phone | ./run.sh camera=1 | ./run.sh --check | ./run.sh --test"
      exit 1
      ;;
  esac
done

python preflight.py
if [[ -n "${DROWSINESS_CAMERA:-}" ]]; then
  echo "Kamera modu: $DROWSINESS_CAMERA (pencereden çıkmak: q)"
elif [[ -n "${DROWSINESS_CAMERA_INDEX:-}" ]]; then
  echo "Kamera indeksi: $DROWSINESS_CAMERA_INDEX (pencereden çıkmak: q)"
else
  echo "Kamera seçimi sorulacak (PC / Phone). Çıkmak: q"
fi
exec python ai_live_arduino.py
