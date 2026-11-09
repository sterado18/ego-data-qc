#!/usr/bin/env bash
# setup.sh — 検品環境を一から作る（Ubuntu 24.04 / macOS）
set -euo pipefail   # 途中で失敗したらそこで止める

if command -v apt >/dev/null 2>&1; then
  sudo apt update
  # libegl1 / libgles2：MediaPipe が画面のない Ubuntu で動くのに必要（無いと libEGL.so.1 エラー）
  sudo apt install -y python3-venv ffmpeg libgl1 libglib2.0-0 libegl1 libgles2 curl
fi

# Python 3.12 を使う（requirements.txt の numpy==2.5.4 は 3.12 以上が必要。Ubuntu 24.04 の python3 は 3.12）
PY=""
for c in python3.12 python3; do
  if "$c" -c "import sys; sys.exit(sys.version_info < (3, 12))" >/dev/null 2>&1; then PY=$c; break; fi
done
[ -n "$PY" ] || { echo "Python 3.12 以上が見つかりません"; exit 1; }
"$PY" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 手の検出モデル（MediaPipe Hand Landmarker）
mkdir -p models
if [ ! -f models/hand_landmarker.task ]; then
  curl -L -o models/hand_landmarker.task \
    https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
fi

.venv/bin/python scripts/check_env.py
echo "setup OK"
