# 実験記録

| 日付 | モデル | LeRobot | 実行環境 | 試行回数 | 成功率 | 失敗の様子 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-09 | lerobot/diffusion_pusht | 0.6.1 | Mac（mps） | 10（未完） | | 推論まで届かず（下記） |

## 2026-11-09 lerobot-eval が動くまでに詰まったこと

1. `Namespace gym_pusht not found`：`gym-pusht` 未導入 → `pip install gym-pusht`。入れた後も同じエラー → 既定の並列実行（AsyncVectorEnv）の子プロセスに環境の登録が引き継がれない。`--eval.use_async_envs=false` で解消
2. `'diffusers' is required`：diffusion 方策の部品が無い → `pip install 'lerobot[diffusion]==0.6.1'`（版を固定したまま追加）
3. `requires migration to processor format`：Hub のモデルが旧形式。`python -m lerobot.processor.migrate_policy_normalization --pretrained-path lerobot/diffusion_pusht --output-dir ...` で変換 → 前処理・後処理は書き出せたが、モデル本体の保存で止まり未解決
