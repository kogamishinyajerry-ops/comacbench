"""隐藏动态题生成器（gtm.transport_control_hard，H5 族，评审件）。

采样策略（版本化）：
  - 参数空间：box 百分比 pct ∈ {0.15, 0.20, ..., 0.45}、
    目标 SP (wn ∈ {1.8,1.9,...,2.5} × ζ ∈ {0.50,0.52,...,0.64})、
    采样种子 seed ∈ 固定递增序列；
  - 种子：SAMPLING_SEED（每轮评测可轮换；轮换后须重跑本生成器重锁参考）；
  - 题目参数三元组 (pct, wn_cl, z_cl, seed) 无放回采样；
  - 参考答案：gold 分析模式预计算 → base64 隔离存 answers.b64（不明文入库）。
"""
import base64
import json
import random

SAMPLING_SEED = 20260823
N_SAMPLES = 3

rng = random.Random(SAMPLING_SEED)
pcts = [round(0.15 + 0.05 * i, 2) for i in range(7)]
wns = [round(1.8 + 0.1 * i, 1) for i in range(8)]
zs = [round(0.50 + 0.02 * i, 2) for i in range(8)]
seeds = list(range(21000000, 21000000 + 64))
combos = [(p, w, z, s) for p in pcts for w in wns for z in zs for s in seeds]
rng.shuffle(combos)
picked = combos[:N_SAMPLES]
payload = {"seed": SAMPLING_SEED, "combos": picked}
print(json.dumps(payload, indent=1))
