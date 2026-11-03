"""環境の動作確認。使い方: .venv/bin/python scripts/check_env.py [動画ファイル]

動画を渡すと、MediaPipe で手が映っていたコマの割合を表示する。
"""
import sys
from pathlib import Path

import cv2
import mediapipe as mp
import pandas  # noqa: F401
try:
    from lerobot.datasets.lerobot_dataset import LeRobotDataset  # noqa: F401
    HAS_LEROBOT = True
except ImportError:
    HAS_LEROBOT = False

MODEL = Path(__file__).resolve().parent.parent / "models" / "hand_landmarker.task"
print(f"OpenCV {cv2.__version__} / MediaPipe {mp.__version__} / LeRobot {'OK' if HAS_LEROBOT else 'なし（検品だけなら不要）'}")

if len(sys.argv) < 2:
    sys.exit(0)

V = mp.tasks.vision
opts = V.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),
    running_mode=V.RunningMode.VIDEO, num_hands=2)
cap = cv2.VideoCapture(sys.argv[1])
fps = cap.get(cv2.CAP_PROP_FPS)
n = hands = 0
with V.HandLandmarker.create_from_options(opts) as lm:
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        img = mp.Image(image_format=mp.ImageFormat.SRGB,
                       data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        res = lm.detect_for_video(img, int(n * 1000 / fps))
        hands += len(res.hand_landmarks) >= 1
        n += 1
if n == 0:
    sys.exit("動画を読み込めませんでした")
print(f"{n}コマ（{n / fps:.1f}秒）中、手が映っていたのは {hands / n:.0%}")
