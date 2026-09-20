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
import sys
import time
from pathlib import Path
from typing import Any

from . import common
from .common import (FM_MISSING_OUTPUT, TaskSpec, aggregate_score,
                     build_result, environment_digest, gate_distribution,
                     load_tasks)
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


# ---------------------------------------------------------------- ccx_fea 分支

def _run_ccx_task(
    task: TaskSpec, code: str, meta: dict, t0: float, env_digest: str,
    logs: list[str], applicability: dict[str, str], timeout: float,
) -> dict[str, Any]:
    """ccx_fea：模型 python 脚本写出 model.inp（不执行求解器），runner 跑 ccx
    并解析 .dat 数值判分（structures 维，brew calculix-ccx）。

    两段执行（foam 同构）：脚本沙箱段只写文件；求解段由本 runner 调
    solvers.calculix.run_ccx。判分口径与 gtm_matlab 同构（result_keys/
    numeric_rel_tol，数值对 gold ccx 运行的相对误差）——mesh 自由度由
    题面钉死最小网格与单元类型，离散化差进容差带。
    """
    from .solvers.calculix import parse_dat, run_ccx
    import hashlib
    import math
    engineering = "deck_contract" in task["grader"]
    deck_audit = None
    solver_started = False
    grade_t0 = time.time()
    iso = IsolatedRun()
    script = iso.write("make_case.py", code)
    r1 = iso.run(script, min(timeout, 120.0))
    logs.append(f"make_case exit={r1['exit']} {r1['duration_s']}s")

    def _ret(gate: int, gf: list[str], fm: str | None, subs: dict, details: dict):
        artifacts = {"code": json.dumps(code[:4000], ensure_ascii=False),
                     "model_meta": json.dumps(meta, ensure_ascii=False)}
        if engineering:
            evidence = {"complete": True, "files": {}}
            for name in ("make_case.py", "model.inp", "model.dat", "model.solver.log"):
                path = iso.dir / name
                if name != "make_case.py" and not path.exists() and not path.is_symlink():
                    continue
                if name != "make_case.py" and (path.is_symlink() or not path.is_file() or path.stat().st_size > 8*1024*1024):
                    evidence["complete"] = False
                    evidence["files"][name] = {"error": "not a regular file or over 8 MiB"}
                    continue
                raw = code.encode("utf-8") if name == "make_case.py" else path.read_bytes()
                try:
                    content = raw.decode("utf-8")
                except UnicodeError:
                    evidence["complete"] = False
                    evidence["files"][name] = {"error": "not UTF-8"}
                    continue
                evidence["files"][name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "text": content,
                                           "origin": "submitted_code" if name == "make_case.py" else "generated_input" if name == "model.inp" else "solver" if solver_started else "untrusted_candidate_output"}
            if not evidence["complete"]:
                gate, gf, fm = 0, gf + ["evidence_capture_failed"], "evidence_capture_failed"
            details = {"kind": "ccx_fea", **details, "deck_audit": deck_audit,
                       "evidence_files": {k: {f: v for f, v in value.items() if f != "text"}
                                          for k, value in evidence["files"].items()}}
            artifacts["engineering_evidence"] = json.dumps(evidence, ensure_ascii=False)
        artifacts["grade_details"] = json.dumps(details, ensure_ascii=False)
        weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
        score = aggregate_score({k: (v if v is not None else 0.0)
                                 for k, v in subs.items()}, weights, gate)
        return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
            gate_failures=gf, subscores=subs, score=score,
            artifacts=artifacts,
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs, failure_mode=fm,
            applicability=applicability)

    if r1["timeout"] or r1["exit"] != 0:
        return _ret(0, ["timeout" if r1["timeout"] else _SCRIPT_FAIL],
                    "timeout" if r1["timeout"] else _SCRIPT_FAIL,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None},
                    {"stderr_tail": r1["stderr"][-800:]})

    inp = iso.dir / "model.inp"
    if not inp.exists():
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None}, {"missing": "model.inp"})

    if engineering:
        if inp.is_symlink() or not inp.is_file() or inp.stat().st_size > 8*1024*1024:
            return _ret(0, ["invalid_deck"], "invalid_deck", {}, {"reason": "model.inp must be a regular file up to 8 MiB"})
        from .solvers.cantilever_contract import audit_cantilever_deck
        try:
            deck_text = inp.read_text(encoding="utf-8")
        except UnicodeError:
            return _ret(0, ["invalid_deck"], "invalid_deck", {}, {"reason": "model.inp must be UTF-8"})
        deck_audit = audit_cantilever_deck(deck_text, task["grader"]["deck_contract"])
        if not deck_audit["passed"]:
            reason = "unsupported_deck_feature" if any(i["code"] == "unsupported_deck_feature" for i in deck_audit["issues"]) else "engineering_contract_failed"
            return _ret(0, [reason], reason,
                        {"physics": 0.0, "requirements": 0.0, "objective": None,
                         "robustness": None}, {"kind": "ccx_fea", "deck_audit": deck_audit})

    # The external-agent protocol has a separate generation timeout. Its network /
    # reasoning latency must not consume the declared artifact/solver budget.
    budget_t0 = grade_t0 if meta.get("provider") == "external" else t0
    if engineering:
        # Generated .dat/log files are not solver evidence. Remove them first.
        for name in ("model.dat", "model.solver.log", "model.frd", "model.sta", "model.cvg"):
            path = iso.dir / name
            if path.exists() or path.is_symlink():
                if path.is_dir() and not path.is_symlink():
                    return _ret(0, ["invalid_deck"], "invalid_deck", {}, {"reason": f"unexpected output directory: {name}"})
                path.unlink()
        solver_started = True
        rr = run_ccx(iso.dir, "model", timeout - (time.time() - budget_t0), capture_log=True)
    else:
        rr = run_ccx(iso.dir, "model", timeout - (time.time() - budget_t0))
    logs.append(f"ccx exit={rr['exit']} {rr['duration_s']}s"
                + (" TIMEOUT" if rr["timeout"] else ""))
    if rr["timeout"] or rr["exit"] != 0:
        return _ret(0, ["timeout" if rr["timeout"] else _SIM_FAIL],
                    "timeout" if rr["timeout"] else _SIM_FAIL,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None},
                    {"ccx_stdout_tail": rr["stdout_tail"][-800:]})

    g = task["grader"]
    if engineering and not (iso.dir / "model.dat").is_file():
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": 0.0, "objective": None, "robustness": None},
                    {"missing": "model.dat", "ccx_s": rr["duration_s"]})
    got = parse_dat(iso.dir / "model.dat", dict(g["extract"]))
    invalid_metrics = [k for k, value in got.items() if not math.isfinite(float(value))] if engineering else []
    for k in invalid_metrics:
        got.pop(k)
    keys = list(g["result_keys"])
    ref = dict(task["reference"]["values"])
    tol = float(g.get("numeric_rel_tol", 0.05))
    present = [k for k in keys if k in got]
    req_ratio = round(len(present) / len(keys), 4)
    if len(present) < len(keys):
        logs.append(f"missing keys: {sorted(set(keys) - set(got))}")

    hits: dict[str, Any] = {}
    for k in keys:
        if k not in got:
            hits[k] = {"status": "missing"}
            continue
        rv, gv = float(ref[k]), float(got[k])
        rel = abs(gv - rv) / max(abs(rv), 1e-12)
        hits[k] = {"status": "tol", "ok": bool(rel <= tol),
                   "rel_err": round(rel, 6), "got": gv, "ref": rv}
    n_ok = sum(1 for v in hits.values() if v.get("ok"))
    physics = round(n_ok / max(1, len(keys)), 4)
    subs = {"physics": physics, "requirements": req_ratio,
            "objective": None, "robustness": None}
    details = {"kind": "ccx_fea", "hits": hits,
               "physics_hits": f"{n_ok}/{len(keys)}", "rel_tol": tol,
               "ccx_s": rr["duration_s"]}
    if invalid_metrics:
        details["nonfinite_metrics"] = invalid_metrics
    if engineering and (len(present) != len(keys) or any(not math.isfinite(float(got[k])) for k in present)):
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT, subs, details)
    return _ret(1, [], None, subs, details)


