"""hidden_runtime.py — 受控隐藏层运行时（2026-08-26，深审 M10 接线首落地）。

机制（scoring/README.md §5 的运行时兑现）：
  - 隐藏任务**不存在于静态任务目录**（tasks/），由 data/<registry_id 路径>/hidden/
    generator.py 在评测时动态物化（判分侧可信代码，同 gold 脚本信任模型）；
  - answers.b64 = 全池冻结答案（base64 JSON：id/prompt_sha256/reference/exact_keys），
    运行时与生成器输出逐一校验——防生成器静默漂移；
  - 抽样：按 run seed 从池中抽 N 题（轮换能力：不同 seed/周期不同子集）；
  - 防泄漏纪律：result 落盘**不含题面文本**（仅 prompt_sha256），summary 只给聚合
    与 hidden-public 分差；题面内容不出现在任何持久化产物；
  - 诚实边界（PROVENANCE 必须声明）：hidden ≠ 对人保密——生成器与 answers 在 git
    内；其价值是「静态题库零暴露 + 可轮换 + 分差可监控」，防的是语料/报告级泄漏
    与记忆，不是防阅仓者。

adapter 支持：qa_grounded（--hidden N）首发；simulation_agent/design_artifact 族
接线为 backlog（生成器产出需适配各自 TaskSpec 契约）。
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from .common import TaskSpec

HIDDEN_DIR = "hidden"          # data/<bench path>/hidden/
_POOL_ENTRY = "pool"           # 生成器返回 dict: {"pool": [task dicts], "rev": str}


def hidden_data_dir(assets_root: Path, registry_id: str) -> Path:
    """registry_id 点号→斜杠 = 数据目录约定（engtable.office_basic→data/engtable/office_basic）。"""
    return assets_root / "data" / registry_id.replace(".", "/")


def load_hidden_pool(assets_root: Path, registry_id: str) -> tuple[list[TaskSpec], dict[str, str], str]:
    """加载全隐藏池 -> (TaskSpec 列表, prompt 文本缓存, 池版本)。

    TaskSpec 以内存构造（yaml_path 用 hidden:<id> 占位）；prompt 直接进缓存，
    不落盘。answers.b64 一致性校验失败即抛（fail-fast，判分侧零容忍）。
    """
    d = hidden_data_dir(assets_root, registry_id) / HIDDEN_DIR
    gen_py = d / "generator.py"
    ans_b64 = d / "answers.b64"
    if not gen_py.exists() or not ans_b64.exists():
        raise SystemExit(f"[hidden] {registry_id} 无 {gen_py}/{ans_b64}（hidden_dynamic 声明需配套交付）")
    spec = importlib.util.spec_from_file_location(f"hidden_gen_{registry_id.replace('.', '_')}", gen_py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = mod.gen()
    pool = out[_POOL_ENTRY] if isinstance(out, dict) and _POOL_ENTRY in out else out
    rev = str(out.get("rev", "n/a")) if isinstance(out, dict) else "n/a"

    frozen = {r["id"]: r for r in json.loads(base64.b64decode(ans_b64.read_text()))}
    if len(frozen) != len(pool):
        raise SystemExit(f"[hidden] 池规模漂移：generator {len(pool)} vs answers.b64 {len(frozen)}")

    tasks, prompts = [], {}
    for item in pool:
        fid = item["id"]
        fz = frozen.get(fid)
        if fz is None:
            raise SystemExit(f"[hidden] {fid}: answers.b64 无此条")
        psha = hashlib.sha256(item["prompt"].encode("utf-8")).hexdigest()
        if psha != fz["prompt_sha256"]:
            raise SystemExit(f"[hidden] {fid}: prompt sha 与 answers.b64 不一致（生成器漂移）")
        if item["reference_json"] != fz["reference_json"] or \
                list(item.get("exact_keys") or []) != list(fz.get("exact_keys") or []):
            raise SystemExit(f"[hidden] {fid}: reference/exact_keys 与 answers.b64 不一致")
        spec_dict = {
            "id": fid,
            "registry_id": registry_id,
            "domain": item.get("domain", "airworthiness"),
            "task_type": "qa_grounded",
            "model_profile": "plain_llm",
            "assets_revision": item.get("rev", rev),
            "environment_digest": "computed-at-runtime",
            "hidden": True,
            "allowed_tools": [],
            "input": {"prompt_file": f"hidden:{fid}",
                      "prompt_sha256": psha, "assets": []},
            "output_contract": ["json"],
            "reference": {"source": "hidden pool（动态物化，不落盘）",
                          "reference_json": item["reference_json"],
                          "rel_tol": item.get("rel_tol", 0.02)},
            "grader": {"answer_format": "json_extract",
                       "validity_gate": True,
                       "numeric_rel_tol": item.get("rel_tol", 0.02),
                       "exact_keys": item.get("exact_keys") or [],
                       "sandbox": {"banned": "shell/network/process",
                                   "isolated_interpreter": False}},
            "scoring": item.get("scoring") or {"weights": {
                "requirements": 1.0, "physics": 0.0, "objective": 0.0, "robustness": 0.0}},
            "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 180, "attempts": 3},
            "license_provenance": {"source": "自建 hidden 池（同公开族协议）",
                                   "license": "self-built",
                                   "status": "confirmed-selfbuilt",
                                   "mirror_allowed": True,
                                   "revision": rev},
        }
        tasks.append(TaskSpec(spec_dict, Path(f"{fid}.yaml")))
        prompts[fid] = item["prompt"]
    return tasks, prompts, rev


def strip_prompt_for_record(result: dict[str, Any]) -> dict[str, Any]:
    """防泄漏：hidden 结果落盘前抹除题面文本与答案值（保分数/字段名/ok 标志）。

    - artifacts.answer/raw/code/prompt 全删（oracle 答案=reference，同样不留）；
    - layer_details.fields 仅保 {field, ok, exact}——got/ref 值不留（隐藏组调试
      粒度降级为聚合，是受控隐藏层的代价，PROVENANCE 声明）；
    - raw_tail 同删。
    """
    art = result.get("artifacts", {})
    for k in ("code", "raw", "prompt", "answer"):
        art.pop(k, None)
    ld = art.get("layer_details")
    if isinstance(ld, str):
        try:
            d = json.loads(ld)
            d.pop("raw_tail", None)
            if isinstance(d.get("fields"), list):
                d["fields"] = [{"field": f.get("field"), "ok": f.get("ok"),
                                "exact": f.get("exact")}
                               for f in d["fields"]]
            art["layer_details"] = json.dumps(d, ensure_ascii=False)
        except Exception:  # noqa: BLE001
            art.pop("layer_details", None)
    # logs 含 provider meta 的 answer 回显（attempts 行）——同样抹除
    if isinstance(result.get("logs"), list):
        result["logs"] = [ln for ln in result["logs"]
                          if not ln.startswith("answer=")]
    result["hidden"] = True
    return result


def hidden_public_gap(hidden_results: list[dict], public_dir: Path) -> dict[str, Any] | None:
    """hidden-public 分差（scoring §5 承诺）：同 provider 公开目录存在时计算。

    返回 {overall: (h, p, gap), by_family: {...}}；公开目录缺失返回 None。
    """
    if not public_dir.exists():
        return None
    pub = [json.loads(f.read_text()) for f in sorted(public_dir.glob("result_*.json"))]
    if not pub:
        return None

    def fam(tid: str) -> str:
        return tid.rsplit("_", 1)[0] if "_" in tid else tid

    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else None

    hf = {}
    for r in hidden_results:
        hf.setdefault(fam(r["task_id"]), []).append(r["score"])
    pf = {}
    for r in pub:
        pf.setdefault(fam(r["task_id"]), []).append(r["score"])
    by_family = {}
    for k in sorted(set(hf) | set(pf)):
        h, p = mean(hf.get(k, [])), mean(pf.get(k, []))
        by_family[k] = {"hidden": h, "public": p,
                        "gap": round(h - p, 4) if (h is not None and p is not None) else None}
    h_all, p_all = mean([r["score"] for r in hidden_results]), mean([r["score"] for r in pub])
    return {"overall": {"hidden": h_all, "public": p_all,
                        "gap": round(h_all - p_all, 4) if (h_all is not None and p_all is not None) else None},
            "by_family": by_family,
            "public_dir": str(public_dir)}
