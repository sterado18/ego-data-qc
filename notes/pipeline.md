# 動画を渡してから結果が出るまで（自分で回す手順書）

## 全体の流れ

```
① 取り込み確認 → ② 中身の目視 → ③ metadata.csv に記録 → ④ score.py で採点 → ⑤ 比較・集計
```

## ① 取り込み確認：本数と順番が合っているか

```sh
cd data/raw
for f in IMG_*.MOV; do
  ffprobe -v error -show_entries format_tags=creation_time:format=duration \
    -of default=nw=1:nk=1 "$f" | tr '\n' ' '; echo " $f"
done
```

- `ffprobe` は動画の情報を読む道具。**長さ（秒）**と**撮影時刻**を出す。
- 見るのは「本数が表と同じか」「番号順＝撮影時刻順か」「抜け番（消した撮り損ね）がどこか」。

## ② 中身の目視：表のとおりの物・場所か

```sh
f=IMG_0533.MOV
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
ffmpeg -v error -ss $(python3 -c "print($d*0.5)") -i "$f" -frames:v 1 -vf scale=400:-2 /tmp/0533.jpg
# 複数枚を1枚に並べる（4列×3行）
ffmpeg -pattern_type glob -i '/tmp/*.jpg' -vf "tile=4x3:padding=6:color=white" /tmp/sheet.jpg
```

- 各動画の途中（50% の位置など）から1コマ切り出し、一覧にして見る。
- 見るのは「物・置く場所・タスクの切り替わり」。**ラベル違いはここで止める**（学習データで一番まずいミス）。
- 画像には自宅が写るので、見終わったら消す。

## ③ metadata.csv に記録

- 1行＝1エピソード。`file_name`（どの動画か）、`instruction`（何をしたか）、`success`（成功／失敗）、`intended_failure`（わざとの失敗か）、`notes`（代用・順番の入れ替えなど計画との違い）を**実際に撮ったとおり**に書く。
- `score.py` は `file_name` で動画と行をつなぎ、`task`（A/B/C）と成否を読む。

## ④ score.py で採点：1コマずつ測って割合にする

```sh
.venv/bin/python scripts/score.py --out reports/scores_round1.csv
```

1本の動画（30fps なら7秒で約210コマ）を1コマずつ読み、各コマで次を測る。

| 列 | 何を測るか | どう測るか | 合格の基準 |
| --- | --- | --- | --- |
| `hand` | 手が写っているコマの割合 | MediaPipe（手の位置を推定するモデル）が手を1つ以上見つけたコマ ÷ 調べたコマ。速さのため3コマに1回だけ調べる | 70% 以上 |
| `both` | 両手が写っているコマの割合 | 手を2つ見つけたコマ ÷ 調べたコマ | 50% 以上（B だけ） |
| `blur` | ブレたコマの割合 | 白黒にして、輪郭を強調するフィルタ（ラプラシアン）をかけ、その値のばらつき（分散）を「鮮明さ」とする。30 未満のコマをブレとみなす | **合否に使わない**。20% を超えたら `review` 列に「要目視：ブレ」 |
| `light` | 暗すぎ・明るすぎのコマの割合 | 白黒の平均（0＝真っ黒〜255＝真っ白）が 40〜220 の外 | 10% 以下 |
| `sec` | 長さ | コマ数 ÷ fps | 5秒以上、タスクの上限の2倍以内 |
| `sharp_median` | 鮮明さの中央値 | 全コマの鮮明さの真ん中の値（判定には使わない、原因調べ用） | — |

- 1つでも基準を外れたら不合格。外れた項目が `reasons` に入る。
- ブレは「要目視」の印だけ付ける。鮮明さは輪郭の量なので、無地の床や黒い袖が多い画面でも低く出る。人の目で付けた正解20コマと旧判定の一致は 4/18 だった（11/16 の検証）。
- わざとの失敗（`intended_failure=yes`）は、品質が基準を満たせば「失敗例」として合格。
- 合格した動画は `data/accepted/` にコピーされる（S3 に送る元）。

### 数字の読み方の例（第1ラウンド A003）

```
A003  sec 7.2  hand 0.667  blur 0.009  → 不合格：手の映り不足
```

7.2秒中、手が写っていたのは 67%（基準 70%）。前後1秒ずつの待ち時間は手が写らないので、7秒の動画では最大でも約71%。→ 撮り方より「待ち時間と基準の噛み合わせ」が原因と読める。

## ⑤ 比較・集計

```sh
python3 - <<'EOF'
import csv
r1 = {r["episode_id"]: r for r in csv.DictReader(open("reports/scores_round1.csv", encoding="utf-8-sig"))}
r2 = {r["episode_id"]: r for r in csv.DictReader(open("reports/scores_round2.csv", encoding="utf-8-sig"))}
for e, b in r2.items():
    a = r1[e.replace("_r2", "")]
    print(e, "hand", a["hand"], "→", b["hand"], "blur", a["blur"], "→", b["blur"], a["accepted"], "→", b["accepted"])
EOF
```

- 同じエピソードの第1・第2ラウンドを横に並べ、**どの数字が動いたか**を見る。
- 合否だけでなく、元の数字（hand・blur・sharp_median）まで見ると、「撮り方が悪いのか、測り方が場面に合っていないのか」を切り分けられる。
