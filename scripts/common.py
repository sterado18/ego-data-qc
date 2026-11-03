"""検品・重ね描き・変換で共通に使う道具（パス、メタデータ、手の検出）。"""
import csv
import os
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "models" / "hand_landmarker.task"
RAW = Path(os.environ.get("EGO_RAW_DIR", ROOT / "data" / "raw"))
METADATA = ROOT / "data" / "metadata.csv"
SCORES = ROOT / "reports" / "scores.csv"
VIDEO_EXTS = {".mov", ".mp4", ".m4v"}

V = mp.tasks.vision
CONNECTIONS = [(c.start, c.end) for c in V.HandLandmarksConnections.HAND_CONNECTIONS]


def list_videos(folder):
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in VIDEO_EXTS)


def load_metadata(path=METADATA):
    """metadata.csv を file_name をキーにした辞書で返す。ファイルがなければ空。"""
    if not Path(path).exists():
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        return {r["file_name"]: r for r in csv.DictReader(f) if r.get("file_name")}


def detect_hands(path, stride=1):
    """動画を1コマずつ読み、(コマ番号, BGR画像, 検出結果 or None, fps) を返す。

    stride>1 のときは stride コマに1回だけ手を検出し、それ以外は None を返す。
    """
    opts = V.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL)),
        running_mode=V.RunningMode.VIDEO, num_hands=2)
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    i = 0
    with V.HandLandmarker.create_from_options(opts) as lm:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            res = None
            if i % stride == 0:
                img = mp.Image(image_format=mp.ImageFormat.SRGB,
                               data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                res = lm.detect_for_video(img, int(i * 1000 / fps))
            yield i, frame, res, fps
            i += 1
    cap.release()


def hand_pose_vector(res):
    """検出結果を126個の数値（左手21点×xyz、右手21点×xyz）にする。映っていない手は0。

    MediaPipe の左右判定は自撮り（鏡像）前提なので、一人称映像では左右が逆に出ることがある。
    ここでは判定ラベルをそのまま使い、並び順をそろえることだけを目的にしている。
    """
    vec = np.zeros(126, dtype=np.float32)
    for lms, hd in zip(res.hand_landmarks, res.handedness):
        offset = 0 if hd[0].category_name == "Left" else 63
        vec[offset:offset + 63] = [v for p in lms for v in (p.x, p.y, p.z)]
    return vec


def draw_hands(frame, res):
    """検出した手の骨格を画像に描く（その場で書き換える）。"""
    h, w = frame.shape[:2]
    for lms in res.hand_landmarks:
        pts = [(int(p.x * w), int(p.y * h)) for p in lms]
        for a, b in CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (0, 255, 0), 3)
        for pt in pts:
            cv2.circle(frame, pt, 5, (0, 0, 255), -1)
    return frame
