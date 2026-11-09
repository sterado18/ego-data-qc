# 実験記録

| 日付 | モデル | LeRobot | 実行環境 | 試行回数 | 成功率 | 失敗の様子 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-10 | lerobot/diffusion_pusht（下記で形式変換） | 0.6.1 | Mac（mps）、seed=1000 | 10 | **60%**（6/10） | 失敗4回も最高到達度 0.96〜0.99。ほぼ押し切ったが時間切れ？（動画で確認する） |

## lerobot-eval が動くまでに詰まったこと（11/9〜11/10）

1. `Namespace gym_pusht not found`：`gym-pusht` 未導入 → `pip install gym-pusht`。入れた後も同じエラー → 既定の並列実行（AsyncVectorEnv）の子プロセスに環境の登録が引き継がれない。`--eval.use_async_envs=false` で解消
2. `'diffusers' is required`：diffusion 方策の部品が無い → `pip install 'lerobot[diffusion]==0.6.1'`（版を固定したまま追加）
3. `requires migration to processor format`：Hub のモデルが旧形式。`python -m lerobot.processor.migrate_policy_normalization --pretrained-path lerobot/diffusion_pusht --output-dir ...` で変換 → 前処理・後処理は書き出せたが、モデル本体の保存で `Couldn't encode 84` と落ちる
4. 原因：変換ツールのバグ。旧設定の `crop_shape: [84, 84]`（リスト）を `tuple[int, int]` 型の欄にそのまま入れ、保存（draccus）で型が合わない。→ `experiments/migrate_fix.py` で呼び出し時だけタプルに直して変換（LeRobot 本体は変更しない）

### 再現コマンド

```sh
python -I experiments/migrate_fix.py --pretrained-path lerobot/diffusion_pusht --output-dir <変換先>
lerobot-eval --policy.path=<変換先> --env.type=pusht --eval.n_episodes=10 --eval.batch_size=10 \
  --eval.use_async_envs=false --policy.device=mps --seed=1000 --output_dir=<出力先>
```

### 1回ごとの結果

| 回 | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 成否 | 成功 | 成功 | 成功 | 成功 | 失敗 | 失敗 | 失敗 | 成功 | 失敗 | 成功 |
| 最高到達度 | 1.00 | 1.00 | 1.00 | 1.00 | 0.98 | 0.99 | 0.96 | 1.00 | 0.99 | 1.00 |

所要：10回で 452 秒（1回 45 秒、Mac mps）。
