#!/usr/bin/env bash
# setup.sh — 検品環境を一から作る（Ubuntu 24.04 / macOS）
set -euo pipefail   # 途中で失敗したらそこで止める

if command -v apt >/dev/null 2>&1; then
  sudo apt update
  # libegl1 / libgles2：MediaPipe が画面のない Ubuntu で動くのに必要（無いと libEGL.so.1 エラー）
  sudo apt install -y python3-venv ffmpeg libgl1 libglib2.0-0 libegl1 libgles2 curl
fi

python3 -m venv .venv
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
