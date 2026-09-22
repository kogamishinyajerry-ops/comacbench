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
import shutil as _shutil
import threading
import time
from pathlib import Path
from typing import Any

from .common import (FM_MISSING_OUTPUT, TaskSpec, aggregate_score, build_result,
                     environment_digest, load_tasks, write_json_atomic)
from . import common
from .providers import ProviderError, get_answer
from .sandbox import IsolatedRun, static_check

_EV_LOCK = threading.Lock()  # evaluator 模块缓存写入锁（PR-B）

ADAPTER = "deliverable_review"
DEFAULT_WEIGHTS = {"physics": 0.55, "requirements": 0.45,
                   "objective": 0.0, "robustness": 0.0}

PROTOCOL = "comacbench.artifacts.v1"
MANIFEST = "manifest.json"
EVIDENCE_PROTOCOL = common.EVIDENCE_PROTOCOL
EVIDENCE_MANIFEST = common.EVIDENCE_MANIFEST
MAX_MANIFEST_BYTES = 256 * 1024
MAX_DELIVERABLES = 64
MAX_FILE_BYTES = 8 * 1024 * 1024
HASH_CHUNK = 1 << 20

_MANIFEST_MISSING = "manifest_missing"
_MANIFEST_INVALID = "manifest_invalid"
_PATH_ESCAPE = "deliverable_path_escape"
_TREE_MISMATCH = "deliverable_tree_mismatch"
_CONTENT_FAILED = "deliverable_content_check_failed"
_OVER_FILE_LIMIT = "over_file_limit"
_COPY_MISMATCH = "copy_mismatch"
_IRREGULAR = "missing or irregular"
EVALUATOR_OUTPUT = "evaluator_output.json"


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


def _hash_file(path: Path) -> tuple[str, int]:
    """流式读文件算 (sha256, 字节数)——不把整份内容解码成文本。"""
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as fh:
        while chunk := fh.read(HASH_CHUNK):
            h.update(chunk)
            total += len(chunk)
    return h.hexdigest(), total


def _capture_evidence(
    workspace: Path, rels: list[tuple[str, str]], ev_dir: Path | None,
) -> tuple[list[dict], bool]:
    """把交付原件按**二进制流**复制进证据目录，复制后重新核对 SHA-256 与长度。

    ``rels`` 是 (相对路径, origin) 序列。返回 (索引条目列表, complete)；
    索引条目形如 ``{"path", "sha256", "bytes", "origin"}``。任何一步不成立就写入
    ``error`` 并把 complete 置假——**绝不截断后仍宣称完整**，也**不猜编码**：
    原件按字节落盘，需要文本预览的复核方自行解码。
    """
    index: list[dict] = []
    complete = True
    for rel, origin in rels:
        src = workspace / rel
        entry: dict[str, Any] = {"path": rel}
        if not src.is_file() or src.is_symlink():
            entry["error"] = _IRREGULAR
            index.append(entry)
            complete = False
            continue
        size = src.stat().st_size
        if size > MAX_FILE_BYTES:
            # 超限显式失败，不做隐式截断
            entry.update({"bytes": size, "error": _OVER_FILE_LIMIT})
            index.append(entry)
            complete = False
            continue
        src_sha, src_len = _hash_file(src)
        if ev_dir is not None:
            dst = ev_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            with src.open("rb") as fh_in, dst.open("wb") as fh_out:
                _shutil.copyfileobj(fh_in, fh_out)
            dst_sha, dst_len = _hash_file(dst)
            if (dst_sha, dst_len) != (src_sha, src_len):
                # 复制没有忠实还原原件——归档不可信，如实记录而非静默接受
                entry.update({"sha256": dst_sha, "bytes": dst_len,
                              "source_sha256": src_sha,
                              "source_bytes": src_len, "error": _COPY_MISMATCH})
                index.append(entry)
                complete = False
                continue
        entry.update({"sha256": src_sha, "bytes": src_len, "origin": origin})
        index.append(entry)
    return index, complete


