"""全エピソードを採点し、合否と不採用理由を CSV に書き出す（手順2）。

使い方:
  .venv/bin/python scripts/score.py                 # data/raw の全動画
  .venv/bin/python scripts/score.py --blur-th 25    # ブレの閾値を変える
  .venv/bin/python scripts/score.py --stride 1      # 全コマで手を検出（遅いが細かい）

出力: reports/scores.csv（1動画1行）と、画面への集計。
合格した動画は data/accepted/ にコピーする（verify_upload.sh の送り元）。
閾値は入門ガイドの「判定基準」の初期値。自分のデータを見ながら調整する。
"""
import argparse
import csv
import shutil
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from common import RAW, ROOT, SCORES, detect_hands, list_videos, load_metadata

# タスクごとの想定の長さ（秒）の上限。これの2倍を超えたら長すぎとみなす
MAX_SEC = {"A": 40, "B": 60, "C": 30}
MIN_SEC = 5
HAND_MIN = 0.70    # 手の映り率の下限
BOTH_MIN = 0.50    # 両手の映り率の下限（タオル＝タスクBのみ）
BLUR_MAX = 0.20    # ブレたコマの割合の上限
LIGHT_MAX = 0.10   # 暗すぎ・明るすぎのコマの割合の上限


def measure(path, blur_th, stride):
    n = det = hands1 = hands2 = blurry = bad_light = 0
    sharp = []
    fps = 30.0
    for i, frame, res, fps in detect_hands(path, stride):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        v = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharp.append(v)
        blurry += v < blur_th
        bad_light += not 40 < gray.mean() < 220
        if res is not None:
            k = len(res.hand_landmarks)
            hands1 += k >= 1
            hands2 += k >= 2
            det += 1
        n += 1
    if n == 0:
        return None
    return dict(sec=round(n / fps, 1), hand=round(hands1 / det, 3), both=round(hands2 / det, 3),
                blur=round(blurry / n, 3), light=round(bad_light / n, 3),
                sharp_p10=round(float(np.percentile(sharp, 10)), 1),
                sharp_median=round(float(np.median(sharp)), 1))


def judge(m, meta):
    task = meta.get("task", "").strip().upper()
    reasons = []
    if m["hand"] < HAND_MIN:
        reasons.append("手の映り不足")
    if task == "B" and m["both"] < BOTH_MIN:
        reasons.append("両手の映り不足")
    if m["blur"] > BLUR_MAX:
        reasons.append("ブレ")
    if m["light"] > LIGHT_MAX:
        reasons.append("明るさ")
    if m["sec"] < MIN_SEC or (task in MAX_SEC and m["sec"] > MAX_SEC[task] * 2):
        reasons.append("長さ")
    # 成否は合否とは別のラベル。予定どおりの失敗は「失敗例」として採用し、予定外の失敗だけ落とす
    if meta.get("success", "").strip() == "失敗" and meta.get("intended_failure", "").strip() != "yes":
        reasons.append("予定外の失敗")
    flag = meta.get("self_flag", "").strip()
    if flag:
        reasons.append(flag)  # 演出／ループ／写り込み（人の目で判断したもの）
    return reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=RAW, type=Path)
    ap.add_argument("--out", default=SCORES, type=Path)
    ap.add_argument("--blur-th", default=30.0, type=float,  # IMG_0453（13 Pro・0.5倍・1080p）の実測で暫定
                    help="鮮明さ（ラプラシアン分散）がこれ未満のコマをブレとみなす")
    ap.add_argument("--stride", default=3, type=int, help="何コマに1回手を検出するか")
    args = ap.parse_args()

    meta_all = load_metadata()
    videos = list_videos(args.raw)
    if not videos:
        raise SystemExit(f"動画がありません: {args.raw}")

    rows = []
    for k, path in enumerate(videos, 1):
        print(f"[{k}/{len(videos)}] {path.name}", flush=True)
        m = measure(path, args.blur_th, args.stride)
        if m is None:
            print("  読み込めませんでした。スキップします")
            continue
        meta = meta_all.get(path.name, {})
        reasons = judge(m, meta)
        rows.append(dict(file_name=path.name, episode_id=meta.get("episode_id", ""),
                         task=meta.get("task", ""), success=meta.get("success", "").strip(), **m,
                         accepted="yes" if not reasons else "no",
                         reasons="／".join(reasons)))
        print(f"  {m['sec']}秒 手{m['hand']:.0%} 両手{m['both']:.0%} ブレ{m['blur']:.0%} "
              f"明るさ{m['light']:.0%} → {'合格' if not reasons else '不採用：' + '／'.join(reasons)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r["accepted"] == "yes"]
    # 合格分だけを data/accepted に置き直す（前回の残りが混ざらないよう毎回作り直す）
    accepted_dir = ROOT / "data" / "accepted"
    shutil.rmtree(accepted_dir, ignore_errors=True)
    accepted_dir.mkdir(parents=True)
    for r in ok:
        shutil.copy2(Path(args.raw) / r["file_name"], accepted_dir / r["file_name"])
    total_min = sum(r["sec"] for r in rows) / 60
    ok_min = sum(r["sec"] for r in ok) / 60
    print(f"\n{len(rows)}本中 合格{len(ok)}本／不採用率 {1 - len(ok) / len(rows):.0%}")
    print(f"撮影 {total_min:.1f}分 → 受入 {ok_min:.1f}分")
    fail_ok = sum(r["success"] == "失敗" for r in ok)
    if fail_ok:
        print(f"  合格のうち失敗例（ラベル付きで採用）: {fail_ok}本")
    counts = Counter(x for r in rows for x in r["reasons"].split("／") if x)
    for reason, c in counts.most_common():
        print(f"  {reason}: {c}本")
    if not load_metadata():
        print("※ metadata.csv が空なので、タスク別の基準（両手・長さ上限）と成否は判定していません")
    print(f"\n書き出し: {args.out}／合格 {len(ok)}本を {accepted_dir} にコピー")


if __name__ == "__main__":
    main()
