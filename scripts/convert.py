"""合格したエピソードを LeRobot 形式にまとめる（手順3）。

使い方:
  .venv/bin/python scripts/convert.py              # reports/scores.csv の合格分を変換
  .venv/bin/python scripts/convert.py --overwrite  # 前回の出力を消して作り直す

出力: data/lerobot/ego_pilot/
  observation.images.ego  … 頭のカメラ映像（計測値）
  observation.hand_pose   … 両手×21点×xyz の126個（MediaPipe による推定値。手がないコマは0）
  next.success            … 作業が成功したエピソードの最後のコマだけ True（LeRobot の慣例）
  meta/episode_labels.json … エピソード番号ごとの episode_id・元ファイル・成否・予定どおりの失敗か
  meta/estimates.json     … 推定値に使った道具とバージョンの記録
"""
import argparse
import csv
import json
import shutil
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from lerobot.datasets.lerobot_dataset import LeRobotDataset

from common import MODEL, RAW, ROOT, SCORES, detect_hands, hand_pose_vector, load_metadata

OUT = ROOT / "data" / "lerobot" / "ego_pilot"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=RAW, type=Path)
    ap.add_argument("--scores", default=SCORES, type=Path)
    ap.add_argument("--out", default=OUT, type=Path)
    ap.add_argument("--repo-id", default="sasuke/ego-kitchen-pilot")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    with open(args.scores, encoding="utf-8-sig", newline="") as f:
        accepted = [r["file_name"] for r in csv.DictReader(f) if r["accepted"] == "yes"]
    if not accepted:
        raise SystemExit("合格したエピソードがありません。先に score.py を実行してください")
    meta = load_metadata()

    if args.out.exists():
        if not args.overwrite:
            raise SystemExit(f"{args.out} がすでにあります。作り直すなら --overwrite を付けてください")
        shutil.rmtree(args.out)

    # 映像の大きさとfpsは1本目に合わせる。違う設定で撮った動画は飛ばす
    cap = cv2.VideoCapture(str(args.raw / accepted[0]))
    ok, first = cap.read()
    fps = round(cap.get(cv2.CAP_PROP_FPS))
    cap.release()
    h, w = first.shape[:2]

    features = {
        "observation.images.ego": {"dtype": "video", "shape": (h, w, 3),
                                   "names": ["height", "width", "channels"]},
        "observation.hand_pose": {"dtype": "float32", "shape": (126,), "names": None},
        "next.success": {"dtype": "bool", "shape": (1,), "names": None},
    }
    ds = LeRobotDataset.create(repo_id=args.repo_id, fps=fps, features=features,
                               root=args.out, use_videos=True)

    done = 0
    labels = []
    for name in accepted:
        m = meta.get(name, {})
        instruction = m.get("instruction", "").strip() or "（指示文なし）"
        success = m.get("success", "").strip() == "成功"
        print(f"{name}: {instruction}（{'成功' if success else '失敗例'}）", flush=True)
        # 最後のコマにだけ成否を付けるため、1コマ遅れで書き込む
        n, prev = 0, None
        for i, frame, res, _ in detect_hands(args.raw / name):
            if frame.shape[:2] != (h, w):
                print(f"  映像の大きさが {frame.shape[1]}x{frame.shape[0]} で1本目と違うので飛ばします")
                break
            if prev is not None:
                ds.add_frame({**prev, "next.success": np.array([False])})
            prev = {"observation.images.ego": cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                    "observation.hand_pose": hand_pose_vector(res),
                    "task": instruction}
            n += 1
        else:
            ds.add_frame({**prev, "next.success": np.array([success])})
            ds.save_episode()
            labels.append({"episode_index": done, "episode_id": m.get("episode_id", ""),
                           "file_name": name, "success": success,
                           "intended_failure": m.get("intended_failure", "").strip() == "yes"})
            done += 1
            print(f"  {n}コマを保存")
            continue
        ds.clear_episode_buffer()
    ds.finalize()

    (args.out / "meta" / "estimates.json").write_text(json.dumps({
        "observation.hand_pose": {
            "kind": "estimated",
            "estimator": "MediaPipe Hand Landmarker",
            "mediapipe_version": mp.__version__,
            "model_file": MODEL.name,
            "model_variant": "float16",
            "layout": "left hand 21x(x,y,z), then right hand 21x(x,y,z); x,y normalized to image; 0 when not detected",
            "note": "handedness labels assume a mirrored (selfie) view and may be swapped in egocentric video",
        },
        "observation.images.ego": {"kind": "measured"},
    }, ensure_ascii=False, indent=2))

    (args.out / "meta" / "episode_labels.json").write_text(
        json.dumps(labels, ensure_ascii=False, indent=2))

    check = LeRobotDataset(args.repo_id, root=args.out)
    print(f"\n{done}エピソード・{len(check)}コマを書き出し、読み込み直しも成功: {args.out}")


if __name__ == "__main__":
    main()
