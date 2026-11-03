# Linux（Ubuntu）練習メモ

11/5 に Multipass の VM で打ったコマンドと、分かったことを書く。

| 知りたいこと | コマンド | 分かったこと |
| --- | --- | --- |
| 動いているプログラム | `ps aux \| grep python` | |
| サービスの状態 | `systemctl status ssh` | |
| ログ | `journalctl -u ssh -n 50` | |
| ネットワーク | `ip a` | |
| つながっている機器 | `lsusb` | |
| ディスクの空き | `df -h` | |
