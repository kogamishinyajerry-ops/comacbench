"""gen_tasks_pinnacle.py — 从镜像 PINNacle 参考场生成 pinnacle.suite 任务。

上游：github.com/i207M/PINNacle（MIT，NeurIPS 2024），本地克隆锁定
  /tmp/asset_recon/PINNacle（快照克隆，非开发跟踪）。
镜像：data/pinnacle/ref/{burgers1d.dat, poisson_classic.dat}（COMSOL/FD 参考场逐字）+
  laplace_eval_points.npy / laplace_ref_u.npy（从 poisson_classic.dat 派生的评测点集与
  参考解，生成脚本见本文件 main 内嵌逻辑，可重放）。

任务形态（code_exec，exec_kind=pinnacle_rel_l2）：
  模型输出单个 ```python 脚本（PyTorch PINN，允许 numpy），在沙箱内训练并写出
  pred.npy（规格逐题声明）；判分侧加载参考场，计算 rel L2 = ||pred-ref||/||ref||，
  低于阈值满分、否则 0（阈值 = oracle 实测误差 ×3 向上取整，见各 YAML）。
  训练类任务不做双跑确定性（CPU 训练非逐位确定），robustness 权重 0。

题目集（2026-08-29，3 题；laplace 洞域版因原生 PINN 不可训练性被撤换，见 git 历史）：
  pinnacle_burgers1d        粘性 Burgers（ν=0.01/π，COMSOL 参考场，101×10 网格）
  pinnacle_helmholtz2d      Helmholtz 2D 制造解（101×101 网格，解析参考）
  pinnacle_poisson1d        Poisson 1D 解析解冒烟档（u''+sin x=0，sin x 解析参考）

用法（仓库根）：
  python3 -m runners.gen_tasks_pinnacle           # 生成/覆盖
  python3 -m runners.gen_tasks_pinnacle --check   # 只校验
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/pinnacle"
TASKS_DIR = BENCH / "tasks/pinnacle.suite"
UPSTREAM = {
    "repo": "github.com/i207M/PINNacle",
    "revision": "pinnacle@2026-08-29-clone",   # 快照克隆（MIT）
    "license": "MIT",
}

PROMPT_COMMON = """## 交付形式（严格遵守）

