"""simulation_agent.py — 仿真工程 Agent adapter（五类标准 adapter 之三，YAML 驱动）。

适用（adapters/README.md §3）：cfdllm.foam_basic（dev）；aviary/nasa_tmr/crm 等后续。
求解器无关（硬性）：判分只认 case 产物 + 求解日志判据 + 场结果；求解器调用经
runners/solvers/ 层（openfoam.py 可换 fluent.py），任务 YAML 声明 backend。

foam_basic 判分管线：
  gate（顺序短路）：
    1. 脚本可执行（沙箱内跑通，写出算例文件）——code_not_executable
    2. 算例结构合法（system 四件套 + constant/ + 0/ + Allrun）——missing_output
    3. 求解跑完（docker Allrun 不超时；官方判据 log.*Foam 倒数第二行 == "End"）
       ——timeout / simulation_failed
  physics   = NMSE vs GT 末时刻场（官方阈值 <0.1→1.0 / <0.3→0.5 / else 0）
  requirements = 结构契约文件存在率
  objective / robustness = N/A（基础题无目标函数/扰动重算；权重 0，YAML 声明）

模型输出契约：单个 ```python 脚本，在 cwd 写出完整 OpenFOAM 算例（含 Allrun）。

运行（须用 .venv，判分侧依赖 pyvista）：
  cd benchmarks && .venv/bin/python -m runners.simulation_agent \
      --tasks tasks/cfdllm.foam_basic --out results/cfdllm.foam_basic/<date>/<provider> \
      --provider minimax --model MiniMax-M3 --seed 0
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from . import common
from .common import (FM_MISSING_OUTPUT, TaskSpec, aggregate_score,
                     build_result, environment_digest, gate_distribution,
                     load_tasks, write_run_manifest)
from .providers import ProviderError, get_answer
from .sandbox import IsolatedRun, static_check
from .solvers.openfoam import get_solver

ADAPTER = "simulation_agent"
DEFAULT_WEIGHTS = {"physics": 0.35, "requirements": 0.30,
                   "objective": 0.20, "robustness": 0.15}

REQUIRED_PATHS = ["system/controlDict", "system/fvSchemes", "system/fvSolution",
                  "system/blockMeshDict", "constant", "0", "Allrun"]

_SIM_FAIL = "simulation_failed"
_SCRIPT_FAIL = "code_not_executable"


# ---------------------------------------------------------------- aviary 分支

def _run_aviary_task(
    task: TaskSpec, code: str, meta: dict, t0: float, env_digest: str,
    logs: list[str], applicability: dict[str, str],
    companions: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """aviary_mission / pycycle_cycle：模型脚本在沙箱内求解 result.json，对参考判分。

    companions：伴随模块（文件名, 源码）——仅 oracle gold 需要（vendored 引擎
    turbojet_engine.py 与 gold 同目录依赖）；被测模型按题面自建循环，不提供。
    """
    grade_t0 = time.time()
    timeout = float(task["limits"]["wall_clock_s"])
    iso = IsolatedRun()
    script = iso.write("solve.py", code)
    for name, content in (companions or []):
        iso.write(name, content)
        logs.append(f"companion written: {name} ({len(content)}B)")
    rr = iso.run(script, timeout)
    logs.append(f"solve exit={rr['exit']} {rr['duration_s']}s")

    def _ret(gate: int, gf: list[str], fm: str | None, subs: dict, details: dict):
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subs.items()}, weights, gate)
        return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
            gate_failures=gf, subscores=subs, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs, failure_mode=fm,
            applicability=applicability)

    if rr["timeout"] or rr["exit"] != 0:
        return _ret(0, ["timeout" if rr["timeout"] else _SCRIPT_FAIL],
                    "timeout" if rr["timeout"] else _SCRIPT_FAIL,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None},
                    {"stderr_tail": rr["stderr"][-800:]})

    rj = iso.dir / "result.json"
    if not rj.exists():
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None}, {"missing": "result.json"})
    try:
        got = json.loads(rj.read_text())
        if not isinstance(got, dict):
            raise ValueError("result.json 顶层必须是对象")
    except Exception as e:  # noqa: BLE001
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None},
                    {"parse_error": str(e)[:200]})

    g = task["grader"]
    keys = list(g["result_keys"])
    exact_keys = set(g.get("exact_keys", []))
    ref = dict(task["reference"]["values"])
    tol = float(g.get("numeric_rel_tol", 0.01))
    present = [k for k in keys if k in got]
    req_ratio = round(len(present) / len(keys), 4)
    if len(present) < len(keys):
        logs.append(f"missing keys: {sorted(set(keys) - set(got))}")

    hits: dict[str, Any] = {}
    for k in keys:
        if k not in got:
            hits[k] = {"status": "missing"}
            continue
        if k in exact_keys or not isinstance(got[k], (int, float)) or not isinstance(ref.get(k), (int, float)):
            ok = (str(got[k]) == str(ref.get(k)))
            hits[k] = {"status": "exact", "ok": bool(ok),
                       "got": got[k], "ref": ref.get(k)}
        else:
            rv = float(ref[k])
            gv = float(got[k])
            rel = abs(gv - rv) / max(abs(rv), 1e-12)
            ok = rel <= tol
            hits[k] = {"status": "tol", "ok": bool(ok), "rel_err": round(rel, 6),
                       "got": gv, "ref": rv}
    n_ok = sum(1 for v in hits.values() if v.get("ok"))
    physics = round(n_ok / max(1, len(keys)), 4)
    subs = {"physics": physics, "requirements": req_ratio,
            "objective": None, "robustness": None}
    details = {"kind": "aviary_mission", "hits": hits,
               "physics_hits": f"{n_ok}/{len(keys)}", "rel_tol": tol}
    return _ret(1, [], None, subs, details)


# ---------------------------------------------------------------- gtm_matlab 分支

def _run_matlab_task(
    task: TaskSpec, code: str, meta: dict, t0: float, env_digest: str,
    logs: list[str], applicability: dict[str, str], timeout: float,
) -> dict[str, Any]:
    """gtm_matlab：模型 MATLAB 脚本在隔离目录 matlab -batch 执行，写 result.json 判分。

    判分口径与 _run_aviary_task 完全同构（result_keys/numeric_rel_tol/exact_keys，
    数值对锁定参考的相对误差）——本函数为镜像实现，不改 _run_aviary_task
    （pycycle/aviary 回归已锁定，动它需整链重验）。
    """
    from .solvers.matlab import run_matlab
    grade_t0 = time.time()
    iso = IsolatedRun()
    iso.write("model.m", code)
    rr = run_matlab(iso.dir, "model", timeout)
    logs.append(f"matlab exit={rr['exit']} {rr['duration_s']}s"
                + (" TIMEOUT" if rr["timeout"] else ""))

    def _ret(gate: int, gf: list[str], fm: str | None, subs: dict, details: dict):
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subs.items()}, weights, gate)
        return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
            gate_failures=gf, subscores=subs, score=score,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs, failure_mode=fm,
            applicability=applicability)

    if rr["timeout"] or rr["exit"] != 0:
        return _ret(0, ["timeout" if rr["timeout"] else _SCRIPT_FAIL],
                    "timeout" if rr["timeout"] else _SCRIPT_FAIL,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None},
                    {"stdout_tail": rr["stdout_tail"][-800:]})

    rj = iso.dir / "result.json"
    if not rj.exists():
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None}, {"missing": "result.json"})
    try:
        got = json.loads(rj.read_text())
        if not isinstance(got, dict):
            raise ValueError("result.json 顶层必须是对象")
    except Exception as e:  # noqa: BLE001
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None}, {"parse_error": str(e)[:200]})

    g = task["grader"]
    keys = list(g["result_keys"])
    exact_keys = set(g.get("exact_keys", []))
    ref = dict(task["reference"]["values"])
    tol = float(g.get("numeric_rel_tol", 0.01))
    present = [k for k in keys if k in got]
    req_ratio = round(len(present) / len(keys), 4)
    if len(present) < len(keys):
        logs.append(f"missing keys: {sorted(set(keys) - set(got))}")

    hits: dict[str, Any] = {}
    for k in keys:
        if k not in got:
            hits[k] = {"status": "missing"}
            continue
        if k in exact_keys or not isinstance(got[k], (int, float)) or not isinstance(ref.get(k), (int, float)):
            ok = (str(got[k]) == str(ref.get(k)))
            hits[k] = {"status": "exact", "ok": bool(ok),
                       "got": got[k], "ref": ref.get(k)}
        else:
            rv = float(ref[k])
            gv = float(got[k])
            rel = abs(gv - rv) / max(abs(rv), 1e-12)
            ok = rel <= tol
            hits[k] = {"status": "tol", "ok": bool(ok), "rel_err": round(rel, 6),
                       "got": gv, "ref": rv}
    n_ok = sum(1 for v in hits.values() if v.get("ok"))
    physics = round(n_ok / max(1, len(keys)), 4)
    subs = {"physics": physics, "requirements": req_ratio,
            "objective": None, "robustness": None}
    details = {"kind": "gtm_matlab", "hits": hits,
               "physics_hits": f"{n_ok}/{len(keys)}", "rel_tol": tol,
               "matlab_s": rr["duration_s"]}
    return _ret(1, [], None, subs, details)


def run_task(
    task: TaskSpec, *, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str], assets_root: Path,
    oracle_cache: dict[str, str] | None,
    companions: list[tuple[str, str]] | None = None,
    prompt_override: str | None = None,
) -> dict[str, Any]:
    from .foam_nmse import evaluate_nmse, nmse_to_score
    t0 = time.time()
    prompt = prompt_override if prompt_override is not None else prompt_cache[task.id]
    g = task["grader"]
    timeout = float(task["limits"]["wall_clock_s"])
    kind = g.get("exec_kind", "foam_basic")

    # ---- 模型脚本 ----
    if provider == "oracle":
        code = oracle_cache[task.id]
        meta = {"provider": "oracle", "note": "GT files verbatim writer"}
    else:
        out = get_answer(provider, task, prompt, seed=seed, model=model,
                         max_attempts=int(task["limits"]["attempts"]),
                         expect="matlab" if kind == "gtm_matlab" else "code")
        code, meta = out["answer"], out["meta"]

    if provider == "oracle":
        violations, syntax_ok = [], True
    elif kind == "gtm_matlab":
        # MATLAB 方言：正则级逃逸检查（无 AST）；语法错误由 -batch 非零退出拦截
        from .solvers.matlab import matlab_static_check
        violations = matlab_static_check(code)
        syntax_ok = True
    else:
        violations, syntax_ok = static_check(code)
    logs = [f"violations={violations}", f"syntax_ok={syntax_ok}"]
    if kind in ("aviary_mission", "pycycle_cycle", "gtm_matlab"):
        applicability = {"physics": "numeric_vs_reference", "requirements": "result.json 键完备",
                         "objective": "N/A(静态任务)", "robustness": "N/A(无扰动重算)"}
    else:
        applicability = {"physics": "field_nmse_vs_gt", "requirements": "case_structure",
                         "objective": "N/A(基础题无目标函数)", "robustness": "N/A(无扰动重算)"}

    if violations:
        return build_result(task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=["sandbox_escape_attempt"],
            subscores={"physics": 0.0, "requirements": 0.0, "objective": None,
                       "robustness": None}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0, "grade_s": 0.0},
            env_digest=env_digest, logs=logs, failure_mode="sandbox_escape_attempt",
            applicability=applicability)
    if not syntax_ok:
        return build_result(task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=[_SCRIPT_FAIL],
            subscores={"physics": 0.0, "requirements": 0.0, "objective": None,
                       "robustness": None}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0, "grade_s": 0.0},
            env_digest=env_digest, logs=logs, failure_mode=_SCRIPT_FAIL,
            applicability=applicability)

    # ---- exec_kind 分派 ----
    if kind in ("aviary_mission", "pycycle_cycle"):
        return _run_aviary_task(task, code, meta, t0, env_digest, logs,
                                applicability, companions=companions)
    if kind == "gtm_matlab":
        return _run_matlab_task(task, code, meta, t0, env_digest, logs,
                                applicability, timeout)

    # ---- 1) 沙箱跑脚本 → 算例目录 ----
    grade_t0 = time.time()
    iso = IsolatedRun()
    script = iso.write("make_case.py", code)
    r1 = iso.run(script, min(timeout, 300.0))
    logs.append(f"make_case exit={r1['exit']} {r1['duration_s']}s")
    case_dir = iso.dir
    if r1["timeout"] or r1["exit"] != 0:
        return build_result(task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=["timeout" if r1["timeout"] else _SCRIPT_FAIL],
            subscores={"physics": 0.0, "requirements": 0.0, "objective": None,
                       "robustness": None}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "stderr_tail": json.dumps(r1["stderr"][-1200:], ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest,
            logs=logs + [f"stderr: {r1['stderr'][-300:]}"],
            failure_mode="timeout" if r1["timeout"] else _SCRIPT_FAIL,
            applicability=applicability)

    # ---- 2) 结构契约 ----
    present = [p for p in REQUIRED_PATHS if (case_dir / p).exists()]
    missing = [p for p in REQUIRED_PATHS if p not in present]
    req_ratio = round(len(present) / len(REQUIRED_PATHS), 4)
    logs.append(f"structure present={len(present)}/{len(REQUIRED_PATHS)} missing={missing}")
    if missing:
        return build_result(task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=[FM_MISSING_OUTPUT],
            subscores={"physics": 0.0, "requirements": req_ratio, "objective": None,
                       "robustness": None}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "grade_details": json.dumps({"missing": missing}, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs, failure_mode=FM_MISSING_OUTPUT,
            applicability=applicability)

    # ---- 3) 求解（经 solvers 层，可替换后端）----
    (case_dir / "Allrun").chmod(0o755)
    solver = get_solver(g.get("solver_backend", "openfoam10-docker"))
    rr = solver.run_case(case_dir, timeout)
    logs.append(f"solver {solver.name} ok={rr['ok']} exit={rr['exit']} "
                f"{rr['duration_s']}s last_time={rr['last_time']}")
    exec_ok = solver.execution_ok(case_dir)
    if rr["timeout"] or not exec_ok:
        return build_result(task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=["timeout" if rr["timeout"] else _SIM_FAIL],
            subscores={"physics": 0.0, "requirements": req_ratio, "objective": None,
                       "robustness": None}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "grade_details": json.dumps(
                           {"solver": solver.name, "exit": rr["exit"],
                            "last_time": rr["last_time"], "exec_ok": exec_ok,
                            "stderr_tail": rr["stderr"][-800:]}, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs,
            failure_mode="timeout" if rr["timeout"] else _SIM_FAIL,
            applicability=applicability)

    # ---- 4) NMSE 判分（venv pyvista，官方语义）----
    gt_run = assets_root / task["reference"]["gt_run_dir"]
    nmse_agg, per_field = evaluate_nmse(gt_run, case_dir)
    physics = nmse_to_score(nmse_agg)
    details = {"solver": solver.name, "exit": rr["exit"], "last_time": rr["last_time"],
               "exec_ok": True, "nmse": round(nmse_agg, 6),
               "nmse_per_field": per_field, "nmse_score": physics}
    subscores = {"physics": physics, "requirements": 1.0, "objective": None,
                 "robustness": None}
    weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
    score = aggregate_score({k: (v if v is not None else 0.0)
                             for k, v in subscores.items()}, weights, 1)
    logs.append(f"nmse={nmse_agg:.4g} score={physics}")
    return build_result(task=task, adapter=ADAPTER, validity_gate=1,
        gate_failures=[], subscores=subscores, score=score,
        artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                   "model_meta": json.dumps(meta, ensure_ascii=False),
                   "grade_details": json.dumps(details, ensure_ascii=False)},
        timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                 "grade_s": time.time() - grade_t0},
        env_digest=env_digest, logs=logs, failure_mode=None,
        applicability=applicability)


# ---------------------------------------------------------------- 迭代协议（v0.2）

# 可反馈修复的失败模式（喂回 stderr/诊断后模型有机会修好）；
# 越界/超时/环境类失败不进入迭代——前者是策略违规，后者重试无意义且烧配额。
_FIXABLE_MODES = {_SCRIPT_FAIL, FM_MISSING_OUTPUT, _SIM_FAIL}


def build_feedback_prompt(base_prompt: str, prev_result: dict[str, Any],
                          round_no: int) -> str:
    """构造第 N 轮反馈提示：原题面 + 上一轮代码 + 执行诊断。

    诊断来源（按分支）：artifacts.stderr_tail（foam）/ grade_details.stderr_tail
    （aviary/pycycle/gtm）/ grade_details.parse_error / missing / gate_failures。
    """
    kind = (prev_result.get("artifacts", {}).get("grade_details")
            and "gtm" in str(json.loads(prev_result["artifacts"].get("grade_details") or "{}").get("kind", "")))
    fence = "matlab" if kind else "python"
    try:
        code = json.loads(prev_result["artifacts"].get("code") or '""')
    except Exception:  # noqa: BLE001
        code = ""
    code = str(code)[:6000]
    det = json.loads(prev_result["artifacts"].get("grade_details") or "{}")
    stderr = (prev_result["artifacts"].get("stderr_tail")
              or det.get("stdout_tail") or det.get("stderr_tail") or "")
    try:
        stderr = json.loads(stderr) if isinstance(stderr, str) and stderr.startswith('"') else stderr
    except Exception:  # noqa: BLE001
        pass
    stderr = str(stderr)[-1200:]

    diag = [f"- failure_mode: {prev_result.get('failure_mode')}",
            f"- gate_failures: {prev_result.get('gate_failures')}"]
    if stderr:
        diag.append(f"- execution output tail:\n```\n{stderr}\n```")
    if det.get("parse_error"):
        diag.append(f"- result.json parse error: {det['parse_error']}")
    if det.get("missing"):
        diag.append(f"- missing artifact: {det['missing']}")
    for k in ("last_time", "exit", "solver"):
        if det.get(k) is not None:
            diag.append(f"- {k}: {det[k]}")

    return (f"{base_prompt}\n\n---\n\n## ITERATION FEEDBACK — attempt {round_no} FAILED\n\n"
            f"Your previous script:\n```{fence}\n{code}\n```\n\n"
            f"Execution diagnostics:\n" + "\n".join(diag) +
            f"\n\nFix the failure. Respond with a single complete "
            f"```{fence} code block (the full revised script, not a diff).")


def run_task_iterate(
    task: TaskSpec, *, iterate: int, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str], assets_root: Path,
    oracle_cache: dict[str, str] | None = None,
    companions: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """迭代协议包装：执行失败且可修复时，把诊断喂回模型修订，至多 iterate 轮。

    - 单轮行为与直调 run_task 逐字节等价（iterate=1 时 wrapper 不介入）；
    - rounds_to_success 不进 subscores（评分语义不变），落 artifacts.iteration
      {rounds_used, iterate_max, converged}——harness 增益 = 迭代均分 − 单轮均分，
      轮数分布单独报告（scoring 口径：分数导航、增益与轮次是证据）。
    - oracle 第 1 轮即过 gate（不耗反馈轮）；stub 恒定失败会跑满 N 轮（确定性，
      每轮仅本地执行，无 API 消耗）。
    """
    r = run_task(task, provider=provider, model=model, seed=seed,
                 env_digest=env_digest, prompt_cache=prompt_cache,
                 assets_root=assets_root, oracle_cache=oracle_cache,
                 companions=companions)
    rounds_used = 1
    while (r["validity_gate"] == 0 and rounds_used < iterate
           and (r.get("failure_mode") in _FIXABLE_MODES)):
        fb = build_feedback_prompt(prompt_cache[task.id], r, rounds_used)
        r = run_task(task, provider=provider, model=model, seed=seed,
                     env_digest=env_digest, prompt_cache=prompt_cache,
                     assets_root=assets_root, oracle_cache=oracle_cache,
                     companions=companions, prompt_override=fb)
        rounds_used += 1
    r["artifacts"]["iteration"] = json.dumps(
        {"rounds_used": rounds_used, "iterate_max": iterate,
         "converged": r["validity_gate"] == 1}, ensure_ascii=False)
    if "applicability" in r:
        r["applicability"]["iteration"] = f"rounds {rounds_used}/{iterate}"
    return r


# ---------------------------------------------------------------- summary

def write_summary(out_dir: Path, results: list[dict[str, Any]],
                  provider: str, model_label: str, seed: int) -> Path:
    dist = gate_distribution(results)
    lines = []
    a = lines.append
    a(f"# simulation_agent 结果汇总（provider={provider}, model={model_label}, seed={seed}）")
    a("")
    a("## ValidityGate 分布（先看 gate，再看子分）")
    a("")
    a(f"- 任务总数: {dist['n_tasks']}")
    a(f"- gate 通过: {dist['gate_passed']}")
    a(f"- gate 失败: {dist['gate_failed']}（直接 0 分）")
    a(f"- 作废: {dist['voided']}")
    a(f"- gate 失败原因分布: {dist['gate_failure_reasons'] or '无'}")
    a("")
    # 迭代协议轮次分布（v0.2：artifacts.iteration 存在时才报）
    iters = []
    for r in results:
        try:
            iters.append(json.loads(r["artifacts"].get("iteration") or "null"))
        except Exception:  # noqa: BLE001
            iters.append(None)
    if any(iters):
        from collections import Counter as _C
        by_round = _C((it or {}).get("rounds_used") for it in iters if it)
        converged = sum(1 for it in iters if it and it.get("converged"))
        succ_rounds = [(it or {}).get("rounds_used") for it in iters
                       if it and it.get("converged")]
        a("## 迭代协议（rounds_to_success，不进 score）")
        a("")
        a(f"- 收敛任务: {converged}/{len(iters)}；轮次分布: {dict(sorted(by_round.items(), key=lambda x: (x[0] is None, x[0])))}")
        if succ_rounds:
            a(f"- 收敛任务平均轮数: {sum(succ_rounds)/len(succ_rounds):.2f}"
              f"（rounds_to_success；单轮协议下该值恒为 1）")
        a("")
    ph = [r["subscores"]["physics"] for r in results if r["subscores"]["physics"] is not None]
    if ph:
        a(f"## physics（NMSE 阈值分）分布（n={len(ph)}）")
        a("")
        for lbl, cnt in (("1.0", sum(1 for v in ph if v == 1.0)),
                         ("0.5", sum(1 for v in ph if v == 0.5)),
                         ("0.0", sum(1 for v in ph if v == 0.0))):
            a(f"- {lbl}: {cnt}")
        a("")
    a("## 每任务明细")
    a("")
    a("| task | gate | nmse | nmse_score | score | 关键信息 |")
    a("| --- | --- | --- | --- | --- | --- |")
    for r in results:
        det = r["artifacts"].get("grade_details")
        info = ""
        nmse_s = "-"
        if det:
            d = json.loads(det)
            nmse_s = d.get("nmse", "-")
            if d.get("exec_ok"):
                info = f"last={d.get('last_time')} fields={list(d.get('nmse_per_field', {}).keys())}"
            else:
                info = f"missing={json.loads(r['artifacts'].get('grade_details','{}')).get('missing') or 'exec_fail'}"
        ph_s = r["subscores"]["physics"]
        a(f"| {r['task_id']} | {r['validity_gate']} | {nmse_s} "
          f"| {ph_s if ph_s is not None else '-'} | {r['score']} | {info} |")
    p = out_dir / "summary.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="simulation_agent adapter runner")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="stub",
                    choices=["stub", "oracle", "openai_compat", "glm", "minimax"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="跳过 out 下已有 result_<task_id>.json 的任务（读入参与"
                         "汇总，损坏文件自动重跑）；summary/manifest 按全量重建")
    ap.add_argument("--iterate", type=int, default=1,
                    help="迭代协议轮数上限（v0.2）：失败且可修复时把执行诊断喂回"
                         "模型修订重跑；1=单轮（默认，与既有锁定行为逐字节一致）。"
                         "rounds_to_success 落 artifacts.iteration 不进 score")
    ap.add_argument("--limit", type=int, default=0,
                    help="只跑前 K 个任务（试点子集用；0=全量）")
    ap.add_argument("--scaffold", default=None,
                    help="H2/H3 harness 臂：蒸馏工作流文档路径，注入每题 prompt 前"
                         "部（反馈轮自动携带）。与 --iterate 组合构成 harness 臂矩阵："
                         "H0=无；H1=--iterate 3；H2=--scaffold；H3=--iterate 3 --scaffold")
    args = ap.parse_args()

    tasks_dir = Path(args.tasks)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(tasks_dir)
    if args.limit > 0:
        tasks = tasks[:args.limit]
    rids = {t["registry_id"] for t in tasks}
    if len(rids) > 1:
        raise SystemExit(f"一次运行只允许一个 registry_id: {rids}")
    registry_id = rids.pop()
    assets_root = tasks_dir.resolve().parent.parent

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

    # H2/H3 harness 臂：蒸馏工作流文档注入 prompt 前部（反馈轮以 prompt_cache
    # 为基底自动携带）。文档是受测 harness 的核心资产，其 sha256 落 manifest。
    scaffold_text = ""
    if args.scaffold:
        sp = Path(args.scaffold)
        if not sp.is_absolute():
            sp = (common.BENCH_ROOT / sp).resolve()
        scaffold_text = sp.read_text(encoding="utf-8").strip() + \
            "\n\n---\n\n# TASK\n\n"
        for tid in prompt_cache:
            prompt_cache[tid] = scaffold_text + prompt_cache[tid]

    oracle_cache: dict[str, str] = {}
    companions: list[tuple[str, str]] = []
    if args.provider == "oracle":
        for t in tasks:
            src = t["grader"].get("oracle_source")
            if not src:
                raise SystemExit(f"{t.id}: 无 oracle_source")
            p = Path(src)
            if not p.is_absolute():
                p = (assets_root / src).resolve()
            oracle_cache[t.id] = p.read_text(encoding="utf-8")
            # gold 的同目录/父目录伴随模块（如 vendored turbojet_engine.py，位于
            # gold/ 上层）：gold 里 import 了才随行——被测模型按题面自建，不提供
            seen: set[Path] = set()
            for cand in sorted(list(p.parent.glob("*.py")) + list(p.parent.parent.glob("*.py"))):
                if cand in seen or cand == p or cand.stem == "__init__":
                    continue
                seen.add(cand)
                if f"import {cand.stem}" in oracle_cache[t.id] and \
                        (cand.stem, cand.read_text(encoding="utf-8")) not in companions:
                    companions.append((cand.stem + ".py",
                                       cand.read_text(encoding="utf-8")))

    from .providers import PROVIDER_PRESETS
    model_label = args.model or PROVIDER_PRESETS.get(args.provider, {}).get("model_default", "n/a")

    rerun = (f"cd {common.BENCH_ROOT} && .venv/bin/python -m runners.simulation_agent "
             f"--tasks {tasks_dir.as_posix()} --out {out_dir.as_posix()} "
             f"--provider {args.provider}"
             + (f" --model {args.model}" if args.model else "")
             + f" --seed {args.seed}"
             + (f" --iterate {args.iterate}" if args.iterate > 1 else "")
             + (f" --limit {args.limit}" if args.limit else "")
             + (f" --scaffold {args.scaffold}" if args.scaffold else "")
             + (" --resume" if args.resume else ""))

    results, crash, resumed = [], 0, 0
    for t in tasks:
        rp = out_dir / f"result_{t.id}.json"
        if args.resume and rp.exists():
            try:
                results.append(json.loads(rp.read_text(encoding="utf-8")))
                resumed += 1
                continue
            except Exception:  # noqa: BLE001 — 损坏的半截文件按缺失处理重跑
                pass
        try:
            if args.iterate > 1:
                r = run_task_iterate(t, iterate=args.iterate,
                                     provider=args.provider, model=args.model,
                                     seed=args.seed, env_digest=env_digest,
                                     prompt_cache=prompt_cache,
                                     assets_root=assets_root,
                                     oracle_cache=oracle_cache or None,
                                     companions=companions or None)
            else:
                r = run_task(t, provider=args.provider, model=args.model, seed=args.seed,
                             env_digest=env_digest, prompt_cache=prompt_cache,
                             assets_root=assets_root, oracle_cache=oracle_cache or None,
                             companions=companions or None)
        except ProviderError as e:
            raise SystemExit(f"[终止] provider 失败: {e}")
        except Exception as e:  # noqa: BLE001
            crash += 1
            r = build_result(task=t, adapter=ADAPTER, validity_gate=0,
                gate_failures=[common.FM_CRASH],
                subscores={"physics": None, "requirements": None, "objective": None,
                           "robustness": None}, score=0.0, artifacts={},
                timings={"agent_s": 0.0, "setup_s": 0.0, "grade_s": 0.0},
                env_digest=env_digest, logs=[f"runner exception: {e!r}"],
                failure_mode=common.FM_CRASH)
        results.append(r)
        (out_dir / f"result_{t.id}.json").write_text(
            json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    mf = write_run_manifest(out_dir, registry_id=registry_id, adapter=ADAPTER,
                            provider=args.provider, seed=args.seed, tasks_dir=tasks_dir,
                            env_digest=env_digest, assets=asset_hashes,
                            rerun_command=rerun,
                            extra={"crash_tasks": crash, "model": model_label,
                                   "resumed_tasks": resumed,
                                   "protocol": "iterate" if args.iterate > 1 else "single",
                                   "iterate_rounds": args.iterate,
                                   "limit": args.limit,
                                   "harness_arm": ("H3" if (args.scaffold and args.iterate > 1)
                                                   else "H2" if args.scaffold
                                                   else "H1" if args.iterate > 1 else "H0"),
                                   "scaffold": (args.scaffold or None)})
    sm = write_summary(out_dir, results, args.provider, model_label, args.seed)
    dist = gate_distribution(results)
    print(f"[done] {dist['n_tasks']} tasks | gate pass {dist['gate_passed']} "
          f"| fail {dist['gate_failed']} | voided {dist['voided']} | crash {crash}")
    print(f"       summary -> {sm}")
    print(f"       rerun: {rerun}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