def write_evidence_manifest(
    ev_dir: Path, task_id: str, index: list[dict], complete: bool,
) -> Path:
    """证据目录自描述清单：复用前据此逐条核验（见 runners/run_state.py）。"""
    target = ev_dir / EVIDENCE_MANIFEST
    write_json_atomic(target, {
        "protocol": EVIDENCE_PROTOCOL, "task_id": task_id, "adapter": ADAPTER,
        "files": index, "complete": complete})
    return target


def evaluate_deliverables(
    task: TaskSpec, workspace: Path, manifest: dict,
) -> tuple[dict, list[str]]:
    """运行任务 YAML 声明的独立 evaluator，从文件内容复算。

    evaluator 是任务 YAML grader.evaluator 里的 ``module``（判分侧资产，
    位于 pack 的 private/ 下）：函数 ``evaluate(task, workspace, deliverables)
    -> {"checks": [{"name","passed","expected","actual"}], "summary": str}``。
    本函数不信任 evaluator 之外的任何自评。

    加载方式（PR-B 修复）：按 evaluator **文件内容 SHA256** 派生唯一模块名，
    经 spec_from_file_location 加载并缓存。绝不 import_module(mod_name)——
    sys.modules 按模块名缓存，同一进程先后载入 A/B 两个 pack 的同名
    evaluator 时 B 会命中 A 的缓存代码（验收 P1 实测复现）。
    """
    g = task["grader"]
    spec = g.get("evaluator") or {}
    mod_name = spec.get("module")
    checks: list[dict] = []
    notes: list[str] = []
    if not mod_name:
        return {"checks": checks, "summary": "no evaluator module declared",
                "evaluated": False}, []
    import hashlib
    import importlib.util
    import contextlib
    import io
    import sys
    import threading
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
    ev_file = pack_root / "private" / f"{mod_name}.py"
    if not ev_file.is_file():
        return {"checks": [], "summary": f"evaluator file missing: {mod_name}",
                "evaluated": False}, ["evaluator_error"]
    ev_sha = hashlib.sha256(ev_file.read_bytes()).hexdigest()
    cache_key = f"_comacbench_ev_{mod_name}_{ev_sha[:16]}"
    with _EV_LOCK:
        mod = sys.modules.get(cache_key)
        if mod is None:
            pyspec = importlib.util.spec_from_file_location(cache_key, ev_file)
            if pyspec is None or pyspec.loader is None:
                return {"checks": [], "summary": "evaluator spec unresolved",
                        "evaluated": False}, ["evaluator_error"]
            mod = importlib.util.module_from_spec(pyspec)
            sys.modules[cache_key] = mod
            try:
                pyspec.loader.exec_module(mod)
            except Exception as exc:
                # 加载期异常与运行期同等待遇：判分侧故障 → 结构化作废。
                # 此前这里 re-raise 会让 traceback 直接逸出 run_task，既不留
                # 结构化结果也不落 voided 标记，与执行/返回协议两阶段不一致。
                sys.modules.pop(cache_key, None)
                return {"checks": checks,
                        "summary": f"evaluator import crashed: "
                                   f"{type(exc).__name__}: {exc}",
                        "evaluated": False, "stage": "import",
                        "stderr": str(exc)}, ["evaluator_error"]
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
    if not isinstance(raw, list) or not raw:
        return {"checks": checks, "summary": "evaluator returned no checks",
                "evaluated": False}, ["evaluator_error"]
    names: set[str] = set()
    for c in raw:
        if not isinstance(c, dict) or not isinstance(c.get("name"), str):
            return {"checks": checks,
                    "summary": "evaluator protocol violation: bad check shape",
                    "evaluated": False}, ["evaluator_error"]
        if c["name"] in names:
            return {"checks": checks,
                    "summary": f"evaluator protocol violation: duplicate name {c['name']!r}",
                    "evaluated": False}, ["evaluator_error"]
        names.add(c["name"])
        if type(c.get("passed")) is not bool:
            # 字符串 "false" 等绝不能被 bool(...) 隐转成 True（验收 P1）
            return {"checks": checks,
                    "summary": "evaluator protocol violation: passed must be bool",
                    "evaluated": False}, ["evaluator_error"]
        checks.append({
            "name": c["name"],
            "passed": c["passed"],
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
    evidence_dir: Path | None = None,
) -> dict[str, Any]:
    t0 = time.time()
    prompt = prompt_override if prompt_override is not None else prompt_cache[task.id]
    timeout = float(task["limits"]["wall_clock_s"])
    # 证据目录的相对引用（相对 run 根）；result 与证据清单共用同一口径。
    evidence_rel_dir = (f"evidence/{task.id}" if evidence_dir is not None
                        else None)
    index: list[dict] | None = None   # 交付树被捕获后才有值（此前无可归档对象）
    archive_ok = False

    def _seal_evidence(extra: dict | None = None) -> None:
        """密封证据目录：补 evaluator 输出现场后重写清单（原子发布）。

        清单与 result 内联索引必须逐条相同——RunState 复用前靠这层交叉核对
        发现"只改了证据目录"的改动。
        """
        nonlocal index
        if evidence_dir is None or index is None:
            return
        if extra is not None:
            target = evidence_dir / EVALUATOR_OUTPUT
            write_json_atomic(target, extra)
            sha, size = _hash_file(target)
            index = [e for e in index if e["path"] != EVALUATOR_OUTPUT]
            index.append({"path": EVALUATOR_OUTPUT, "sha256": sha,
                          "bytes": size, "origin": "evaluator_output"})
        write_evidence_manifest(evidence_dir, task.id, index, archive_ok)

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
    # PR-B 证据归档（二进制原件）：声明树 ∪ 实际树 ∪ agent 自己的 manifest.json。
    # 原件按字节复制进 evidence/<task_id>/，复制后复算 SHA-256 与长度；
    # result.json 只存**索引**（path/sha256/bytes/origin），不存内容——
    # JSON 无法承载任意字节，把内容塞进 JSON 正是此前行尾被改写、大文件被
    # 截断的根因。超限/复制不一致一律显式失败，不隐式截断。
    declared_rel = {p.relative_to(ws).as_posix() for p in declared}
    rels: list[tuple[str, str]] = [
        (r, "declared_deliverable" if r in declared_rel else "undeclared_file")
        for r in sorted({p.relative_to(ws).as_posix()
                         for p in set(declared) | set(actual)})]
    if (ws / MANIFEST).is_file() and not (ws / MANIFEST).is_symlink():
        rels.append((MANIFEST, "agent_declaration"))
    index, archive_ok = _capture_evidence(ws, rels, evidence_dir)
    evidence = {"complete": archive_ok,
                "files": {e["path"]: {k: v for k, v in e.items()
                                      if k != "path"} for e in index}}
    if issues or not evidence["complete"]:
        _seal_evidence()
        return _fail(issues or ["evidence_capture_failed"],
                     (issues or ["evidence_capture_failed"])[0],
                     {**details, "stage": "manifest_tree",
                      "manifest": manifest,
                      "evidence_files": {k: {f: v for f, v in val.items()
                                             if f != "text"}
                                         for k, val in evidence["files"].items()}})

    ev, ev_issues = evaluate_deliverables(task, ws, manifest)
    # PR-B 故障三分：evaluator 崩溃/协议违规 = 判分侧基础设施故障 → 作废
    # （completion 按 result['voided'] 识别，见 comacbench/completion.py）。
    # 不得把基础设施作废算成 agent 零分，也不得删除该任务的 result。
    grade_details = {**details, "evaluator": ev}
    _seal_evidence(grade_details)
    if "evaluator_error" in ev_issues:
        res = build_result(task=task, adapter=ADAPTER, validity_gate=0,
            gate_failures=["infrastructure_voided"],
            subscores={"physics": None, "requirements": None, "objective": None,
                       "robustness": None}, score=0.0,
            artifacts={"code": json.dumps(code[:4000], ensure_ascii=False),
                       "model_meta": json.dumps(meta, ensure_ascii=False),
                       "deliverable_files": json.dumps(index,
                                                       ensure_ascii=False),
                       "deliverable_files_dir": evidence_rel_dir,
                       "grade_details": json.dumps(
                           {**details, "stage": "evaluator",
                            "evaluator": ev, "error_origin": "evaluator"},
                           ensure_ascii=False)},
            timings={"agent_s": grade_t0 - t0, "setup_s": 0.0,
                     "grade_s": time.time() - grade_t0},
            env_digest=env_digest, logs=logs,
            failure_mode="crash",  # 对齐 completion.VOIDED_FAILURE_MODES
            applicability=applicability)
        res["voided"] = True  # completion.result_issues 按 voided 布尔识别
        return res
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
    # 归档已在 IsolatedRun 存活期内完成（见上方 _capture_evidence）：原件是
    # evidence/<task_id>/ 下的字节，result 只持索引与目录引用。哈希是索引，
    # 复核者离线比对证据目录；复用前再由 RunState 逐条复算（fail-closed）。
    result = build_result(task=task, adapter=ADAPTER, validity_gate=gate,
        gate_failures=[] if gate else failures,
        subscores={"physics": phy, "requirements": req, "objective": None,
                   "robustness": None}, score=score,
        artifacts={"code": json.dumps(code, ensure_ascii=False),
                   "model_meta": json.dumps(meta, ensure_ascii=False),
                   "engineering_evidence": json.dumps(evidence,
                                                      ensure_ascii=False),
                   "deliverable_files": json.dumps(index,
                                                   ensure_ascii=False),
                   "deliverable_files_dir": evidence_rel_dir,
                   "grade_details": json.dumps(grade_details,
                                               ensure_ascii=False)},
        timings={"agent_s": grade_t0 - t0, "setup_s": 0.0,
                 "grade_s": time.time() - grade_t0},
        env_digest=env_digest, logs=logs,
        failure_mode=failures[0] if failures else None,
        applicability=applicability)
    return result


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="deliverable_review adapter runner")
    ap.add_argument("--tasks", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="stub")
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed", type=int, default=0)
    # PR-B：与上层 CLI（run_suite）协议一致的可信复跑。B04 基线：传 --resume
    # 曾直接 argparse 退出 2。行为复用 RunState（与 code_exec 同机制）：
    # 同身份（env/资产/任务清单一致）→ 已完成任务复用不重跑；身份变化 →
    # _reject 拒绝复用并要求新目录（旧证据不覆盖）。
    ap.add_argument("--resume", action="store_true",
                    help="reuse valid results from the same run identity")
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

    from .run_state import RunState, provider_identity, rerun_command
    model_label = provider_identity(args.provider, args.model)["model"]
    rerun = rerun_command("runners.deliverable_review", args, model_label)
    assets = {}
    for t in tasks:
        for a in (t["input"].get("assets") or []):
            ap2 = pack_root / a["path"]
            if ap2.is_file():
                assets[a["path"]] = hashlib.sha256(ap2.read_bytes()).hexdigest()
        ev_src = (t["grader"].get("evaluator") or {}).get("module")
        if ev_src:
            evp = pack_root / "private" / f"{ev_src}.py"
            if evp.is_file():
                assets[f"evaluator:{ev_src}"] = hashlib.sha256(
                    evp.read_bytes()).hexdigest()

    with RunState(out_dir=out, tasks=tasks, prompts=prompt_cache,
                  adapter=ADAPTER, provider=args.provider, model=args.model,
                  seed=args.seed, env_digest=env, assets=assets,
                  tasks_dir=Path(args.tasks), rerun=rerun,
                  resume=args.resume) as run:
        results, resumed = [], 0
        for t in tasks:
            if t.id in run.cached:
                results.append(run.cached[t.id])
                resumed += 1
                print(f"{t.id}: reused (resume)")
                continue
            r = run_task(t, provider=args.provider, model=args.model,
                         seed=args.seed, env_digest=env,
                         prompt_cache=prompt_cache, assets_root=Path(args.tasks),
                         oracle_cache=oracle_cache or None,
                         evidence_dir=out / "evidence" / t.id)
            # 证据归档已在 run_task 内完成（IsolatedRun 存活期内按二进制流复制原件，
            # 并在写 result 之前密封 evidence_manifest.json）。此处不再补写任何
            # 证据文件——否则会出现"清单未覆盖的归档物"，复用核验将无从对账。
            results.append(r)
            run.write_result(t, r)
            print(f"{t.id}: gate={r['validity_gate']} score={r['score']}"
                  + (" voided" if r.get("voided") else ""))
        run.finish(resumed_tasks=resumed)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