# ---------------------------------------------------------------- cfdb 分支

_CFDB_REQUIRED = ["case/system/controlDict", "case/constant", "case/0"]
_CFDB_QOI_TIMEOUT_S = 120.0
_CFDB_DEFAULT_TOL = 0.05


def _cfdb_compare(
    ref_path: Path, got: dict, tols: dict, abs_tols: dict,
) -> tuple[float, dict, int, int]:
    """held_out 逐键容差对账（cfdb 双容差语义：零参考 QoI 用绝对容差，其余相对）。"""
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    hits: dict[str, Any] = {}
    n_ok = 0
    for k, rv in ref.items():
        gv = got.get(k)
        if not isinstance(gv, (int, float)) or not isinstance(rv, (int, float)):
            hits[k] = {"status": "missing" if gv is None else "type", "ref": rv,
                       "got": gv, "ok": False}
            continue
        rel = abs(float(gv) - float(rv)) / max(abs(float(rv)), 1e-12)
        abs_diff = abs(float(gv) - float(rv))
        if k in abs_tols:
            ok = abs_diff <= float(abs_tols[k])
            mode = "abs"
        else:
            ok = rel <= float(tols.get(k, _CFDB_DEFAULT_TOL))
            mode = "rel"
        hits[k] = {"status": mode, "ok": bool(ok), "rel_err": round(rel, 6),
                   "abs_diff": round(abs_diff, 9), "got": gv, "ref": rv,
                   "tol": float(abs_tols.get(k, tols.get(k, _CFDB_DEFAULT_TOL)))}
        n_ok += 1 if ok else 0
    return round(n_ok / max(1, len(ref)), 4), hits, n_ok, len(ref)


