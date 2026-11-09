# Linux（Ubuntu）練習メモ

11/5 に Multipass の VM で打ったコマンドと、分かったことを書く。

環境：Mac（Apple Silicon）上の Multipass 1.16.4、Ubuntu 24.04.5 LTS（aarch64）、CPU 2・メモリ 4GB・ディスク 20GB。

```sh
multipass launch 24.04 --name ego --cpus 2 --memory 4G --disk 20G   # 既定（1GB/5GB）だと動画処理に足りない
multipass shell ego
```

| 知りたいこと | コマンド | 分かったこと |
| --- | --- | --- |
| 動いているプログラム | `ps aux \| grep python` | 何も起動していないのに python が1つ動いていた（OS の自動更新 `unattended-upgrades`）。grep 自身も行として出る |
| サービスの状態 | `systemctl status ssh` | `Active: active (running)` なら生きている。`disabled` なのに動いているのは、`ssh.socket` が接続を受けたときに起動する仕組みだから |
| ログ | `journalctl -u ssh -n 50` | `Accepted publickey for ubuntu` が2回。起動時の Multipass の接続と、自分の `multipass shell`。ログは「いつ・誰が」を後から追える |
| ネットワーク | `ip a` | `lo` は自分自身（127.0.0.1）、`enp0s1` が外向き。`192.168.252.2` が Mac からこの VM を呼ぶ住所 |
| つながっている機器 | `lsusb` | 何も出ない。VM には Mac の USB が見えない。実機ならカメラ等がここに出る |
| ディスクの空き | `df -h` | `/` が 19G 中 17G 空き。作ったとおり |

## つまずいたこと

- `q` は `systemctl` / `journalctl` の画面（ページャ）の中で押すもの。シェルに戻ってから打つと `Command 'q' not found` になる。抜けるのは `Ctrl+C` でもよい。

## 11/9 VM で再現（setup.sh → score.py）

- `setup.sh` は通ったが、`check_env.py` で `libEGL.so.1` が無いと落ちた。MediaPipe は画面のない Ubuntu でも描画用ライブラリを使う → `libegl1 libgles2` を setup.sh に追加。
- iPhone の HEVC（.MOV）は Linux 版 OpenCV でもそのまま読めた。
- 動画は `multipass transfer` でコピーし、sha256 が Mac 側と全件一致することを確認。
- `score.py` の合否は Mac と5本とも一致（合格3／C の2本がブレで不合格）。
- 数値は少しずれた（手の写り率で最大 +0.012、シャープネス ±0.2）。原因はライブラリのバージョン差（Mac: OpenCV 4.13.0 / MediaPipe 1.1.1、VM: 5.0.0 / 1.2.2）。`requirements.txt` を固定した。
- `git diff` の `^M` は CSV の改行コード（CRLF）の表示。Mac 側も同じで差ではない。
