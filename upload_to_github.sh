#!/usr/bin/env bash
# NiteDrive-AI → GitHub yükleme (tek seferlik giriş sonrası)
set -euo pipefail
cd "$(dirname "$0")"

if ! gh auth status &>/dev/null; then
  echo "GitHub girişi gerekli. Tarayıcı açılacak..."
  gh auth login --hostname github.com --git-protocol https --web
fi

if git remote get-url origin &>/dev/null; then
  git remote set-url origin https://github.com/emrekayy/NiteDrive-AI.git
else
  git remote add origin https://github.com/emrekayy/NiteDrive-AI.git
fi

if gh repo view emrekayy/NiteDrive-AI &>/dev/null; then
  echo "Repo mevcut, push ediliyor..."
  git push -u origin main
else
  echo "Repo oluşturuluyor ve push ediliyor..."
  gh repo create NiteDrive-AI --public --source=. --remote=origin --push \
    --description "AI-powered real-time driver drowsiness detection and Arduino alert system"
fi

echo "Tamam: https://github.com/emrekayy/NiteDrive-AI"
