"""code_exec.py — 科学代码执行 adapter（五类标准 adapter 之二，YAML 驱动）。

适用（adapters/README.md §2）：scicode.physics、cfdllm.cfdcode、humaneval.python、mbpp.sanitized。
判分管线（严格顺序）：
  1. ValidityGate：静态沙箱检查违规（sandbox_escape_attempt）/ 代码不可执行 /
     缺 output_contract 产物（cfdcode 的 .npy）/ 场值非物理（NaN/Inf）=> gate=0；
  2. executability（requirements）：代码可导入、入口可调用；
  3. hidden_tests + numerical_tolerance（physics）：
     - scicode：逐步骤官方 assert 语义（h5 期望值 + 数据集原始断言行），逐 case 判；
     - cfdcode：官方比对语义（形状插值对齐 + MSE/MAE/RMSE/Cosine/R²/NMSE），
       physics = mean(clamp01(Cosine), clamp01(R²)) 按变量均值；
     - unit_tests（humaneval/mbpp）：隐藏断言逐条执行，physics = case 通过率，
       另报 pass@1（全断言通过任务占比，与社区口径直接可比）；
  4. stability（objective）：数据集无边界输入测试 => N/A（权重 0，YAML 声明）；
  5. determinism（robustness）：两次独立执行结果一致（scicode/unit_tests 比对逐 case
     通过模式，cfdcode 比对 npy allclose）。

沙箱强度（dev 终端，如实声明）：静态 AST 审查 + `python -I` 隔离解释器 + 临时工作目录
+ 墙钟超时；非 OS 级强制隔离（macOS 无 RLIMIT_AS），intranet 移植换容器执行。

CLI：
  cd benchmarks && python3 -m runners.code_exec \
      --tasks tasks/scicode.physics --out results/scicode.physics/<date>/<provider> \
      --provider minimax --model MiniMax-M3 --seed 0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.ndimage import zoom
from sklearn.metrics import r2_score
from sklearn.metrics.pairwise import cosine_similarity

from . import common
from .common import (FM_MISSING_OUTPUT, TaskSpec, aggregate_score,
                     build_result, environment_digest, gate_distribution,
                     load_tasks)
from .providers import ProviderError, get_answer
from .sandbox import IsolatedRun, static_check

ADAPTER = "code_exec"
DEFAULT_WEIGHTS = {"physics": 0.35, "requirements": 0.30,
                   "objective": 0.20, "robustness": 0.15}

RUNNERS_DIR = Path(__file__).resolve().parent
USER_SITE = Path.home() / ".local/lib/python3.12/site-packages"  # h5py 所在（-I 排除 user site）

_SANDBOX_ESCAPE = "sandbox_escape_attempt"
_NOT_PHYSICAL = "non_physical_values"
_EXEC_FAIL = "code_not_executable"


# ---------------------------------------------------------------- assembly

def _assemble_scicode(task: TaskSpec, model_code: str, h5_path: Path) -> str:
    deps = task["grader"]["dependencies"]
    steps = task["grader"]["steps"]
    vendor = RUNNERS_DIR / "vendor_shim"
    # scipy 兼容前置：数据集依赖声明使用老 API（simps 于 scipy>=1.14 改名 simpson，
    # 官方环境为旧版）。可信侧别名，保持数据集原文不动。
    compat = (
        "import scipy.integrate as _si\n"
        "if not hasattr(_si, 'simps') and hasattr(_si, 'simpson'):\n"
        "    _si.simps = _si.simpson\n"
    )
    harness = f"""
import sys as _sys
_sys.path.insert(0, {str(RUNNERS_DIR)!r})
_sys.path.insert(0, {str(vendor)!r})          # scicode.compare.cmp shim（官方测试用例引用）
_sys.path.insert(0, {str(USER_SITE)!r})
{compat}
{deps}
# ==== 被测代码（模型输出） ====
{model_code}
# ==== 判分 harness（可信侧） ====
import json as _json
from _scicode_h5 import load_targets
_results = []
"""
    for st in steps:
        sid, n = st["step_id"], int(st["n_cases"])
        cases = st["test_cases"]
        # 官方语义：同一步的全部 case 在同一命名空间顺序执行（case 间变量共享，
        # 如 7.1 case4 引用 case1 定义的 image_array、10.1 case4 引用 L）
        harness += f"""