def _cfdb_run_frozen_qoi(
    qoi_path: Path, target_dir: Path, logs: list[str],
) -> dict | None:
    """冻结 QoI 脚本宿主执行（cfdb 协议：末行 stdout = JSON；失败返回 None）。"""
    import subprocess as _sp
    import sys as _sys
    try:
        rq = _sp.run([_sys.executable, "-B", str(qoi_path), str(target_dir)],
                     capture_output=True, text=True, timeout=_CFDB_QOI_TIMEOUT_S)
    except _sp.TimeoutExpired:
        logs.append(f"qoi_script timeout >{_CFDB_QOI_TIMEOUT_S}s")
        return None
    lines = [ln for ln in rq.stdout.strip().splitlines() if ln.strip()]
    if rq.returncode != 0 or not lines:
        logs.append(f"qoi exit={rq.returncode} stderr={rq.stderr[-300:]}")
        return None
    try:
        got = json.loads(lines[-1])
        if not isinstance(got, dict):
            raise ValueError("QoI 末行 JSON 顶层必须是对象")
        return got
    except Exception as e:  # noqa: BLE001
        logs.append(f"qoi parse: {e!r}")
        return None


def _run_cfdb_task(
    task: TaskSpec, code: str, meta: dict, t0: float, env_digest: str,
    logs: list[str], applicability: dict[str, str], timeout: float,
    assets_root: Path,
) -> dict[str, Any]:
    """cfdb_cfd_qoi / cfdb_case_setup（managed + evidence 工具通道）。

    managed 管线（2026-08-28 定案）：
      1. 模型脚本在沙箱 cwd 创建 case/ 完整算例（0/ constant/ system/）；
      2. 结构门：system/controlDict + constant/ + 0/ 缺一即 missing_output；
      3. 判分侧真实求解：docker opencfd v2312 按案例冻结 steps 执行；
      4. 冻结 QoI 脚本宿主执行（sys.executable -B）→ held_out 逐键容差对账。

    evidence 工具通道（2026-08-30 实装；两阶段候选协议）：
      1-3 同上（solver 由判分 harness 代跑 = agent 侧工具执行，产物为真实求解输出）；
      4. 写标记 .cfdb_assemble 后**重放候选脚本**（组装阶段）：从 case/ 运行产物
         提取原始数据组装证据包（manifest.json + evidence/*，文件清单为案例冻结
         契约）——自报 QoI 不进入任何环节；
      5. 证据包契约校验（清单齐全 + manifest 可解析）→ 冻结 QoI 脚本对**证据包根**
         降算（cfdb 上游 evidence 同款：Judge runs NO solver）→ held_out 对账。
    """
    from .solvers.openfoam_v2312 import OpenFOAMV2312
    grade_t0 = time.time()

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

    # 1) 沙箱跑脚本 → case/
    iso = IsolatedRun()
    script = iso.write("make_case.py", code)
    r1 = iso.run(script, min(timeout, 300.0))
    logs.append(f"make_case exit={r1['exit']} {r1['duration_s']}s")
    if r1["timeout"] or r1["exit"] != 0:
        return _ret(0, ["timeout" if r1["timeout"] else _SCRIPT_FAIL],
                    "timeout" if r1["timeout"] else _SCRIPT_FAIL,
                    {"physics": 0.0, "requirements": 0.0, "objective": None,
                     "robustness": None},
                    {"stdout_tail": r1["stdout"][-800:],
                     "stderr_tail": r1["stderr"][-800:]})

    # 2) 结构门
    case_dir = iso.dir / "case"
    present = [p for p in _CFDB_REQUIRED if (iso.dir / p).exists()]
    missing = [p for p in _CFDB_REQUIRED if p not in present]
    req_ratio = round(len(present) / len(_CFDB_REQUIRED), 4)
    logs.append(f"structure present={len(present)}/{len(_CFDB_REQUIRED)} missing={missing}")
    if missing:
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": req_ratio,
                     "objective": None, "robustness": None},
                    {"missing": missing})

    # 3) 真实求解（steps 声明执行）
    g = task["grader"]
    solver = OpenFOAMV2312()
    rr = solver.run_steps(iso.dir, g["steps"], timeout)
    exec_ok = solver.execution_ok(iso.dir, rr)
    logs.append(f"solver {solver.name} ok={rr['ok']} steps={rr['steps']}")
    if not exec_ok:
        return _ret(0, ["timeout" if any(s.get("timeout") for s in rr["steps"])
                        else _SIM_FAIL],
                    "timeout" if any(s.get("timeout") for s in rr["steps"])
                    else _SIM_FAIL,
                    {"physics": 0.0, "requirements": req_ratio,
                     "objective": None, "robustness": None},
                    {"steps": rr["steps"], "tail": rr["tail"][-800:]})

    # 4) 冻结 QoI：evidence 模式先走组装阶段 + 证据包契约，QoI 面向证据包根；
    #    managed 模式直接对 case/ 降算（两条路径同款宿主协议，判分材料不经模型）
    g = task["grader"]
    is_evidence = g.get("mode") == "evidence"
    if is_evidence:
        # —— 工具通道第二阶段：候选脚本从运行产物组装证据包 ——
        (iso.dir / ".cfdb_assemble").write_text("", encoding="utf-8")
        r2 = iso.run(script, min(timeout, 300.0))
        logs.append(f"assemble exit={r2['exit']} {r2['duration_s']}s "
                    f"stdout_tail={r2['stdout'][-200:]!r}")
        if r2["timeout"] or r2["exit"] != 0:
            return _ret(0, ["timeout" if r2["timeout"] else _SCRIPT_FAIL],
                        "timeout" if r2["timeout"] else _SCRIPT_FAIL,
                        {"physics": 0.0, "requirements": req_ratio,
                         "objective": None, "robustness": None},
                        {"assemble_stderr_tail": r2["stderr"][-600:]})
        bundle = iso.dir / "submission"   # 任务书合同：证据包根 = submission/
        required_ev = list(g.get("evidence_required_files") or [])
        missing_ev = [p for p in required_ev if not (bundle / p).exists()]
        manifest_ok = False
        try:
            manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
            manifest_ok = isinstance(manifest, dict) and bool(manifest.get("solver"))
        except Exception:
            pass
        logs.append(f"evidence missing={missing_ev} manifest_ok={manifest_ok}")
        if missing_ev or not manifest_ok:
            return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                        {"physics": 0.0, "requirements": req_ratio,
                         "objective": None, "robustness": None},
                        {"missing_evidence": missing_ev, "manifest_ok": manifest_ok})
        qoi_target = bundle  # 证据包根 = 提交目录（cfdb evidence 语义）
    else:
        qoi_target = case_dir

    qoi_path = assets_root / g["case_ref"] / g["qoi_script"]
    if not qoi_path.exists():
        return _ret(0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                    {"physics": 0.0, "requirements": req_ratio,
                     "objective": None, "robustness": None},
                    {"missing": f"qoi_script: {qoi_path}"})
    got = _cfdb_run_frozen_qoi(qoi_path, qoi_target, logs)
    if got is None:
        return _ret(0, [_SIM_FAIL], _SIM_FAIL,
                    {"physics": 0.0, "requirements": req_ratio,
                     "objective": None, "robustness": None},
                    {"qoi_error": "frozen qoi script failed (see logs)"})

    # 5) held_out 容差对账
    ref_path = assets_root / task["reference"]["held_out"]["path"]
    tols = task["reference"].get("tolerances") or {}
    abs_tols = task["reference"].get("abs_tolerances") or {}
    physics, hits, n_ok, n_ref = _cfdb_compare(ref_path, got, tols, abs_tols)
    details = {"kind": "cfdb_evidence" if is_evidence else "cfdb_managed",
               "hits": hits, "physics_hits": f"{n_ok}/{n_ref}",
               "steps": rr["steps"], "solver": solver.name}
    subs = {"physics": physics, "requirements": req_ratio,
            "objective": None, "robustness": None}
    logs.append(f"qoi hits={n_ok}/{n_ref} physics={physics}")
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
    elif kind == "ccx_fea":
        applicability = {"physics": "numeric_vs_reference", "requirements": "model.inp+dat 键完备",
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
    if kind == "cfd_step":
        from .solvers.cfd_step_runtime import evaluate
        grade_t0 = time.time()
        details = evaluate(task, code, timeout)
        gate = int(details['cfd_audit']['passed'])
        failures = [i['code'] for i in details['cfd_audit']['issues']]
        return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
            gate_failures=failures, subscores={'physics':float(gate),'requirements':float(gate),
                'objective':None,'robustness':None}, score=float(gate),
            artifacts={'code':json.dumps(code[:4000],ensure_ascii=False),
                'model_meta':json.dumps(meta,ensure_ascii=False),
                'grade_details':json.dumps(details,ensure_ascii=False)},
            timings={'agent_s':grade_t0-t0,'setup_s':0.0,'grade_s':time.time()-grade_t0},
            env_digest=env_digest, logs=logs, failure_mode=failures[0] if failures else None,
            applicability={'physics':'native wall shear reattachment vs reference',
                'requirements':'native inputs, mesh, convergence and mass balance',
                'objective':'N/A','robustness':'N/A'})
    if kind in ("aviary_mission", "pycycle_cycle"):
        return _run_aviary_task(task, code, meta, t0, env_digest, logs,
                                applicability, companions=companions)
    if kind == "gtm_matlab":
        return _run_matlab_task(task, code, meta, t0, env_digest, logs,
                                applicability, timeout)
    if kind == "ccx_fea":
        return _run_ccx_task(task, code, meta, t0, env_digest, logs,
                             applicability, timeout)
    if kind in ("cfdb_case_setup", "cfdb_cfd_qoi", "cfdb_case_setup_evidence"):
        # evidence 工具通道已实装（2026-08-30）：两阶段候选协议——
        # 判分 harness 代跑求解（agent 侧工具执行）→ 候选组装证据包 → 冻结 QoI 降算
        return _run_cfdb_task(task, code, meta, t0, env_digest, logs,
                              applicability, timeout, assets_root)

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
    if "subscore_applicability" in r:
        r["subscore_applicability"]["iteration"] = f"rounds {rounds_used}/{iterate}"
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
                    choices=["stub", "oracle", "openai_compat", "glm", "minimax", "external"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--resume", action="store_true",
                    help="仅复用身份匹配的完整结果；旧协议、损坏或条件不一致时"
                         "拒绝续写，请使用新 --out 目录")
    ap.add_argument("--allow-partial-oracle", action="store_true",
                    help="oracle 模式下跳过缺 oracle_source 的任务（增量 bring-up 用："
                         "部分案例 oracle 未编写时先验证其余；跳过记录进 logs）")
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
                if getattr(args, "allow_partial_oracle", False):
                    print(f"[partial-oracle] 跳过（无 oracle_source）: {t.id}")
                    continue
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
        if getattr(args, "allow_partial_oracle", False):
            before = len(tasks)
            tasks = [t for t in tasks if t.id in oracle_cache]
            print(f"[partial-oracle] 任务集 {before} -> {len(tasks)}（仅含已编写 oracle 的任务）")

    from .run_state import RunState, provider_identity, rerun_command
    model_label = provider_identity(args.provider, args.model)["model"]
    rerun = rerun_command("runners.simulation_agent", args, model_label)

    with RunState(out_dir=out_dir, tasks=tasks, prompts=prompt_cache,
                  adapter=ADAPTER, provider=args.provider, model=args.model,
                  seed=args.seed, env_digest=env_digest, assets=asset_hashes,
                  tasks_dir=tasks_dir, rerun=rerun, resume=args.resume,
                  options={"iterate": args.iterate, "limit": args.limit,
                           "scaffold": args.scaffold, "allow_partial_oracle": args.allow_partial_oracle},
                  extra={"model": model_label,
                         "harness_arm": ("H3" if args.scaffold and args.iterate > 1
                                         else "H2" if args.scaffold
                                         else "H1" if args.iterate > 1 else "H0"),
                         "scaffold": args.scaffold or None,
                         "iterate_rounds": args.iterate, "limit": args.limit,
                         "protocol": "iterate" if args.iterate > 1 else "single"},
                  runtime_inputs={name: common.sha256_bytes(content.encode())
                                  for name, content in companions}) as run:
        results, crash, resumed = [], 0, 0
        for t in tasks:
            if t.id in run.cached:
                results.append(run.cached[t.id])
                resumed += 1
                continue
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
