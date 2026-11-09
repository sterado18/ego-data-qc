# LeRobot 0.6.1 の変換ツールは、旧設定の crop_shape=[84,84]（リスト）をそのまま
# tuple[int,int] 型の欄に入れて保存に失敗する。呼び出し時だけタプルに直して回す。
import sys
import lerobot.processor.migrate_policy_normalization as m

_orig = m.make_policy_config
def make_policy_config(policy_type, **kw):
    for k, v in kw.items():
        if k.endswith("_shape") and isinstance(v, list):
            kw[k] = tuple(v)
    return _orig(policy_type, **kw)
m.make_policy_config = make_policy_config

sys.argv = ["migrate", *sys.argv[1:]]
m.main()
