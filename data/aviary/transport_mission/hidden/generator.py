"""隐藏动态题生成器（aviary.transport_mission，M3 评审件）。

采样策略（版本化进 git）：
  - 参数空间：range ∈ [2200, 3800] NM（步长 50）、cruise Mach ∈ [0.72, 0.82]（步长 0.005）、
    设计总重 ∈ [165400, 185400] lbm（步长 1000）；
  - 种子：SAMPlING_SEED（每轮评测可轮换；轮换后须重跑本生成器重锁参考）；
  - 题目参数三元组均匀无放回采样；
  - 参考答案：gold 分析模式预计算 → base64 隔离存 answers.b64（不明文入库，
    满足 scoring/README.md §5「采样种子与参考答案不明文入库」）；
  - 泄漏监控：每轮统计 hidden-public 分差（report 汇总层），分差收窄触发轮换。
"""
import base64
import json
import random

SAMPLING_SEED = 20260819
N_SAMPLES = 3  # 试点规模；正式轮可扩

ranges = list(range(2200, 3801, 50))
machs = [round(0.72 + 0.005 * i, 3) for i in range(21)]
masses = list(range(165400, 185401, 1000))

rng = random.Random(SAMPLING_SEED)
combos = [(r, m, g) for r in ranges for m in machs for g in masses]
rng.shuffle(combos)
picked = combos[:N_SAMPLES]

payload = {"seed": SAMPLING_SEED, "combos": picked,
           "answers": {f"h{i+1}": None for i in range(N_SAMPLES)}}
print(json.dumps(payload, indent=1))
# answers 由外部 gold 预计算后填入并 base64 落盘（见 README.md）
