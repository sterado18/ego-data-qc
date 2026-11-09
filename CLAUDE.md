# CLAUDE.md — ego-data-qc

## このリポジトリの目的
リアルワールド株式会社（RLWRLD）の「Robot Data Curator（業務委託）」に応募するための公開ポートフォリオ。
一人称映像の検品（正常／異常の仕分け）、S3 転送の完全性確認、学習済みモデルの推論記録を、求人の業務内容に合わせてミニチュアで実演する。
応募予定日：2026-11-20（11/9 に引き直し）。計画書：https://claude.ai/artifact/5PojKKBTLLVnJP3yipDEB8

## 持ち主について
寺戸颯介。ロボット学習の初学者。説明は噛み砕いて、コマンドは何をしているかを添えること。
Python・AWS は実務経験あり。Ubuntu は練習中。

## 絶対に守ること
- **公開リポジトリ**。動画（.MOV/.mp4）、data/raw、自宅が分かる画像は commit しない。commit 前に `git status` で確認する。
- 非公開の事業資料は `~/business/physical-ai-data/` にある。そこのファイル（調査メモ・事業モデル・契約の読み解き等）をこのリポジトリにコピーしない。
- 元の作業場は `~/business/physical-ai-data/03_検証_自分で一周回す/`（動画・venv・LeRobot 0.6.1 はそちら）。このリポジトリの scripts はそこからコピーし、パスを英語に置き換えたもの。

## 構成
- scripts/：common.py（パス・手の検出）、score.py（採点）、report.py、overlay.py、convert.py（LeRobot 形式）、check_env.py
- data/metadata.csv：撮影計画と来歴（80本計画、撮影済み5本）
- reports/scores.csv：採点結果
- setup.sh / verify_upload.sh：Ubuntu で再現・S3 照合
- notes/linux.md、experiments/log.md：練習と実験の記録

## 残りの予定（計画書の日別の作業）
- ✅ 11/5 Ubuntu（Multipass）で基本操作 → notes/linux.md
- ✅ 11/9 VM で setup.sh → score.py、Mac と合否一致を確認 → notes/linux.md
- ✅ 11/9 verify_upload.sh 完成、S3（ego-data-qc-sterado18）で件数・容量・指紋 OK
- 11/10 lerobot-eval で PushT 推論（モデル形式の変換で停止中）→ experiments/log.md
- 11/11 予備日
- 11/12 撮影の段取り（30本のタスクと順番を metadata.csv で確定）
- 11/14 30本撮影 → 不採用率を理由別に集計
- 11/15 1点だけ変えて15本撮り直し → 比較と起票表
- 11/16〜17 README の数字と「分からなかったこと」を埋め、検証レポート PDF
- 11/18〜19 職務経歴書・履歴書・メッセージ
- 11/20 応募
