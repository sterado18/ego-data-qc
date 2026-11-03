#!/usr/bin/env bash
# verify_upload.sh — 送ったデータが全部・壊れずに届いたかを確かめる（11/8 に完成させる）
# 使い方: BUCKET=自分のバケット名 bash verify_upload.sh
set -euo pipefail
SRC="data/accepted"
DEST="s3://${BUCKET:?BUCKET を指定してください}/ego_pilot/$(date +%F)"
SUM="shasum -a 256"; command -v sha256sum >/dev/null && SUM="sha256sum"

(cd "$SRC" && $SUM * | sort) > manifest_local.txt
aws s3 sync "$SRC" "$DEST"
TMP=$(mktemp -d)
aws s3 sync "$DEST" "$TMP"
(cd "$TMP" && $SUM * | sort) > manifest_remote.txt

N_LOCAL=$(ls "$SRC" | wc -l | tr -d ' '); N_REMOTE=$(ls "$TMP" | wc -l | tr -d ' ')
KB_LOCAL=$(du -sk "$SRC" | cut -f1); KB_REMOTE=$(du -sk "$TMP" | cut -f1)
RESULT=NG; diff -q manifest_local.txt manifest_remote.txt >/dev/null && RESULT=OK
echo "件数 $N_LOCAL → $N_REMOTE / 容量 ${KB_LOCAL}KB → ${KB_REMOTE}KB / 指紋 $RESULT"
[ -f transfer_log.csv ] || echo "datetime,dest,files,kb,checksum" > transfer_log.csv
echo "$(date '+%F %T'),$DEST,$N_LOCAL,$KB_LOCAL,$RESULT" >> transfer_log.csv
