"""arm_router.py — harness 臂自动路由（v0.3 生产化，2026-08-25）。

范式：模型固定（生产对 {minimax-m3, glm-5.3}），harness 臂是被测/被选变量。
本模块把 v0.3 增益矩阵的实测证据固化为**路由策略表**：给定 (模型, 基准)
推荐最优臂并直接给出可执行的 runner 命令行——生产 harness 的「臂调度器」。

证据基线（results/harness-eval-2026-08-24.md §3 矩阵 + §8 谱系化扩展）：
  minimax 家族（遵循型）：
    pycycle  H2=1.000 / H3=1.000 → H2（更省，反馈无增量）
    foam     H2=0.360 / H3=0.400 → H3
    cadgen / gtm-hard → 谱系化臂（见 SCAFFOLDS，证据随臂补齐更新本表）
  glm-5.3 家族（改写型——会偏离脚手架，需反馈修复）：
    pycycle  H2=0.300 / H3=0.900 → H3
    foam     H2=0.000 / H3=0.040 → H3（弱但为最优已知）
    cadgen   H0=0.8636 已强 → H0（臂证据补齐前不注入）
  通用事实：H1（反馈单独）四组合全零——不推荐任何模型单独用 H1。

用法：
  python3 -m runners.arm_router --provider glm --model glm-5.3 \
      --benchmark pycycle.engine_cycle           # 打印推荐与命令行
  加 --execute 直接脱离执行（起跑生产基线）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent

# 蒸馏工作流资产登记（benchmark → scaffold 路径；None=暂无谱系化资产）
SCAFFOLDS = {
    "pycycle.engine_cycle": "data/pycycle/engine_cycle/scaffold.md",
    "cfdllm.foam_basic": "data/cfdllm/foam_basic/scaffold_v2.md",   # v2 物理层
    "cadgen.local_validity": "data/cadgen/local_validity/scaffold.md",
    "gtm.transport_control_hard": "data/gtm/transport_control_hard/scaffold.md",
}

# 模型家族归类（生产对为 minimax / glm-5.x 思考型；新模型按行为归类后入表）
def _family(provider: str, model: str | None) -> str:
    m = (model or "").lower()
    if provider == "minimax":
        return "minimax"
    if provider == "glm":
        return "glm-thinking" if m.startswith(("glm-5", "glm-4.6v")) else "glm-base"
    return provider

# 策略表：(模型家族, 基准) -> (臂, 证据均分, 依据)
# 臂语义：H0=单发 H1=反馈 H2=脚手架 H3=脚手架+反馈
POLICY: dict[tuple[str, str], tuple[str, float, str]] = {
    ("minimax", "pycycle.engine_cycle"): ("H2", 1.000, "v0.3 矩阵：H2 即满分，反馈无增量"),
    ("minimax", "cfdllm.foam_basic"): ("H3", 0.400, "v0.3 矩阵：H3>H2(0.36)，物理层仍受限"),
    ("glm-thinking", "pycycle.engine_cycle"): ("H3", 0.900, "v0.3 矩阵：改写型需反馈修复（H2 仅 0.3）"),
    ("glm-thinking", "cfdllm.foam_basic"): ("H3", 0.040, "v0.3 矩阵：弱臂但为最优已知（模型入场即难）"),
    ("glm-thinking", "cadgen.local_validity"): ("H0", 0.8636, "固定对基线已强；臂证据补齐前不注入"),
    ("minimax", "cadgen.local_validity"): ("H3", 0.9792, "谱系化 2026-08-25：H2 0.9583/H3 0.9792（lbracket 0.25→0.771）；M3 反馈无反例取 H3"),
    ("glm-thinking", "cadgen.local_validity"): ("H2", 1.0000, "谱系化 2026-08-25：H2 满分 22/22（H0 0.8636→1.0）"),
    ("minimax", "gtm.transport_control_hard"): ("H2", 0.8000, "谱系化 2026-08-25：H2/H3 均 0.80（margin 族 1.0；id 族 0.25→0.50）；H2 省轮次"),
    ("glm-thinking", "gtm.transport_control_hard"): ("H2", 0.6000, "谱系化 2026-08-25：H2/H3 均 0.60（margin 1.0）；id 族=provider 长度墙(32768 截断) scaffold 不可治"),
}

# 各基准的 runner 入口（interpreter 钉子栈）
RUNNER = {
    "pycycle.engine_cycle": (".venv/bin/python", "runners.simulation_agent"),
    "cfdllm.foam_basic": (".venv/bin/python", "runners.simulation_agent"),
    "aviary.transport_mission": (".venv-aviary/bin/python", "runners.simulation_agent"),
    "cadgen.local_validity": (".venv-cad/bin/python", "runners.design_artifact"),
    "gtm.transport_control_hard": ("python3", "runners.simulation_agent"),
}


def recommend(provider: str, model: str | None, benchmark: str,
              iterate_default: int = 3) -> dict:
    """返回 {arm, scaffold, evidence, command, env}。未知组合回退 H3+已知 scaffold。"""
    fam = _family(provider, model)
    arm, score, why = POLICY.get((fam, benchmark),
                                 ("H3", None, "无实测证据——回退默认 H3（安全上界：H3⊇H2）"))
    scaffold = SCAFFOLDS.get(benchmark)
    if arm == "H0":
        scaffold = None
    interp, module = RUNNER.get(benchmark, ("python3", "runners.simulation_agent"))
    label = model or provider
    out = f"results/{benchmark}/routed/{label}-{arm}"
    argv = [interp, "-m", module, "--tasks", f"tasks/{benchmark}",
            "--out", out, "--provider", provider, "--seed", "0", "--resume"]
    if model:
        argv += ["--model", model]
    if arm in ("H1", "H3"):
        argv += ["--iterate", str(iterate_default)]
    if arm in ("H2", "H3") and scaffold:
        argv += ["--scaffold", scaffold]
    return {"family": fam, "arm": arm, "evidence_score": score, "why": why,
            "scaffold": scaffold,
            "command": f"cd {BENCH} && PYTHONPATH=runners/vendor_shim/pyvista_shim "
                       + " ".join(argv) if benchmark.startswith("aviary")
            else f"cd {BENCH} && " + " ".join(argv),
            "argv": argv, "interpreter": interp}


def main() -> int:
    ap = argparse.ArgumentParser(description="harness 臂路由器（v0.3 生产化）")
    ap.add_argument("--provider", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--benchmark", required=True)
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()
    r = recommend(args.provider, args.model, args.benchmark)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print(f"模型家族: {r['family']}")
    print(f"推荐臂:   {r['arm']}" + (f"（证据: {r['evidence_score']}）" if r["evidence_score"] is not None else "（回退）"))
    print(f"依据:     {r['why']}")
    print(f"scaffold: {r['scaffold'] or '—'}")
    print(f"命令:\n  {r['command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
