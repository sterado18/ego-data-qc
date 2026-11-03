"""scores.csv から品質レポートの下書きを作る（手順4）。

使い方:
  .venv/bin/python scripts/report.py --work-hours 12   # 撮影〜検品にかかった自分の作業時間

出力: reports/quality_report.md。1〜3と5は自動で埋まり、4・6・7は自分で書く。
"""
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from common import ROOT, SCORES


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default=SCORES, type=Path)
    ap.add_argument("--work-hours", type=float, help="撮影から検品までの自分の作業時間（時間）")
    ap.add_argument("--out", default=ROOT / "reports" / "quality_report.md", type=Path)
    args = ap.parse_args()

    with open(args.scores, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["sec"] = float(r["sec"])
    ok = [r for r in rows if r["accepted"] == "yes"]
    total_min = sum(r["sec"] for r in rows) / 60
    ok_min = sum(r["sec"] for r in ok) / 60

    lines = ["# 品質レポート", "",
             "## 1. サマリー", "",
             f"撮影総時間 {total_min:.1f} 分、エピソード数 {len(rows)}、合格 {len(ok)}、"
             f"不採用率 {1 - len(ok) / len(rows):.0%}、受入時間 {ok_min:.1f} 分。"
             f"合格のうち失敗例（予定どおりの失敗をラベル付きで採用）{sum(r.get('success') == '失敗' for r in ok)} 本", "",
             "## 2. タスク別の結果", "",
             "| タスク | 本数 | 合格率 | 平均の長さ（秒） |", "| --- | --- | --- | --- |"]
    by_task = defaultdict(list)
    for r in rows:
        by_task[r["task"] or "（未記入）"].append(r)
    for task, rs in sorted(by_task.items()):
        rate = sum(r["accepted"] == "yes" for r in rs) / len(rs)
        avg = sum(r["sec"] for r in rs) / len(rs)
        lines.append(f"| {task} | {len(rs)} | {rate:.0%} | {avg:.1f} |")

    lines += ["", "## 3. 不採用の理由別件数", "",
              "1本に複数の理由が付くことがあるので、合計は不採用の本数より多くなることがある。", "",
              "| 理由 | 本数 |", "| --- | --- |"]
    counts = Counter(x for r in rows for x in r["reasons"].split("／") if x)
    lines += [f"| {k} | {v} |" for k, v in counts.most_common()] or ["| なし | 0 |"]

    lines += ["", "## 4. 見本の画像", "",
              "合格例2枚・不採用例2枚。`scripts/overlay.py <動画> --still <秒>` で作った静止画を貼る。", "",
              "## 5. 原価の手応え", ""]
    if args.work_hours and ok_min:
        lines.append(f"作業時間 {args.work_hours:g} 時間 ÷ 受入時間 {ok_min / 60:.2f} 時間 ＝ "
                     f"受入1時間あたり {args.work_hours / (ok_min / 60):.1f} 時間")
    else:
        lines.append("作業時間 [ ] 時間 ÷ 受入時間 [ ] 時間 ＝ 受入1時間あたり [ ] 時間"
                     "（`--work-hours` を付けると自動で計算する）")
    lines += ["", "受入率（合格した時間 ÷ 撮影した時間）は "
              f"{ok_min / total_min:.0%}。必要な撮影量 ＝ 目標の受入時間 ÷ 受入率。" if total_min else "",
              "", "## 6. 次に不採用率を下げる打ち手", "", "- ", "",
              "## 7. 分からなかったこと", "", "1. ", "2. ", "3. ", ""]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"書き出し: {args.out}")


if __name__ == "__main__":
    main()