输出**单个 ```python 代码块**：脚本在当前工作目录训练 PINN 并写出 `pred.npy`。
- 仅允许 PyTorch（CPU）与 numpy/标准库；固定随机种子保证可复现；
- 建议显存无关：`torch.set_num_threads(4)` 控制线程；训练预算见题面（墙钟 {wall}s）；
- `pred.npy` 形状与网格规格逐题给定，判分脚本按规格加载，错形/非有限值判 0；
- 判分 = 相对误差 rel L2 = ||pred-ref||₂/||ref||₂ ≤ 阈值（阈值随题面给出，满分线）。
"""


def _burgers1d() -> tuple[str, str, dict]:
    prompt = """# PINN 基准 — 粘性 Burgers 方程（1D 非定常）

求解粘性 Burgers 方程：

    u_t + u·u_x = ν·u_xx,   ν = 0.01/π
    定义域 x ∈ [-1, 1], t ∈ [0, 1]
    初始条件 u(x, 0) = -sin(πx)
    边界条件 u(±1, t) = 0

参考解：COMSOL 高精度数值解（PINNacle ref/burgers1d.dat）。

## 输出规格

`pred.npy` 形状 **(101, 10)**：x 方向 101 个均匀点（-1 到 1，与参考场一致），
t 方向 10 列对应 t = 0.1, 0.2, …, 1.0（不含 t=0）。判分与参考场逐点相对 L2。

## 训练建议

MLP（如 2→64×4→1, tanh），Adam ~2e4 步（lr 1e-3，可分段衰减）即可达标；
固定 `torch.manual_seed(0)` + `np.random.seed(0)`。
""" + PROMPT_COMMON.format(wall=900)
    return ("pinnacle_burgers1d", prompt, {
        "pred_shape": [101, 10],
        "rel_l2_threshold": None,  # oracle 落盘后回填
    })


def _helmholtz2d() -> tuple[str, str, dict]:
    prompt = """# PINN 基准 — Helmholtz 2D（制造解）

求解 Helmholtz 方程（制造解形式）：

    Δu + k²·u = f,   k = 3,  (x, y) ∈ [-1, 1]²
    f = (k² - 2π²)·sin(πx)·sin(πy)
    边界条件 u = 0（x=±1 与 y=±1 上制造解恒为 0）
    精确解 u(x, y) = sin(πx)·sin(πy)

## 输出规格

`pred.npy` 形状 **(10201,)**：101×101 网格点（x/y 均为 linspace(-1,1,101)，
np.meshgrid(indexing="ij") 后按 C 序展平——即先变 x 后变 y），给出 u。

## 训练建议

硬边界约束 u = (1-x²)(1-y²)·N_θ(x,y) 可精确满足零边界，只需训 PDE 残差；
MLP 2→64×4→1 tanh，Adam ~1e4 步即可到 1e-3 量级；固定种子。
""" + PROMPT_COMMON.format(wall=900)
    return ("pinnacle_helmholtz2d", prompt, {
        "pred_shape": [10201],
        "rel_l2_threshold": None,
    })


def _poisson1d() -> tuple[str, str, dict]:
    prompt = """# PINN 基准 — Poisson 1D（解析解冒烟档）

求解 Poisson 方程：

    u''(x) + sin(x) = 0,   x ∈ [0, 2π]
    u(0) = 0, u(2π) = 0
    精确解 u(x) = sin(x)

## 输出规格

`pred.npy` 形状 **(256,)**：x = 256 个均匀点（0 到 2π，含端点），按升序给出 u。
判分与解析解逐点相对 L2。

## 训练建议

MLP 1→32×3→1 tanh + Adam 8e3 步即远超达标线；固定种子。
""" + PROMPT_COMMON.format(wall=600)
    return ("pinnacle_poisson1d", prompt, {
        "pred_shape": [256],
        "rel_l2_threshold": None,
    })


BUILDERS = [_burgers1d, _helmholtz2d, _poisson1d]


def task_yaml(tid: str, prompt_rel: str, prompt_sha: str, spec: dict,
              assets: list[dict], oracle_rel: str | None) -> dict:
    return {
        "id": tid,
        "registry_id": "pinnacle.suite",
        "domain": "cfd",
        "task_type": "code_exec",
        "model_profile": "plain_llm",
        "assets_revision": UPSTREAM["revision"],
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python"],
        "input": {
            "prompt_file": prompt_rel,
            "prompt_sha256": prompt_sha,
            "assets": assets,
        },
        "output_contract": ["pred.npy"],
        "reference": {
            "source": f"PINNacle ref（MIT，{UPSTREAM['revision']}）或题面解析解",
            "revision": UPSTREAM["revision"],
            "uncertainty_note": "参考场为上游高精度数值/解析解；阈值 = oracle 实测 rel L2 ×3 取整",
        },
        "grader": {
            "validity_gate": True,
            "exec_kind": "pinnacle_rel_l2",
            "pred_shape": spec["pred_shape"],
            "rel_l2_threshold": spec["rel_l2_threshold"],
            "ref_loader": f"data/pinnacle/ref/loaders/{tid}.py",
            "sandbox_inputs": spec.get("sandbox_inputs") or [],
            "oracle_source": oracle_rel,
        },
        "scoring": {
            "weights": {"physics": 0.7, "requirements": 0.3,
                        "objective": 0.0, "robustness": 0.0},
            "note": "physics=rel L2 ≤ 阈值（二值，训练类任务 CPU 非逐位确定，不做双跑）；"
                    "requirements=pred.npy 契约（存在/形状/有限值）；robustness 权重 0",
        },
        "limits": {
            "cpu": 4,
            "memory_gb": 8,
            "wall_clock_s": 900 if "poisson1d" not in tid else 600,
            "attempts": 2,
        },
        "license_provenance": {
            "source": UPSTREAM["repo"],
            "license": "MIT",
            "status": "confirmed-repo",
            "revision": UPSTREAM["revision"],
            "mirror_allowed": True,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    drift = []

    thresholds = {}
    thr_file = DATA / "thresholds.json"
    if thr_file.exists():
        thresholds = json.loads(thr_file.read_text(encoding="utf-8"))

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    for b in BUILDERS:
        tid, prompt, spec = b()
        spec = dict(spec)
        spec["rel_l2_threshold"] = thresholds.get(tid)
        assets = []
        if tid == "pinnacle_burgers1d":
            assets.append({"path": "data/pinnacle/ref/burgers1d.dat",
                           "digest": sha256_file(DATA / "ref/burgers1d.dat")})
        if spec["rel_l2_threshold"] is None:
            raise SystemExit(f"{tid}: thresholds.json 缺阈值（先跑 oracle 标定）")
        prompt_rel = f"tasks/pinnacle.suite/{tid}.md"
        sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        y = task_yaml(tid, prompt_rel, sha, spec, assets,
                      f"data/pinnacle/oracle_scripts/{tid}.py")
        want_yaml = yaml.safe_dump(y, sort_keys=False, allow_unicode=True)
        ypath = TASKS_DIR / f"{tid}.yaml"
        ppath = TASKS_DIR / f"{tid}.md"
        if args.check:
            gy = _read_no_translate(ypath)
            gp = _read_no_translate(ppath)
            if gy != want_yaml or gp != prompt:
                drift.append(tid)
        else:
            ypath.write_text(want_yaml, encoding="utf-8")
            ppath.write_text(prompt, encoding="utf-8")
    if args.check:
        if drift:
            print(f"[check] 漂移: {drift}")
            return 1
        print("[check] OK — pinnacle.suite 任务一致")
        return 0
    print(f"[gen] 写出 {len(BUILDERS)} 任务 -> {TASKS_DIR}")
    return 0


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


if __name__ == "__main__":
    raise SystemExit(main())
