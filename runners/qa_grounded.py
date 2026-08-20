"""qa_grounded.py — 有据问答 adapter（五类标准 adapter 之一，YAML 驱动）。

适用（adapters/README.md §1）：aeroengqa.gold、cfdllm.cfdquery、mechvqa、camb。
判分管线（严格顺序）：
  1. ValidityGate：output_contract 声明的答案字段缺失/不可解析 => missing_output，gate=0；
  2. 客观层：选择题选项精确匹配（本实现）；
  3. 证据层/拒答层：仅当任务 YAML 声明证据语料或应拒答标记时启用（cfdquery 无）；
  4. 区分层（可选）：AeroEngQA 专项，未声明则并入客观层。
LLM judge 只允许评"解释质量"且单独报告，不进 score —— 本 adapter 不实现 judge。

子分映射：requirements=客观层；physics=证据层+拒答层（未声明=不适用）；
          objective=区分层（未声明并入 requirements）；robustness=多次采样一致性（可选）。

CLI（cfdquery 冒烟基线示例）：
  cd benchmarks && python3 -m runners.qa_grounded \
      --tasks tasks/cfdllm.cfdquery \
      --out results/cfdllm.cfdquery/2026-08-19 \
      --provider stub --seed 0
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
from .providers import PROVIDER_PRESETS, ProviderError, get_answer

ADAPTER = "qa_grounded"

# adapter 默认权重（scoring/README.md §2；任务 YAML 可覆写）
DEFAULT_WEIGHTS = {"physics": 0.35, "requirements": 0.30,
                   "objective": 0.20, "robustness": 0.15}


# ---------------------------------------------------------------- gate

def validity_gate(
    task: TaskSpec, model_out: dict[str, Any] | None,
) -> tuple[int, list[str], str | None]:
    """qa_grounded 硬门槛：契约答案字段必须存在且可解析（缺产物=missing_output）。"""
    if model_out is None or model_out.get("answer") is None:
        return 0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT
    ans = model_out["answer"]
    opts = task["reference"].get("n_options", 4)
    if not (isinstance(ans, int) and 1 <= ans <= opts):
        return 0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT
    return 1, [], None


# ---------------------------------------------------------------- objective layer

def grade_objective(task: TaskSpec, answer: int) -> float:
    ref = int(task["reference"]["correct_option_index"])
    return 1.0 if answer == ref else 0.0


# ---------------------------------------------------------------- free-text layers
# AeroEngQA 类任务：结构化输出 ANSWER/BASIS/CITATION，全部规则判分（无 LLM judge）。

_ANSWER_RE = None  # 延迟编译占位（见 _compile）
_REFUSAL_PATTERNS = (
    "cannot answer", "can't answer", "cannot be answered",
    "cannot determine", "can't determine", "cannot be determined",
    "not specified", "not stated", "not provided", "not mentioned",
    "not contained", "not include", "not addressed", "no information",
    "insufficient information", "unable to answer", "unable to determine",
    "no answer", "unknown", "无法回答", "无法确定", "未提供", "未提及", "不知道",
)
_BASIS_VALID = {"report", "computed", "inferred", "报告原文", "计算", "推断"}


def parse_structured(text: str) -> dict:
    """解析结构化 free-text 输出 -> {answer_text, refused, basis, citations}。

    - ANSWER 行缺失或为空 => gate 判 missing_output（返回 refused=None 标记）；
    - refused 由 ANSWER 文本判定（显式 REFUSED 或拒答短语，规则表见上）；
    - BASIS/CITATION 缺失不挂 gate，分别计入区分层/证据层扣分。
    """
    import re as _re
    lines = text.strip().splitlines()
    fields: dict[str, str] = {}
    for ln in lines:
        m = _re.match(r"\s*(ANSWER|BASIS|CITATION)\s*[:：]\s*(.*)", ln, _re.I)
        if m:
            fields.setdefault(m.group(1).upper(), m.group(2).strip())
    answer_text = fields.get("ANSWER")
    if answer_text is None or not answer_text.strip():
        return {"answer_text": None, "refused": None, "basis": None,
                "citations": []}
    low = answer_text.lower().strip()
    # 拒答判定：显式 REFUSED 开头，或词边界匹配拒答短语表。
    # 不用裸 "refused" 词边界——事实性答案可能含该词（如 "the pilot refused the clearance"）。
    import re as _re2
    refused = low.startswith("refused") or low.startswith("refuse:") or any(
        _re2.search(rf"\b{_re2.escape(p)}\b", low) for p in _REFUSAL_PATTERNS)
    basis = (fields.get("BASIS") or "").strip().lower() or None
    cite_raw = (fields.get("CITATION") or "").strip()
    citations = sorted({int(x) for x in _re2.findall(r"\d+", cite_raw)})
    return {"answer_text": answer_text.strip(), "refused": refused,
            "basis": basis, "citations": citations}


_NUM_RE = None
_WORD_RE = None
_STOPWORDS = {"the", "a", "an", "of", "to", "is", "are", "was", "were", "and",
              "or", "in", "on", "for", "by", "with", "at", "it", "its", "be",
              "about", "approx", "approximately", "than", "that", "this"}


def _norm_text(s: str) -> str:
    import re as _re
    return " ".join(_re.findall(r"[a-z0-9]+", s.lower()))


def _numbers(s: str) -> set[float]:
    import re as _re
    return {float(x) for x in _re.findall(r"-?\d+(?:\.\d+)?", s)}


def _token_f1(ref: str, ans: str) -> float:
    rt = [t for t in _norm_text(ref).split() if t not in _STOPWORDS]
    at = [t for t in _norm_text(ans).split() if t not in _STOPWORDS]
    if not rt or not at:
        return 0.0
    common = sum(1 for t in at if t in rt)  # 简化多重集合交
    prec, rec = common / len(at), common / len(rt)
    return 2 * prec * rec / (prec + rec) if prec + rec else 0.0


def grade_free_text_objective(ref_answer: str, answer_text: str,
                              numeric_rel_tol: float = 0.05) -> float:
    """自由文本客观层：归一化精确 -> 数值集容差匹配 -> token F1（部分分）。

    adapters/README.md §1：「自由文本按 Exact/F1/关键字数值容差（数值题 ±ε）」。
    """
    rn, an = _norm_text(ref_answer), _norm_text(answer_text)
    if rn == an:
        return 1.0
    rnums, anums = _numbers(ref_answer), _numbers(answer_text)
    if rnums and anums:
        def close(a: float, b: float) -> bool:
            return abs(a - b) <= numeric_rel_tol * max(abs(b), 1e-9)
        if all(any(close(a, r) for a in anums) for r in rnums) and anums:
            return 1.0
    return round(_token_f1(ref_answer, answer_text), 4)


def grade_refusal(refusal_expected: bool, refused: bool) -> float:
    """拒答层：应拒答回答了=0，正确拒答=1；应回答拒答=0，正常回答=1。"""
    return 1.0 if refusal_expected == refused else 0.0


def grade_evidence(citations: list[int], n_contexts: int,
                   needed: list[int], refused: bool,
                   refusal_expected: bool) -> tuple[float, float]:
    """证据层 -> (evidence_support, fabrication_rate)，段落级规则判。

    - fabrication_rate：引用的不存在段落占比（[1,2] 之外即捏造）；
    - answerable：support = |cited∩needed|/|needed|，拒答=0；
    - unanswerable：无 needed（空集），support 只看是否捏造（引用真实段落解释
      「上下文未包含答案」是合法行为，不因引用而扣分）。
    """
    available = set(range(1, n_contexts + 1))
    cited = set(citations)
    fabricated = cited - available
    fab_rate = round(len(fabricated) / len(cited), 4) if cited else 0.0
    if refusal_expected:
        support = 1.0 - fab_rate
    elif refused:
        support = 0.0
    else:
        need = set(needed) or available
        cover = len(cited & need) / len(need)
        support = round(cover * (1.0 - fab_rate), 4)
    return round(support, 4), fab_rate


def grade_distinction(basis: str | None) -> float:
    """区分层：答案的声明结构规则抽取——BASIS 声明齐全且属合法枚举。

    注：数据集无参考 basis 标签，逐字核验（report 应在引用段落命中）不可判真伪
    （实证 11/40 参考答案为转述），故只判结构有效性；逐字命中作为诊断信号另行
    报告不进分（adapters/README.md §1 区分层原文即「由答案的声明结构规则抽取」）。
    """
    return 1.0 if (basis or "").lower() in _BASIS_VALID else 0.0


# ---------------------------------------------------------------- per-task run

def run_task(
    task: TaskSpec, *, provider: str, model: str | None, seed: int,
    env_digest: str, prompt_cache: dict[str, str],
) -> dict[str, Any]:
    t0 = time.time()
    prompt = prompt_cache[task.id]
    answer_format = task["grader"].get("answer_format", "mcq")

    applicability = {}
    # 层适用性由任务 YAML 声明决定（cfdquery 仅客观层；aeroengqa 四层齐备）
    has_evidence = bool(task["grader"].get("evidence_layer"))
    refusal_expected = bool(task["reference"].get("refusal_expected"))
    has_distinction = bool(task["grader"].get("distinction_layer"))
    n_samples = int(task["grader"].get("robustness_samples", 1))

    applicability["physics"] = ("evidence+refusal" if (has_evidence or refusal_expected)
                                else "N/A")
    applicability["objective"] = "distinction" if has_distinction else "merged_into_requirements"
    applicability["requirements"] = ("free_text_obj" if answer_format == "free_text"
                                     else "mcq_exact")
    applicability["robustness"] = f"samples={n_samples}" if n_samples > 1 else "N/A"

    # --- 模型调用（含采样一致性 robustness，未启用时 1 次） ---
    outs = []
    try:
        for _ in range(max(1, n_samples)):
            outs.append(get_answer(provider, task, prompt, seed=seed, model=model,
                                   max_attempts=int(task["limits"]["attempts"]),
                                   expect=answer_format))
    except ProviderError:
        # provider 明确失败（如 API 未配置）=> 整批终止而非静默 0 分
        raise

    layer_details: dict[str, Any] = {}

    if answer_format == "mcq":
        gate, gate_failures, failure_mode = validity_gate(task, outs[0])
        req_score = grade_objective(task, outs[0]["answer"]) if gate else 0.0
        subscores = {"physics": None, "requirements": req_score,
                     "objective": None, "robustness": 0.0}
    else:
        # ---------- free_text（aeroengqa 型）：gate + 四层 ----------
        parsed = parse_structured(str(outs[0]["answer"]))
        if parsed["refused"] is None:      # ANSWER 行缺失/空 => 缺产物
            gate, gate_failures, failure_mode = 0, [FM_MISSING_OUTPUT], FM_MISSING_OUTPUT
        else:
            gate, gate_failures, failure_mode = 1, [], None

        ref = task["reference"]
        n_ctx = int(ref.get("n_contexts", 1))
        needed = list(ref.get("needed_citations") or [])

        # 1) 客观层（可答题；不可答题 requirements N/A）
        if refusal_expected:
            req_score = None
        elif gate:
            req_score = grade_free_text_objective(
                str(ref["reference_answer"]), parsed["answer_text"],
                float(task["grader"].get("numeric_rel_tol", 0.05)))
        else:
            req_score = 0.0

        # 2) 拒答层 + 3) 证据层 -> physics
        if gate:
            refusal_score = grade_refusal(refusal_expected, parsed["refused"])
            support, fab = grade_evidence(parsed["citations"], n_ctx, needed,
                                          parsed["refused"], refusal_expected)
        else:
            refusal_score, support, fab = 0.0, 0.0, 0.0
        physics = round((refusal_score + support) / 2, 4) if has_evidence or refusal_expected else None

        # 4) 区分层 -> objective
        distinction = grade_distinction(parsed["basis"]) if (gate and has_distinction) else (
            None if not has_distinction else 0.0)

        subscores = {"physics": physics, "requirements": req_score,
                     "objective": distinction, "robustness": 0.0}
        layer_details = {"refused": parsed["refused"], "citations": parsed["citations"],
                         "basis": parsed["basis"], "answer_text": parsed["answer_text"],
                         "refusal_score": refusal_score, "evidence_support": support,
                         "fabrication_rate": fab, "needed": needed}

    # --- 采样一致性（可选 robustness；样本>1 时为答案一致率） ---
    if n_samples > 1 and gate:
        answers = {str(o["answer"]) for o in outs}
        subscores["robustness"] = 1.0 if len(answers) == 1 else 0.0

    weights = {**DEFAULT_WEIGHTS, **(task["scoring"].get("weights") or {})}

    score = aggregate_score(
        {k: (v if v is not None else 0.0) for k, v in subscores.items()},
        weights, gate)

    artifacts = {"answer": json.dumps(str(outs[0]["answer"]), ensure_ascii=False),
                 "model_meta": json.dumps(outs[0]["meta"], ensure_ascii=False)}
    if layer_details:
        artifacts["layer_details"] = json.dumps(layer_details, ensure_ascii=False)

    return build_result(
        task=task, adapter=ADAPTER,
        validity_gate=gate, gate_failures=gate_failures,
        subscores=subscores, score=score,
        artifacts=artifacts,
        timings={"agent_s": time.time() - t0, "setup_s": 0.0, "grade_s": 0.0},
        env_digest=env_digest,
        logs=[f"answer={str(outs[0]['answer'])[:120]!r} attempts={outs[0]['attempts']}"],
        failure_mode=failure_mode,
        applicability=applicability,
    )


# ---------------------------------------------------------------- summary

def write_summary(out_dir: Path, results: list[dict[str, Any]],
                  provider: str, model_label: str, seed: int) -> Path:
    dist = gate_distribution(results)
    scored = [r for r in results if r.get("failure_mode") not in common.VOIDED_FAILURE_MODES]
    layered = [r for r in scored if "layer_details" in r["artifacts"]]
    lines = []
    a = lines.append
    a(f"# qa_grounded 结果汇总（provider={provider}, model={model_label}, seed={seed}）")
    a("")
    a("## ValidityGate 分布（先看 gate，再看子分）")
    a("")
    a(f"- 任务总数: {dist['n_tasks']}")
    a(f"- gate 通过: {dist['gate_passed']}")
    a(f"- gate 失败: {dist['gate_failed']}（直接 0 分）")
    a(f"- 作废（不计分）: {dist['voided']}")
    a(f"- gate 失败原因分布: {dist['gate_failure_reasons'] or '无'}")
    a("")

    if layered:
        # ---------- free_text 多层报告（aeroengqa 型） ----------
        import json as _json
        det = [(r, _json.loads(r["artifacts"]["layer_details"])) for r in layered]
        ans_tasks = [(r, d) for r, d in det if r["subscores"]["requirements"] is not None]
        unans_tasks = [(r, d) for r, d in det if r["subscores"]["requirements"] is None]
        a("## 拒答层（refusal）")
        a("")
        if unans_tasks:
            ok_u = sum(1 for _, d in unans_tasks if d["refusal_score"] == 1.0)
            a(f"- 应拒答 {len(unans_tasks)} 题: 正确拒答 {ok_u}"
              f"（拒答正确率 {ok_u/len(unans_tasks):.4f}）")
        if ans_tasks:
            bad_ref = sum(1 for _, d in ans_tasks if d["refused"])
            a(f"- 应回答 {len(ans_tasks)} 题: 误拒答 {bad_ref}"
              f"（误拒率 {bad_ref/len(ans_tasks):.4f}）")
        a("")
        a("## 证据层（evidence support / fabrication）")
        a("")
        sup = [d["evidence_support"] for _, d in det]
        fabs = [d["fabrication_rate"] for _, d in det]
        n_fab = sum(1 for f in fabs if f > 0)
        a(f"- evidence_support 均值: {sum(sup)/max(1,len(sup)):.4f}")
        a(f"- 捏造引用题数: {n_fab}/{len(det)}（fabrication_rate>0）")
        a("")
        a("## 客观层（requirements，仅应回答题）")
        a("")
        if ans_tasks:
            reqs = [r["subscores"]["requirements"] for r, _ in ans_tasks]
            full = sum(1 for x in reqs if x == 1.0)
            a(f"- 满分 {full}/{len(reqs)}；含部分分的均值 {sum(reqs)/len(reqs):.4f}"
              "（归一化精确/数值容差=1，其余 token F1 部分分）")
        else:
            a("- 全部为应拒答题，客观层 N/A")
        a("")
        a("## 区分层（distinction：BASIS 结构声明）")
        a("")
        dists = [r["subscores"]["objective"] for r, _ in det
                 if r["subscores"]["objective"] is not None]
        a(f"- 合法声明率: {sum(dists)/max(1,len(dists)):.4f}（{len(dists)} 题）")
        a("- 口径：BASIS ∈ report/computed/inferred；数据集无参考 basis 标签，"
          "逐字核验仅作诊断不进分（见任务 YAML grader 注释）")
        a("")
        a("## 每题明细")
        a("")
        a("| task | gate | refused | cite | support | fab | req | dist | score |")
        a("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for r, d in det:
            req = r["subscores"]["requirements"]
            req_s = "N/A" if req is None else f"{req}"
            ds = r["subscores"]["objective"]
            a(f"| {r['task_id']} | {r['validity_gate']} | {d['refused']} "
              f"| {d['citations']} | {d['evidence_support']} | {d['fabrication_rate']} "
              f"| {req_s} | {ds} | {r['score']} |")
    else:
        # ---------- MCQ 报告（cfdquery 型） ----------
        n_correct = sum(1 for r in scored if r["subscores"]["requirements"] == 1.0)
        a("## 客观层（requirements）")
        a("")
        a(f"- 正确: {n_correct}/{len(scored)}"
          f"（accuracy = {n_correct / max(1, len(scored)):.4f}，分母=计分任务数）")
        a("- 子分适用性: physics=N/A（无证据/拒答层）；objective=N/A（并入 requirements）；"
          "robustness=采样一致性（本配置样本=1，不适用）")
        a("- 权重（任务 YAML 覆写）: score = gate × 1.0×requirements")
        a("")
        a("## 每题明细")
        a("")
        a("| task | gate | answer_correct | score |")
        a("| --- | --- | --- | --- |")
        for r in results:
            ok = r["subscores"]["requirements"] == 1.0
            a(f"| {r['task_id']} | {r['validity_gate']} | {int(ok)} | {r['score']} |")
    p = out_dir / "summary.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="qa_grounded adapter runner")
    ap.add_argument("--tasks", required=True, help="任务 YAML 目录")
    ap.add_argument("--out", required=True, help="结果输出目录 results/<registry_id>/<date>")
    ap.add_argument("--provider", default="stub",
                    choices=["stub", "oracle", "openai_compat", "glm", "minimax"])
    ap.add_argument("--model", default=None,
                    help="覆写 provider 预设模型名（缺省用 PROVIDER_PRESETS 默认）")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    tasks_dir = Path(args.tasks)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(tasks_dir)
    registry_ids = {t["registry_id"] for t in tasks}
    if len(registry_ids) > 1:
        raise SystemExit(f"一次运行只允许一个 registry_id，发现 {registry_ids}")
    registry_id = registry_ids.pop()

    # 资产校验（assets_revision 锁定）：每个任务的 input.assets 逐个 sha256 核对
    asset_hashes: dict[str, str] = {}
    asset_paths: list[Path] = []
    for t in tasks:
        for a in t.get("input", {}).get("assets", []) or []:
            p = Path(a["path"])
            if not p.is_absolute():
                p = (tasks_dir.parent.parent / p).resolve()
            common.verify_asset(p, a["digest"], f"{t.id}:{a['path']}")
            asset_hashes[a["path"]] = a["digest"]
            asset_paths.append(p)

    env_digest = environment_digest(extra_paths=asset_paths)

    # 题面 prompt（题面文件由 gen_tasks 生成并锁定摘要，此处读回）
    # newline=""：忠实读回上游数据中的真实 CR/LF，禁止 universal-newline 翻译
    prompt_cache = {}
    for t in tasks:
        pf = Path(t["input"]["prompt_file"])
        if not pf.is_absolute():
            pf = (tasks_dir.parent.parent / pf).resolve()
        with open(pf, encoding="utf-8", newline="") as f:
            prompt_cache[t.id] = f.read()

    model_label = args.model or PROVIDER_PRESETS.get(args.provider, {}).get(
        "model_default", "n/a")

    rerun = (f"cd {common.BENCH_ROOT} && python3 -m runners.qa_grounded "
             f"--tasks {Path(args.tasks).as_posix()} --out {Path(args.out).as_posix()} "
             f"--provider {args.provider}"
             + (f" --model {args.model}" if args.model else "")
             + f" --seed {args.seed}")

    results = []
    crash = 0
    for t in tasks:
        try:
            r = run_task(t, provider=args.provider, model=args.model,
                         seed=args.seed, env_digest=env_digest,
                         prompt_cache=prompt_cache)
        except ProviderError as e:
            raise SystemExit(f"[终止] provider 失败: {e}")
        except Exception as e:  # noqa: BLE001 — crash 失败模式需捕获并单题作废
            crash += 1
            r = build_result(
                task=t, adapter=ADAPTER, validity_gate=0,
                gate_failures=[common.FM_CRASH],
                subscores={"physics": None, "requirements": None,
                          "objective": None, "robustness": None},
                score=0.0, artifacts={}, timings={"agent_s": 0.0, "setup_s": 0.0, "grade_s": 0.0},
                env_digest=env_digest, logs=[f"runner exception: {e!r}"],
                failure_mode=common.FM_CRASH)
        results.append(r)
        (out_dir / f"result_{t.id}.json").write_text(
            json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    mf = write_run_manifest(
        out_dir, registry_id=registry_id, adapter=ADAPTER,
        provider=args.provider, seed=args.seed, tasks_dir=tasks_dir,
        env_digest=env_digest, assets=asset_hashes, rerun_command=rerun,
        extra={"crash_tasks": crash, "model": model_label})
    sm = write_summary(out_dir, results, args.provider, model_label, args.seed)

    dist = gate_distribution(results)
    print(f"[done] {dist['n_tasks']} tasks | gate pass {dist['gate_passed']} "
          f"| fail {dist['gate_failed']} | voided {dist['voided']}")
    print(f"       results -> {out_dir}")
    print(f"       manifest -> {mf}")
    print(f"       summary -> {sm}")
    print(f"       rerun: {rerun}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