_step_ns = dict(globals())
try:
    _targets = load_targets({str(h5_path)!r}, {sid!r}, {n})
except Exception as _e:
    _results.append({{"step": {sid!r}, "error": f"targets load: {{_e}}"}})
else:
    for _i, (_case, _tgt) in enumerate(zip({cases!r}, _targets)):
        _step_ns['target'] = _tgt
        try:
            exec(_case, _step_ns)
            _results.append({{"step": {sid!r}, "case": _i + 1, "pass": True}})
        except Exception as _e:
            _results.append({{"step": {sid!r}, "case": _i + 1,
                              "pass": False, "err": f"{{type(_e).__name__}}: {{_e}}"[:200]}})
    globals().update({{k: v for k, v in _step_ns.items() if not k.startswith('_')}})
"""
    harness += "\nprint('@@RESULTS@@' + _json.dumps(_results))\n"
    return harness


def _assemble_cfdcode(model_code: str) -> str:
    return ("import sys as _sys\n"
            f"_sys.path.insert(0, {str(USER_SITE)!r})\n"
            "# ==== 被测代码（模型输出） ====\n"
            f"{model_code}\n")


def _assemble_unit_tests(task: TaskSpec, model_code: str) -> str:
    """humaneval/mbpp 型：模型代码 + 隐藏断言逐条执行（@@RESULTS@@ JSON 回传）。

    - test_imports 置顶（mbpp 官方 test_imports，humaneval 为空）；
    - 每条 case 在 globals() 快照内 exec——单条崩溃不中断其余 case
      （与 scicode 同步骤内 case 共享命名空间的语义一致：对象级状态仍共享）；
    - 官方 check(entry_point) 整块语义在生成器侧拆分为逐断言 case
      （helper 定义逐 case 前置；拆分失败回退整块单 case，见 gen_tasks_humaneval.py）。
    """
    imports = "\n".join(task["grader"].get("test_imports") or [])
    tests_repr = repr(list(task["grader"]["tests"]))
    return (
        imports + "\n"
        "# ==== 被测代码（模型输出） ====\n"
        + model_code + "\n"
        "# ==== 判分 harness（可信侧） ====\n"
        "import sys as _sys_h\n"
        "if hasattr(_sys_h, 'set_int_max_str_digits'):\n"
        "    _sys_h.set_int_max_str_digits(0)   # plus 批量 case 内嵌大整数字面量\n"
        "import json as _json\n"
        "_results = []\n"
        "def _run_case(_idx, _src):\n"
        "    _ns = dict(globals())\n"
        "    try:\n"
        "        exec(_src, _ns)\n"
        '        return {"case": _idx, "pass": True}\n'
        "    except Exception as _e:\n"
        '        return {"case": _idx, "pass": False, '
        '"err": f"{type(_e).__name__}: {_e}"[:200]}\n'
        "_tests = " + tests_repr + "\n"
        "for _i, _t in enumerate(_tests):\n"
        "    _results.append(_run_case(_i + 1, _t))\n"
        "print('@@RESULTS@@' + _json.dumps(_results))\n"
    )


# ---------------------------------------------------------------- grading helpers

def _grade_scicode_results(rows: list[dict]) -> dict[str, Any]:
    per_step: dict[str, dict[str, int]] = {}
    for r in rows:
        key = r.get("step", "case")   # unit_tests 行无 step 字段 -> 单组
        if "error" in r:
            per_step.setdefault(key, {"pass": 0, "total": 0})
            continue
        d = per_step.setdefault(key, {"pass": 0, "total": 0})
        d["total"] += 1
        d["pass"] += 1 if r.get("pass") else 0
    total_cases = sum(d["total"] for d in per_step.values())
    passed = sum(d["pass"] for d in per_step.values())
    steps_all_pass = sum(1 for d in per_step.values() if d["total"] and d["pass"] == d["total"])
    return {"per_step": per_step, "cases_pass": passed, "cases_total": total_cases,
            "steps_all_pass": steps_all_pass, "steps_total": len(per_step)}


def _interp_match(gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
    if gt.shape == pred.shape:
        return pred
    factors = np.array(gt.shape) / np.array(pred.shape)
    return zoom(pred, factors, order=1)


def _grade_one_field(gt: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    """官方 compute_losses 语义 + 形状插值。"""
    if gt.ndim == 1:
        gt = gt[:, np.newaxis]
    if pred.ndim == 1:
        pred = pred[:, np.newaxis]
    pred = _interp_match(gt, pred)
    if gt.shape != pred.shape:
        raise ValueError(f"shape mismatch after interpolation: {gt.shape} vs {pred.shape}")
    g, p = gt.flatten(), pred.flatten()
    mse = float(np.mean((g - p) ** 2))
    mae = float(np.mean(np.abs(g - p)))
    rmse = float(np.sqrt(mse))
    # 零范数守卫：双方均为（数值上）零向量时余弦无定义；相同零场记 1.0
    # （实测 gold 2D_Navier_Stokes_Channel 的 v 为全零场，官方实现返回 Cosine=0 属退化）
    g_norm, p_norm = float(np.linalg.norm(g)), float(np.linalg.norm(p))
    if g_norm < 1e-12 and p_norm < 1e-12:
        cos = 1.0
    elif g_norm < 1e-12 or p_norm < 1e-12:
        cos = 0.0
    else:
        cos = float(cosine_similarity(g.reshape(1, -1), p.reshape(1, -1))[0][0])
    r2 = float(r2_score(g, p))
    nmse = mse / float(np.mean(g ** 2)) if np.mean(g ** 2) != 0 else float("inf")
    return {"MSE": mse, "MAE": mae, "RMSE": rmse, "Cosine": cos,
            "R2": r2, "NMSE": nmse,
            "score01": round((max(0.0, min(1.0, cos)) + max(0.0, min(1.0, r2))) / 2, 4)}


# ---------------------------------------------------------------- per-task

def run_task(
    task: TaskSpec, *, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str], assets_root: Path,
    oracle_cache: dict[str, str] | None,
) -> dict[str, Any]:
    t0 = time.time()
    prompt = prompt_cache[task.id]
    kind = task["grader"]["exec_kind"]
    timeout = float(task["limits"]["wall_clock_s"])

    # ---- 模型代码 ----
    if provider == "oracle":
        if kind == "cfdcode_problem":
            # oracle 特判：gold 源码保存约定（results/{var}_{name}.npy，绝对路径派生）
            # 与任务契约（{var}.npy 于 cwd）不同 => 注入锁定 gold npy 为被测产物。
            # 验证对象 = grader（gate/插值比对/指标/确定性）；gold 源码执行路径
            # 已在预计算阶段验证（PROVENANCE.md）。
            save_values = list(task["grader"]["save_values"])
            gold_dir = assets_root / task["grader"]["gold_dir"]
            prefix = task["grader"]["gold_prefix"]
            lines = ["# oracle: 将锁定 gold 输出复制为契约交付物", "import shutil"]
            for v in save_values:
                src = repr(str(gold_dir / f"{v}_{prefix}.npy"))
                dst = repr(f"{v}.npy")
                lines.append(f"shutil.copy({src}, {dst})")
            code = "\n".join(lines)
            meta = {"provider": "oracle", "note": "cfdcode gold-npy injection"}
        else:
            code = oracle_cache[task.id]
            meta = {"provider": "oracle", "note": "dev gold source"}
    else:
        out = get_answer(provider, task, prompt, seed=seed, model=model,
                         max_attempts=int(task["limits"]["attempts"]), expect="code")
        code, meta = out["answer"], out["meta"]

    # 静态沙箱检查只针对不可信模型输出；oracle 为 grader 侧可信代码，跳过
    if provider == "oracle":
        violations, syntax_ok = [], True
    else:
        violations, syntax_ok = static_check(code)
    logs = [f"violations={violations}", f"syntax_ok={syntax_ok}"]

    if violations:
        return build_result(
            task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=[_SANDBOX_ESCAPE], subscores={"physics": 0.0,
            "requirements": 0.0, "objective": None, "robustness": 0.0},
            score=0.0, artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                                  "model_meta": json.dumps(meta, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0, "grade_s": 0.0},
            env_digest=env_digest, logs=logs + ["sandbox escape -> score 0 + 告警"],
            failure_mode=_SANDBOX_ESCAPE,
            applicability={"physics": "hidden_tests+numeric",
                           "requirements": "executability",
                           "objective": "N/A(数据集无边界输入测试)",
                           "robustness": "determinism(2 runs)"})

    if not syntax_ok:
        return build_result(
            task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=[_EXEC_FAIL], subscores={"physics": 0.0, "requirements": 0.0,
            "objective": None, "robustness": 0.0}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0, "grade_s": 0.0},
            env_digest=env_digest, logs=logs + ["syntax error"],
            failure_mode=_EXEC_FAIL,
            applicability={"requirements": "executability", "physics": "hidden_tests"})

    # ---- 组装 + 首次执行 ----
    iso = IsolatedRun()
    grade_t0 = time.time()
    if kind == "scicode_problem":
        h5_path = assets_root / "data/scicode/physics/test_data.h5"
        script = iso.write("candidate.py", _assemble_scicode(task, code, h5_path))
        r1 = iso.run(script, timeout)
        logs.append(f"run1 exit={r1['exit']} {r1['duration_s']}s")
        results_rows = None
        if r1["exit"] == 0:
            for ln in r1["stdout"].splitlines():
                if ln.startswith("@@RESULTS@@"):
                    results_rows = json.loads(ln[len("@@RESULTS@@"):])
        if results_rows is None:
            return build_result(
                task=task, adapter=ADAPTER, validity_gate=0,
                gate_failures=[_EXEC_FAIL if not r1["timeout"] else "timeout"],
                subscores={"physics": 0.0, "requirements": 0.0, "objective": None,
                           "robustness": 0.0}, score=0.0,
                artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                           "stderr_tail": json.dumps(r1["stderr"][-1500:], ensure_ascii=False)},
                timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                         "grade_s": time.time() - grade_t0},
                env_digest=env_digest, logs=logs + [f"stderr: {r1['stderr'][-300:]}"],
                failure_mode=_EXEC_FAIL if not r1["timeout"] else "timeout",
                applicability={"requirements": "executability"})
        # 可执行性 = 判分 harness 完整跑通（模型函数可导入可调用）
        exec_ok = True
        g = _grade_scicode_results(results_rows)
        # ---- 确定性：第二次执行 ----
        iso2 = IsolatedRun()
        script2 = iso2.write("candidate.py", _assemble_scicode(task, code, h5_path))
        r2 = iso2.run(script2, timeout)
        rows2 = None
        if r2["exit"] == 0:
            for ln in r2["stdout"].splitlines():
                if ln.startswith("@@RESULTS@@"):
                    rows2 = json.loads(ln[len("@@RESULTS@@"):])
        det = None
        if rows2 is not None:
            pat1 = [(x.get("step"), x.get("case"), bool(x.get("pass"))) for x in results_rows]
            pat2 = [(x.get("step"), x.get("case"), bool(x.get("pass"))) for x in rows2]
            det = 1.0 if pat1 == pat2 else 0.0
        subscores = {
            "requirements": 1.0 if exec_ok else 0.0,
            "physics": round(g["cases_pass"] / max(1, g["cases_total"]), 4),
            "objective": None,
            "robustness": det,
        }
        details = {"kind": "scicode", **{k: v for k, v in g.items() if k != "per_step"},
                   "per_step": {k: v for k, v in g["per_step"].items()},
                   "determinism": det}
        gate, gf, fm = 1, [], None
        if exec_ok is False:
            gate, gf, fm = 0, [_EXEC_FAIL], _EXEC_FAIL
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subscores.items()}, weights, gate)
        return build_result(
            task=task, adapter=ADAPTER, validity_gate=gate, gate_failures=gf,
            subscores=subscores, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs,
            failure_mode=fm,
            applicability={"physics": "hidden_tests+numeric", "requirements": "executability",
                           "objective": "N/A(数据集无边界输入测试)", "robustness": "determinism(2 runs)"})

    # ---- unit_tests_problem（humaneval / mbpp 型） ----
    if kind == "unit_tests_problem":
        script = iso.write("candidate.py", _assemble_unit_tests(task, code))
        r1 = iso.run(script, timeout)
        logs.append(f"run1 exit={r1['exit']} {r1['duration_s']}s")
        results_rows = None
        if r1["exit"] == 0:
            for ln in r1["stdout"].splitlines():
                if ln.startswith("@@RESULTS@@"):
                    results_rows = json.loads(ln[len("@@RESULTS@@"):])
        if results_rows is None:
            # 模型代码不可导入/顶层崩溃（或超时）=> gate=0
            return build_result(
                task=task, adapter=ADAPTER, validity_gate=0,
                gate_failures=[_EXEC_FAIL if not r1["timeout"] else "timeout"],
                subscores={"physics": 0.0, "requirements": 0.0, "objective": None,
                           "robustness": 0.0}, score=0.0,
                artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                           "model_meta": json.dumps(meta, ensure_ascii=False),
                           "stderr_tail": json.dumps(r1["stderr"][-1500:], ensure_ascii=False)},
                timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                         "grade_s": time.time() - grade_t0},
                env_digest=env_digest,
                logs=logs + [f"stderr: {r1['stderr'][-300:]}"],
                failure_mode=_EXEC_FAIL if not r1["timeout"] else "timeout",
                applicability={"requirements": "executability",
                               "physics": "hidden_unit_tests",
                               "objective": "N/A(数据集无边界输入测试)",
                               "robustness": "determinism(2 runs)"})
        g = _grade_scicode_results(results_rows)   # 逐 case 统计与 scicode 同构
        # ---- 确定性：第二次执行 ----
        iso2 = IsolatedRun()
        s2 = iso2.write("candidate.py", _assemble_unit_tests(task, code))
        r2 = iso2.run(s2, timeout)
        rows2 = None
        if r2["exit"] == 0:
            for ln in r2["stdout"].splitlines():
                if ln.startswith("@@RESULTS@@"):
                    rows2 = json.loads(ln[len("@@RESULTS@@"):])
        det = None
        if rows2 is not None:
            pat1 = [(x.get("case"), bool(x.get("pass"))) for x in results_rows]
            pat2 = [(x.get("case"), bool(x.get("pass"))) for x in rows2]
            det = 1.0 if pat1 == pat2 else 0.0
        physics = round(g["cases_pass"] / max(1, g["cases_total"]), 4)
        subscores = {
            "requirements": 1.0,            # 判分 harness 完整跑通 = 可导入可调用
            "physics": physics,
            "objective": None,
            "robustness": det,
        }
        details = {"kind": "unit_tests",
                   "cases_pass": g["cases_pass"], "cases_total": g["cases_total"],
                   "failed_cases": [r for r in results_rows if not r.get("pass")][:8],
                   "determinism": det, "run1_s": r1["duration_s"]}
        gate, gf, fm = 1, [], None
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subscores.items()}, weights, gate)
        return build_result(
            task=task, adapter=ADAPTER, validity_gate=gate, gate_failures=gf,
            subscores=subscores, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs, failure_mode=fm,
            applicability={"physics": "hidden_unit_tests",
                           "requirements": "executability",
                           "objective": "N/A(数据集无边界输入测试)",
                           "robustness": "determinism(2 runs)"})

    # ---- cfdcode_problem ----
    if kind == "cfdcode_problem":
        script = iso.write("candidate.py", _assemble_cfdcode(code))
        r1 = iso.run(script, timeout)
        logs.append(f"run1 exit={r1['exit']} {r1['duration_s']}s")
        save_values = list(task["grader"]["save_values"])
        gold_dir = assets_root / task["grader"]["gold_dir"]
        preds = {}
        missing = [v for v in save_values
                   if not (iso.dir / f"{v}.npy").exists()]
        nonfinite = []
        field_metrics: dict[str, dict] = {}
        if r1["exit"] == 0 and not missing:
            for v in save_values:
                arr = np.load(iso.dir / f"{v}.npy")
                preds[v] = arr
                if not np.isfinite(arr).all():
                    nonfinite.append(v)
        gate, gf, fm = 1, [], None
        if r1["timeout"]:
            gate, gf, fm = 0, ["timeout"], "timeout"
        elif r1["exit"] != 0:
            gate, gf, fm = 0, [_EXEC_FAIL], _EXEC_FAIL
        elif missing:
            gate, gf, fm = 0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT
        elif nonfinite:
            gate, gf, fm = 0, [_NOT_PHYSICAL], _NOT_PHYSICAL
        # 数值比对（即使 gate 失败也尝试给出可算的指标，便于诊断）
        if preds and not missing:
            for v in save_values:
                if v in preds and np.isfinite(preds[v]).all():
                    try:
                        gold = np.load(gold_dir / f"{v}_{task['grader']['gold_prefix']}.npy")
                        field_metrics[v] = _grade_one_field(gold, preds[v])
                    except Exception as e:  # noqa: BLE001
                        field_metrics[v] = {"error": f"{type(e).__name__}: {e}"[:200]}
        # 确定性：第二次执行
        det = None
        if gate == 1:
            iso2 = IsolatedRun()
            s2 = iso2.write("candidate.py", _assemble_cfdcode(code))
            r2 = iso2.run(s2, timeout)
            if r2["exit"] == 0:
                det = 1.0
                for v in save_values:
                    try:
                        a, b = preds[v], np.load(iso2.dir / f"{v}.npy")
                        if a.shape != b.shape or not np.allclose(a, b, equal_nan=True):
                            det = 0.0
                            break
                    except Exception:  # noqa: BLE001
                        det = 0.0
                        break
        scored_fields = [m for m in field_metrics.values() if "score01" in m]
        physics = (round(sum(m["score01"] for m in scored_fields) / len(scored_fields), 4)
                   if scored_fields else 0.0)
        subscores = {"requirements": 1.0 if gate == 1 else 0.0,
                     "physics": physics if gate == 1 else 0.0,
                     "objective": None, "robustness": det}
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subscores.items()}, weights, gate)
        details = {"kind": "cfdcode", "missing": missing, "nonfinite": nonfinite,
                   "fields": field_metrics, "determinism": det,
                   "run1_exit": r1["exit"], "run1_s": r1["duration_s"]}
        return build_result(
            task=task, adapter=ADAPTER, validity_gate=gate, gate_failures=gf,
            subscores=subscores, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs + [f"missing={missing} nonfinite={nonfinite}"],
            failure_mode=fm,
            applicability={"physics": "field_metrics(cos/R2)", "requirements": "npy 契约",
                           "objective": "N/A(数据集无边界输入测试)", "robustness": "determinism(2 runs)"})

    if kind == "pinnacle_rel_l2":
        # PINN 训练任务（pinnacle.suite）：候选脚本沙箱内训练并写 pred.npy；
        # 冻结 ref_loader 宿主执行（cfdb qoi_script 同款协议）计算 rel L2，
        # 与 YAML 阈值二值比对。训练类 CPU 非逐位确定 => 不做双跑（robustness N/A）。
        import shutil as _shutil
        import subprocess as _sp
        import sys as _sys
        g = task["grader"]
        # 沙箱输入投递（判分环境放置的冻结数据——laplace 评测点等，不经模型之手）
        for rel in (g.get("sandbox_inputs") or []):
            src = assets_root / rel
            if src.exists():
                _shutil.copy(src, iso.dir / Path(rel).name)
        script = iso.write("candidate.py", code)
        r1 = iso.run(script, timeout)
        logs.append(f"train run exit={r1['exit']} {r1['duration_s']}s")
        pred_path = iso.dir / "pred.npy"
        gate, gf, fm = 1, [], None
        shape_ok = False
        if r1["timeout"]:
            gate, gf, fm = 0, ["timeout"], "timeout"
        elif r1["exit"] != 0:
            gate, gf, fm = 0, [_EXEC_FAIL], _EXEC_FAIL
        elif not pred_path.exists():
            gate, gf, fm = 0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT
        else:
            pred = np.load(pred_path)
            shape_ok = tuple(pred.shape) == tuple(g["pred_shape"])
            if not shape_ok:
                gate, gf, fm = 0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT
                logs.append(f"shape mismatch: {pred.shape} vs {g['pred_shape']}")
            elif not np.isfinite(pred).all():
                gate, gf, fm = 0, [_NOT_PHYSICAL], _NOT_PHYSICAL
        # 冻结 loader 宿主执行（判分材料不经模型）
        rel_l2 = None
        if pred_path.exists():
            loader = assets_root / g["ref_loader"]
            try:
                rq = _sp.run([_sys.executable, "-B", str(loader), str(pred_path)],
                             capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
                lines = [ln for ln in rq.stdout.strip().splitlines() if ln.strip()]
                if rq.returncode == 0 and lines:
                    rel_l2 = float(json.loads(lines[-1])["rel_l2"])
                else:
                    logs.append(f"loader exit={rq.returncode} {rq.stderr[-200:]}")
            except Exception as e:  # noqa: BLE001
                logs.append(f"loader error: {e!r}")
        threshold = float(g["rel_l2_threshold"])
        passed = bool(gate == 1 and rel_l2 is not None and rel_l2 <= threshold)
        physics = 1.0 if passed else 0.0
        subscores = {"requirements": 1.0 if gate == 1 else 0.0,
                     "physics": physics if gate == 1 else 0.0,
                     "objective": None, "robustness": None}
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subscores.items()}, weights, gate)
        details = {"kind": "pinnacle", "rel_l2": rel_l2, "threshold": threshold,
                   "passed": passed, "shape_ok": shape_ok,
                   "train_exit": r1["exit"], "train_s": r1["duration_s"],
                   "stdout_tail": r1["stdout"][-400:]}
        return build_result(
            task=task, adapter=ADAPTER, validity_gate=gate, gate_failures=gf,
            subscores=subscores, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs,
            failure_mode=fm,
            applicability={"physics": "rel_l2_threshold(冻结 loader)",
                           "requirements": "pred.npy 契约(形状/有限值)",
                           "objective": "N/A(无边界输入测试)",
                           "robustness": "N/A(训练类 CPU 非逐位确定,不双跑)"})

    raise ValueError(f"未知 exec_kind: {kind}")


# ---------------------------------------------------------------- summary

def write_summary(out_dir: Path, results: list[dict[str, Any]],
                  provider: str, model_label: str, seed: int) -> Path:
    dist = gate_distribution(results)
    lines = []
    a = lines.append
    a(f"# code_exec 结果汇总（provider={provider}, model={model_label}, seed={seed}）")
    a("")
    a("## ValidityGate 分布（先看 gate，再看子分）")
    a("")
    a(f"- 任务总数: {dist['n_tasks']}")
    a(f"- gate 通过: {dist['gate_passed']}")
    a(f"- gate 失败: {dist['gate_failed']}（直接 0 分）")
    a(f"- 作废: {dist['voided']}")
    a(f"- gate 失败原因分布: {dist['gate_failure_reasons'] or '无'}")
    a("")
    # pass@1（unit_tests 类：全部隐藏断言通过的任务占比；scicode/cfdcode 不适用）
    ut = [r for r in results if "grade_details" in r["artifacts"]
          and json.loads(r["artifacts"]["grade_details"]).get("kind") == "unit_tests"]
    if ut:
        full = sum(1 for r in ut if r["subscores"]["physics"] == 1.0)
        a(f"## pass@1（全部隐藏测试通过）")
        a("")
        a(f"- {full}/{len(ut)} = {full / max(1, len(ut)):.4f}"
          "（physics=1.0 的任务占比；physics 均值含部分通过分，二者并读）")
        a("")
    # 子分分布（分桶，不给裸均分掩盖）
    for key, label in (("physics", "physics（隐藏测试/数值）"), 
                       ("robustness", "robustness（确定性）")):
        vals = [r["subscores"][key] for r in results if r["subscores"][key] is not None]
        if not vals:
            continue
        buckets = {"=1.0": 0, "0.5-1.0": 0, "0-0.5": 0, "=0.0": 0}
        for v in vals:
            if v == 1.0: buckets["=1.0"] += 1
            elif v >= 0.5: buckets["0.5-1.0"] += 1
            elif v > 0: buckets["0-0.5"] += 1
            else: buckets["=0.0"] += 1
        a(f"## {label} 分布（n={len(vals)}）")
        a("")
        for k, n in buckets.items():
            a(f"- {k}: {n}")
        a("")
    # 每任务明细
    a("## 每任务明细")
    a("")
    a("| task | gate | physics | robust | score | 关键信息 |")
    a("| --- | --- | --- | --- | --- | --- |")
    for r in results:
        det = r["artifacts"].get("grade_details")
        info = ""
        if det:
            d = json.loads(det)
            if d.get("kind") == "scicode":
                info = f"steps {d['steps_all_pass']}/{d['steps_total']}, cases {d['cases_pass']}/{d['cases_total']}"
            elif d.get("kind") == "unit_tests":
                info = f"cases {d['cases_pass']}/{d['cases_total']}"
            else:
                info = f"fields {sorted(d.get('fields', {}).keys())} missing={d.get('missing')}"
        a(f"| {r['task_id']} | {r['validity_gate']} | {r['subscores']['physics']} "
          f"| {r['subscores']['robustness']} | {r['score']} | {info} |")
    p = out_dir / "summary.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="code_exec adapter runner")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="stub",
                    choices=["stub", "oracle", "openai_compat", "glm", "minimax", "external"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="仅复用身份匹配的完整结果；旧协议、损坏或条件不一致时"
                         "拒绝续写，请使用新 --out 目录")
    args = ap.parse_args()

    tasks_dir = Path(args.tasks)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(tasks_dir)
    rids = {t["registry_id"] for t in tasks}
    if len(rids) > 1:
        raise SystemExit(f"一次运行只允许一个 registry_id: {rids}")
    registry_id = rids.pop()
    assets_root = tasks_dir.resolve().parent.parent   # 绝对化：沙箱 cwd 变化后相对路径失效

    asset_hashes, asset_paths = {}, []
    for t in tasks:
        for a in t.get("input", {}).get("assets", []) or []:
            p = Path(a["path"])
            if not p.is_absolute():
                p = (assets_root / p).resolve()
            common.verify_asset(p, a["digest"], f"{t.id}:{a['path']}")
            asset_hashes[a["path"]] = a["digest"]
            asset_paths.append(p)
    env_digest = environment_digest(extra_paths=asset_paths)

    prompt_cache = {}
    for t in tasks:
        pf = Path(t["input"]["prompt_file"])
        if not pf.is_absolute():
            pf = (assets_root / pf).resolve()
        with open(pf, encoding="utf-8", newline="") as f:
            prompt_cache[t.id] = f.read()

    # oracle 代码源（判分器自检用）：scicode=dev gold；cfdcode=solution 源码
    oracle_cache: dict[str, str] = {}
    if args.provider == "oracle":
        for t in tasks:
            src = t["grader"].get("oracle_source")
            if not src:
                raise SystemExit(f"{t.id}: oracle 无 gold 源可用（scicode test split 无 gold）")
            p = Path(src)
            if not p.is_absolute():
                p = (assets_root / src).resolve()
            oracle_cache[t.id] = p.read_text(encoding="utf-8")

    from .run_state import RunState, provider_identity, rerun_command
    model_label = provider_identity(args.provider, args.model)["model"]
    rerun = rerun_command("runners.code_exec", args, model_label)

    with RunState(out_dir=out_dir, tasks=tasks, prompts=prompt_cache,
                  adapter=ADAPTER, provider=args.provider, model=args.model,
                  seed=args.seed, env_digest=env_digest, assets=asset_hashes,
                  tasks_dir=tasks_dir, rerun=rerun, resume=args.resume,
                  extra={'model': model_label}) as run:
        results, crash, resumed = [], 0, 0
        for t in tasks:
            if t.id in run.cached:
                results.append(run.cached[t.id])
                resumed += 1
                continue
            try:
                r = run_task(t, provider=args.provider, model=args.model, seed=args.seed,
                             env_digest=env_digest, prompt_cache=prompt_cache,
                             assets_root=assets_root, oracle_cache=oracle_cache or None)
            except ProviderError as e:
                raise SystemExit(f"[终止] provider 失败: {e}")
            except Exception as e:  # noqa: BLE001
                crash += 1
                r = build_result(
                    task=t, adapter=ADAPTER, validity_gate=0, gate_failures=[common.FM_CRASH],
                    subscores={"physics": None, "requirements": None, "objective": None,
                               "robustness": None}, score=0.0, artifacts={},
                    timings={"agent_s": 0.0, "setup_s": 0.0, "grade_s": 0.0},
                    env_digest=env_digest, logs=[f"runner exception: {e!r}"],
                    failure_mode=common.FM_CRASH)
            results.append(r)
            run.write_result(t, r)

        mf = run.finish(crash_tasks=crash, resumed_tasks=resumed)
        sm = write_summary(out_dir, results, args.provider, model_label, args.seed)
        dist = gate_distribution(results)
        print(f"[done] {dist['n_tasks']} tasks | gate pass {dist['gate_passed']} "
              f"| fail {dist['gate_failed']} | voided {dist['voided']} | crash {crash}")
        print(f"       summary -> {sm}")
        print(f"       rerun: {rerun}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
