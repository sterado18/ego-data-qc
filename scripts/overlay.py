"""手の骨格を重ねた確認用の動画（と静止画）を書き出す。

使い方:
  .venv/bin/python scripts/overlay.py data/raw/IMG_1234.MOV
  .venv/bin/python scripts/overlay.py data/raw/IMG_1234.MOV --still 5.0   # 5秒目の静止画も保存

出力: reports/overlay/<元の名前>_overlay.mp4（と _still.png）。
静止画は品質レポートの「見本の画像」に使う。
"""
import argparse
from pathlib import Path

import cv2

from common import ROOT, detect_hands, draw_hands


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--still", type=float, help="静止画を保存する秒数")
    ap.add_argument("--out-dir", default=ROOT / "reports" / "overlay", type=Path)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / f"{args.video.stem}_overlay.mp4"
    writer = None
    n = hands = 0
    for i, frame, res, fps in detect_hands(args.video):
        draw_hands(frame, res)
        hands += len(res.hand_landmarks) >= 1
        n += 1
        if writer is None:
            h, w = frame.shape[:2]
            writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"avc1"), fps, (w, h))
        writer.write(frame)
        if args.still is not None and i == int(args.still * fps):
            cv2.imwrite(str(args.out_dir / f"{args.video.stem}_still.png"), frame)
    if writer is None:
        raise SystemExit("動画を読み込めませんでした")
    writer.release()
    print(f"{n}コマ中、手が映っていたのは {hands / n:.0%}")
    print(f"書き出し: {out}")


if __name__ == "__main__":
    main()
