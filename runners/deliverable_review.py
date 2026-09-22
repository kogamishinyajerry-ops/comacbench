"""deliverable_review.py — 文件制品交付判分 adapter（artifacts.v1 协议，工作项 C）。

定位（推进方案 §2.1/§4）：
  现有 agent.v1 是「一次 JSON 请求 → 一个 answer 字符串」；工程师实际交付的是
  **一套文件**（规范化数据、拒收记录、清单、报告）。本 adapter 引入可选的
  工作包执行类型：agent 交付 manifest + 文件树，evaluator **独立从文件内容**
  复算判分——不看 agent 自述，不看叙述是否像报告。

协议（comacbench.artifacts.v1）：
  1. agent.answer 仍是一段代码（与既有 answer_format: code 一致），由沙箱执行
     后在 workspace/ 产出文件树；runner 另读 **manifest.json**（agent 必须产出）
     声明「我交付了什么」：{"protocol": "comacbench.artifacts.v1",
                              "deliverables": [{"path": "outputs/results.csv",
                                                "kind": "result_table"}]}
  2. evaluator（任务 YAML 的 grader.evaluator）从**文件内容**独立复算：
     每个声明制品一个 verdict（present/missing/invalid + 内容级检查结果），
     不信任 manifest 里的任何自评字段。
  3. 判分口径：
     - requirements = 声明制品存在、可解析、manifest 与实际文件树一致（不多不少）；
     - physics     = evaluator 的内容级数值/语义断言通过率；
     - objective/robustness = N/A（静态交付；YAML 显式置 0 权重）。
  4. 负例必须命中命名诊断（与 ccx_fea 同构）：manifest 缺失、路径逃逸、
     交付与 manifest 不符、内容断言失败各自成码。

安全边界（与既有沙箱纪律一致）：
  - 路径规范化后必须仍在 workspace 内（拒绝对路径/../ 与符号链接）；
  - 文件大小/数量上限来自任务 limits；
  - evaluator 以只读方式接触文件树；evaluator 代码是判分侧资产（private/），
    与 oracle 同级，不在 agent 可见范围内。
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from .common import (FM_MISSING_OUTPUT, TaskSpec, aggregate_score,
                     build_result, environment_digest, load_tasks)
from .providers import ProviderError, get_answer
from .sandbox import IsolatedRun, static_check

ADAPTER = "deliverable_review"
DEFAULT_WEIGHTS = {"physics": 0.55, "requirements": 0.45,
                   "objective": 0.0, "robustness": 0.0}

PROTOCOL = "comacbench.artifacts.v1"
MANIFEST = "manifest.json"
MAX_MANIFEST_BYTES = 256 * 1024
MAX_DELIVERABLES = 64
MAX_FILE_BYTES = 8 * 1024 * 1024

_MANIFEST_MISSING = "manifest_missing"
_MANIFEST_INVALID = "manifest_invalid"
_PATH_ESCAPE = "deliverable_path_escape"
_TREE_MISMATCH = "deliverable_tree_mismatch"
_CONTENT_FAILED = "deliverable_content_check_failed"


def _safe_rel(path: str, root: Path) -> Path | None:
    """把 manifest 声明的相对路径安全解析到 root 内；逃逸/绝对路径返回 None。"""
    if not isinstance(path, str) or not path.strip() or "\x00" in path:
        return None
    p = (root / path).resolve()
    if not p.is_relative_to(root):
        return None
    return p


def read_manifest(workspace: Path) -> tuple[dict | None, list[str]]:
    """读并校验 agent 的 manifest.json；返回 (manifest, issues)。"""
    mp = workspace / MANIFEST
    if not mp.is_file() or mp.is_symlink():
        return None, [_MANIFEST_MISSING]
    if mp.stat().st_size > MAX_MANIFEST_BYTES:
        return None, [_MANIFEST_INVALID]
    try:
        m = json.loads(mp.read_text(encoding="utf-8"))
    except (ValueError, OSError, UnicodeError):
        return None, [_MANIFEST_INVALID]
    if not isinstance(m, dict) or m.get("protocol") != PROTOCOL:
        return None, [_MANIFEST_INVALID]
    dl = m.get("deliverables")
    if not isinstance(dl, list) or not dl or len(dl) > MAX_DELIVERABLES:
        return None, [_MANIFEST_INVALID]
    for d in dl:
        if not isinstance(d, dict) or not isinstance(d.get("path"), str):
            return None, [_MANIFEST_INVALID]
        if not isinstance(d.get("kind"), str) or not d["kind"].strip():
            return None, [_MANIFEST_INVALID]
    return m, []


def declared_tree(manifest: dict, root: Path) -> tuple[list[Path], list[str]]:
    """manifest 声明的制品路径集（安全解析）；返回 (paths, issues)。"""
    out: list[Path] = []
    issues: list[str] = []
    seen: set[str] = set()
    for d in manifest["deliverables"]:
        rel = d["path"]
        if rel in seen:
            issues.append(_TREE_MISMATCH)
            continue
        seen.add(rel)
        p = _safe_rel(rel, root)
        if p is None:
            issues.append(_PATH_ESCAPE)
            continue
        out.append(p)
    return out, issues


def actual_tree(workspace: Path, declared: list[Path]) -> tuple[list[Path], list[str]]:
    """workspace 里实际存在的交付文件（排除平台投递的 inputs/ 与 runner 自身文件）。"""
    reserved = {workspace / "make_case.py", workspace / MANIFEST}
    out: list[Path] = []
    issues: list[str] = []
    for p in sorted(workspace.rglob("*")):
        if p.is_dir() or p in reserved:
            continue
        rel = p.relative_to(workspace)
        if rel.parts and rel.parts[0] == "inputs":
            # 平台投递的只读输入（判分环境放置，不经 agent 之手）——不是交付物
            continue
        if p.is_symlink() or not p.is_file():
            issues.append(_TREE_MISMATCH)
            continue
        if p.stat().st_size > MAX_FILE_BYTES:
            issues.append(_TREE_MISMATCH)
            continue
        out.append(p)
    return out, issues


def evaluate_deliverables(
    task: TaskSpec, workspace: Path, manifest: dict,
) -> tuple[dict, list[str]]:
    """运行任务 YAML 声明的独立 evaluator，从文件内容复算。

    evaluator 是任务 YAML grader.evaluator 里的 ``module``（判分侧资产，
    位于 pack 的 private/ 下）：函数 ``evaluate(task, workspace, deliverables)
    -> {"checks": [{"name","passed","expected","actual"}], "summary": str}``。
    本函数不信任 evaluator 之外的任何自评。
    """
    g = task["grader"]
    spec = g.get("evaluator") or {}
    mod_name = spec.get("module")
    checks: list[dict] = []
    notes: list[str] = []
    if not mod_name:
        return {"checks": checks, "summary": "no evaluator module declared",
                "evaluated": False}, []
    import importlib
    import contextlib
    import io
    import sys
    # evaluator 是 pack 的 private/ 资产：按「pack 根 = 任务 YAML 的 tasks/ 上级」
    # 定位并临时挂到 sys.path（与 oracle_source 的解析层级一致）。
    yaml_path = getattr(task, "yaml_path", None)
    if yaml_path is None and isinstance(task.get("_yaml_path"), str):
        yaml_path = task["_yaml_path"]
    if yaml_path is None:
        # 兜底：tests 直接传 dict 时按 workspace 邻域找不到——保持可测：
        # evaluate_deliverables 的调用方（run_task）保证传入 TaskSpec。
        return {"checks": [], "summary": "no task yaml path; evaluator unresolved",
                "evaluated": False}, []
    # yaml 在 <pack>/tasks/<suite>/x.yaml => parents[2] 是 pack 根。
    pack_root = Path(yaml_path).resolve().parents[2]
    # evaluator 位于 pack/private/（与 oracle_source 同层）：挂 private 目录导入。
    ev_dir = pack_root / "private"
    inserted = str(ev_dir) not in sys.path
    if inserted:
        sys.path.insert(0, str(ev_dir))
    try:
        mod = importlib.import_module(mod_name)
    finally:
        if inserted:
            try:
                sys.path.remove(str(ev_dir))
            except ValueError:
                pass
    deliverables = [{"path": d["path"], "kind": d["kind"]}
                    for d in manifest["deliverables"]]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            out = mod.evaluate(task, workspace, deliverables)
    except Exception as exc:  # evaluator 崩溃是判分侧缺陷，不是 agent 的分数
        return {"checks": checks, "summary": f"evaluator crashed: {exc}",
                "evaluated": False, "stderr": str(exc)}, ["evaluator_error"]
    raw = out.get("checks") if isinstance(out, dict) else None
    if not isinstance(raw, list):
        return {"checks": checks, "summary": "evaluator returned no checks",
                "evaluated": False}, ["evaluator_error"]
    for c in raw:
        if not isinstance(c, dict) or not isinstance(c.get("name"), str):
            continue
        checks.append({
            "name": c["name"],
            "passed": bool(c.get("passed")),
            "expected": c.get("expected"),
            "actual": c.get("actual"),
        })
    failed = [c["name"] for c in checks if not c["passed"]]
    return {"checks": checks, "summary": out.get("summary", ""),
            "evaluated": True,
            "failed": failed}, ([_CONTENT_FAILED] if failed else [])


def run_task(
    task: TaskSpec, *, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str], assets_root: Path,
    oracle_cache: dict[str, str] | None = None,
    companions: list[tuple[str, str]] | None = None,
    prompt_override: str | None = None,
) -> dict[str, Any]:
    from typing import Any
    t0 = time.time()
    prompt = prompt_override if prompt_override is not None else prompt_cache[task.id]
    timeout = float(task["limits"]["wall_clock_s"])

    if provider == "oracle":
        code = oracle_cache[task.id]
        meta: dict[str, Any] = {"provider": "oracle",
                                "note": "deliverables verbatim writer"}
    else:
        out = get_answer(provider, task, prompt, seed=seed, model=model,
                         max_attempts=int(task["limits"]["attempts"]),
                         expect="code")
        code, meta = out["answer"], out["meta"]

    if provider == "oracle":
        violations, syntax_ok = [], True
    else:
        violations, syntax_ok = static_check(code)
    logs = [f"violations={violations}", f"syntax_ok={syntax_ok}"]
    applicability = {"physics": "independent evaluator over file contents",
                     "requirements": "manifest+tree consistency",
                     "objective": "N/A(static deliverable)",
                     "robustness": "N/A(no perturbation rerun)"}

    def _fail(gate_failures: list[str], fm: str, details: dict):
        return build_result(task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=gate_failures,
            subscores={"physics": 0.0, "requirements": 0.0, "objective": None,
                       "robustness": None}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "grade_details": json.dumps(details, ensure_ascii=False)},
            timings={"agent_s": time.time() - t0, "setup_s": 0.0,
                     "grade_s": 0.0},
            env_digest=env_digest, logs=logs, failure_mode=fm,
            applicability=applicability)

    if violations:
        return _fail(["sandbox_escape_attempt"], "sandbox_escape_attempt",
                     {"kind": ADAPTER, "stage": "static_check"})
    if not syntax_ok:
        return _fail([_SCRIPT_FAIL := "script_syntax_invalid"], _SCRIPT_FAIL,
                     {"kind": ADAPTER, "stage": "static_check"})

    grade_t0 = time.time()
    iso = IsolatedRun()
    # 输入资产投递（与 code_exec sandbox_inputs 同构：判分环境放置，不经 agent 之手）
    import shutil as _shutil
    pack_root = Path(task.yaml_path).resolve().parents[2]
    for a in (task["input"].get("assets") or []):
        src = pack_root / a["path"]
        if src.is_file():
            dst = iso.dir / "inputs" / a["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            _shutil.copy(src, dst)
    if any((iso.dir / "inputs").rglob("*")):
        os.environ.setdefault("WORKLOAD_INPUTS", str(iso.dir / "inputs"))
    script = iso.write("make_case.py", code)
    r1 = iso.run(script, min(timeout, 300.0))
    logs.append(f"make_case exit={r1['exit']} {r1['duration_s']}s")
    ws = iso.dir
    details: dict[str, Any] = {"kind": ADAPTER,
                               "make_case_exit": r1["exit"],
                               "make_case_timeout": bool(r1["timeout"])}
    if r1["timeout"] or r1["exit"] != 0:
        return _fail([FM_MISSING_OUTPUT], FM_MISSING_OUTPUT,
                     {**details, "stage": "make_case"})

    manifest, m_issues = read_manifest(ws)
    if m_issues:
        return _fail(m_issues, m_issues[0], {**details, "stage": "manifest"})

    declared, d_issues = declared_tree(manifest, ws)
    actual, a_issues = actual_tree(ws, declared)
    tree_ok = sorted(p.relative_to(ws).as_posix() for p in declared) == \
              sorted(p.relative_to(ws).as_posix() for p in actual)
    issues = list(dict.fromkeys(d_issues + a_issues +
                                ([] if tree_ok else [_TREE_MISMATCH])))
    evidence = {"complete": True, "files": {}}
    for p in sorted(set(declared) | set(actual)):
        rel = p.relative_to(ws).as_posix()
        if p.is_file() and not p.is_symlink():
            raw = p.read_bytes()
            evidence["files"][rel] = {
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                "origin": "declared_deliverable" if p in declared else
                          "undeclared_file"}
        else:
            evidence["complete"] = False
            evidence["files"][rel] = {"error": "missing or irregular"}
    if issues or not evidence["complete"]:
        return _fail(issues or ["evidence_capture_failed"],
                     (issues or ["evidence_capture_failed"])[0],
                     {**details, "stage": "manifest_tree",
                      "manifest": manifest, "evidence_files": {
                          k: {f: v for f, v in val.items() if f != "text"}
                          for k, val in evidence["files"].items()}})

    ev, ev_issues = evaluate_deliverables(task, ws, manifest)
    checks = ev["checks"]
    passed = sum(1 for c in checks if c["passed"])
    req = 1.0 if (tree_ok and not issues) else 0.0
    phy = (passed / len(checks)) if checks else 0.0
    gate = int(bool(checks) and phy == 1.0 and req == 1.0)
    failures = list(dict.fromkeys(ev_issues + [c["name"] for c in checks
                                               if not c["passed"]]))
    weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}
    score = aggregate_score({"physics": phy, "requirements": req,
                             "objective": 0.0, "robustness": 0.0},
                            weights, gate)
    return build_result(task=task, adapter=ADAPTER, validity_gate=gate,
        gate_failures=[] if gate else failures,
        subscores={"physics": phy, "requirements": req, "objective": None,
                   "robustness": None}, score=score,
        artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                   "model_meta": json.dumps(meta, ensure_ascii=False),
                   "engineering_evidence": json.dumps(evidence,
                                                      ensure_ascii=False),
                   "grade_details": json.dumps({**details, "evaluator": ev},
                                               ensure_ascii=False)},
        timings={"agent_s": grade_t0 - t0, "setup_s": 0.0,
                 "grade_s": time.time() - grade_t0},
        env_digest=env_digest, logs=logs,
        failure_mode=failures[0] if failures else None,
        applicability=applicability)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="deliverable_review adapter runner")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="stub")
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    tasks = load_tasks(args.tasks)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    env = environment_digest()
    # prompt_file 相对 pack 根（tasks/ 的上级），与校验器的解析口径一致
    pack_root = Path(args.tasks).resolve().parents[1]
    prompt_cache = {t.id: (pack_root / t["input"]["prompt_file"]).read_text(
        encoding="utf-8") for t in tasks}
    oracle_cache = {}
    if args.provider == "oracle":
        for t in tasks:
            src = t["grader"].get("oracle_source")
            if not src:
                raise SystemExit(f"{t.id}: oracle 模式需要 grader.oracle_source")
            p = pack_root / src
            oracle_cache[t.id] = p.read_text(encoding="utf-8")
    for t in tasks:
        r = run_task(t, provider=args.provider, model=args.model,
                     seed=args.seed, env_digest=env,
                     prompt_cache=prompt_cache, assets_root=Path(args.tasks),
                     oracle_cache=oracle_cache or None)
        (out / f"result_{t.id}.json").write_text(
            json.dumps(r, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{t.id}: gate={r['validity_gate']} score={r['score']}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
