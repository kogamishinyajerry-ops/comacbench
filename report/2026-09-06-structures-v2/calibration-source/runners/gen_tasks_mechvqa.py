"""gen_tasks_mechvqa.py — 从 MechVQA 公开评测集 jsonl 生成多模态 VQA 任务（YAML + 题面 md）。

生成物（全部可重入：重跑覆盖且结果一致）：
  tasks/mechvqa.public_eval/mechvqa_q###.yaml   180 个任务契约（free_vqa）
  tasks/mechvqa.public_eval/mechvqa_q###.md     180 个题面文件

子集规则（确定性，写死本文件，评测口径与 PROVENANCE.md「任务集派生」一致）：
  - 池：mechvqa_benchmark.jsonl 中 qualityscore==1.0 的全部 1117 行（0-based 原始行号）；
  - 分配：按 (capability × difficulty) 9 格比例分配 180 题，最大余数法
    （余数并列时按格内样本数降序、格名升序定序——保证可复现）；
  - 抽样：每格内对格内原始行号列表用 numpy.random.default_rng(20260821) 独立打乱
    （每格同种子重置，逐格互不影响）后取前 k 个；
  - 编号：180 题按原始行号升序编号 mechvqa_q001..mechvqa_q180。

多模态：每题 1 张工程图（input.assets role=image，sha256 逐图锁定）；
qa_grounded 将其加载为 data URI 传给 VLM provider（glmvl）。stub/oracle 均
支持 grader.answer_format: free_vqa（中文感知 Exact/数值容差/token-F1 判分）。

用法（仓库根）：
  python3 -m runners.gen_tasks_mechvqa            # 生成/校验
  python3 -m runners.gen_tasks_mechvqa --check    # 只校验不写
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA_ROOT = BENCH / "data/mechvqa/public_eval/benchmark_data"
JSONL = DATA_ROOT / "vqa_benchmark/mechvqa_benchmark.jsonl"
TASKS_DIR = BENCH / "tasks/mechvqa.public_eval"
ASSETS_REVISION = "mechvqa@github-HEAD-2026-08-19"   # data/mechvqa/public_eval/PROVENANCE.md
SEED = 20260821
N_TASKS = 180
POOL_SIZE = 1117                                      # qualityscore==1.0 行数（断言防数据漂移）

WEIGHTS_NOTE = (
    "纯客观层单层任务：VQA 自由短答无证据语料/拒答/区分层（physics/objective 标注 N/A），"
    "权重经 YAML 覆写塌缩到 requirements（free_vqa 中文感知 Exact/数值容差/F1，adapter 契约机制）"
)

INSTRUCTION_ZH = "请看图用一两句中文直接作答；不要复述题目，不要给出推理步骤。"
INSTRUCTION_EN = ("Look at the figure and answer directly in one or two sentences "
                  "in English; do not restate the question, and do not give "
                  "reasoning steps.")


# ---------------------------------------------------------------- subset

def largest_remainder(cells: dict[tuple[str, str], int],
                      total: int) -> dict[tuple[str, str], int]:
    """最大余数法比例分配。余数并列时：格内样本数降序 -> 格名升序（确定性）。"""
    n = sum(cells.values())
    quota = {k: total * v / n for k, v in cells.items()}
    alloc = {k: int(q // 1) for k, q in quota.items()}
    rem = total - sum(alloc.values())
    order = sorted(quota, key=lambda k: (-(quota[k] - alloc[k]), -cells[k], k))
    for k in order[:rem]:
        alloc[k] += 1
    return alloc


def select_subset(rows: list[dict]) -> tuple[list[int],
                                             dict[tuple[str, str], list[int]],
                                             dict[tuple[str, str], int]]:
    """-> (选中的 180 个原始行号升序, 各格行号池, 各格分配数)。"""
    good = [i for i, r in enumerate(rows) if r["qualityscore"] == 1.0]
    assert len(good) == POOL_SIZE, f"预期 {POOL_SIZE} 行 qualityscore==1.0，实际 {len(good)}"

    cells: dict[tuple[str, str], list[int]] = {}
    for i in good:
        m = rows[i]["metadata"]
        cells.setdefault((m["capability"], m["difficulty"]), []).append(i)

    alloc = largest_remainder({k: len(v) for k, v in cells.items()}, N_TASKS)
    assert sum(alloc.values()) == N_TASKS

    chosen: list[int] = []
    for cell in sorted(cells):
        idxs = cells[cell]
        k = alloc[cell]
        assert k <= len(idxs)
        # 每格独立同种子打乱（子集规则的字面口径；重跑必然一致）
        perm = np.random.default_rng(SEED).permutation(len(idxs))
        chosen.extend(idxs[j] for j in perm[:k])
    assert len(chosen) == N_TASKS
    chosen.sort()
    return chosen, cells, alloc


# ---------------------------------------------------------------- task files

def build_prompt(q: dict, n: int) -> str:
    question = str(q["messages"][0]["content"])
    zh = q["metadata"]["language"] == "中文"
    instruction = INSTRUCTION_ZH if zh else INSTRUCTION_EN
    lines = [
        f"## MechVQA 图文问答（第 {n}/{N_TASKS} 题）",
        "",
        "附图见任务资产（1 张工程图/装配图）。",
        "",
        "### 问题原文",
        "",
        question,
        "",
        "### 作答要求",
        "",
        instruction,
        "",
    ]
    return "\n".join(lines)


def task_yaml(q: dict, idx: int, n: int, image_rel: str,
              digest: str) -> dict:
    tid = f"mechvqa_q{n:03d}"
    m = q["metadata"]
    return {
        "id": tid,
        "registry_id": "mechvqa.public_eval",
        "domain": "knowledge",
        "task_type": "qa_grounded",
        "model_profile": "multimodal_vlm",       # multimodal_only：纯文本模型不进主分
        "hidden": False,
        "allowed_tools": [],                     # 纯 VQA：无工具白名单
        "assets_revision": ASSETS_REVISION,
        "input": {
            "prompt_file": f"tasks/mechvqa.public_eval/{tid}.md",
            "assets": [
                # path 相对仓库根；runner 自动加载 role=image 资产为 data URI 传 VLM
                {"path": image_rel, "digest": digest, "role": "image"},
            ],
        },
        "output_contract": ["answer"],           # 缺答案字段 = missing_output
        "reference": {
            "source": "MechVQA benchmark_data (Apache-2.0, xiaofengShi/MechVQA)",
            "question_index": idx,               # jsonl 0-based 原始行号
            "reference_answer": str(q["messages"][1]["content"]),
            "capability": m["capability"],
            "difficulty": m["difficulty"],
            "subcategory": m["subcategory"],
            "language": m["language"],
            "qualityscore": q["qualityscore"],
        },
        "grader": {
            "validity_gate": True,
            "answer_format": "free_vqa",         # 中文感知 Exact/数值容差/token-F1
            "objective_layer": "exact_or_numeric_or_f1",
            "numeric_rel_tol": 0.05,
            "evidence_layer": False,             # 无证据语料 -> physics N/A
            "refusal_layer": False,
            "distinction_layer": False,          # 无区分层 -> 并入 requirements
            "robustness_samples": 1,
        },
        "scoring": {
            # 覆写默认权重：不适用的层权重归零（子分仍在 result.json 全报告并标注 N/A）
            "weights": {"physics": 0.0, "requirements": 1.0,
                        "objective": 0.0, "robustness": 0.0},
            "note": WEIGHTS_NOTE,
        },
        "limits": {"cpu": 1, "memory_gb": 2, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "xiaofengShi/MechVQA",
            "license": "Apache-2.0",
            "status": "confirmed-repo",
            "mirror_allowed": True,
            "revision": ASSETS_REVISION,
        },
    }


# ---------------------------------------------------------------- main

def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验已生成文件的一致性")
    args = ap.parse_args()

    rows = [json.loads(line) for line in
            JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1185, f"预期 1185 行，实际 {len(rows)}"

    chosen, cells, alloc = select_subset(rows)

    # 逐行结构核验（选定子集）：2 消息/角色正确/问答非空/恰好 1 图
    for idx in chosen:
        r = rows[idx]
        assert len(r["messages"]) == 2
        assert [m["role"] for m in r["messages"]] == ["user", "assistant"]
        assert str(r["messages"][0]["content"]).strip()
        assert str(r["messages"][1]["content"]).strip()
        assert len(r["images"]) == 1

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    digest_cache: dict[str, str] = {}
    drift = []
    for n, idx in enumerate(chosen, start=1):
        r = rows[idx]
        # jsonl images 字段相对 benchmark_data/；YAML path 相对仓库根（同 cfdquery 口径）
        image_rel = f"data/mechvqa/public_eval/benchmark_data/{r['images'][0]}"
        ipath = BENCH / image_rel
        assert ipath.exists(), f"缺图: {image_rel}"
        if image_rel not in digest_cache:
            digest_cache[image_rel] = sha256_file(ipath)
        tid = f"mechvqa_q{n:03d}"
        ypath = TASKS_DIR / f"{tid}.yaml"
        ppath = TASKS_DIR / f"{tid}.md"
        want_yaml = yaml.safe_dump(task_yaml(r, idx, n, image_rel,
                                             digest_cache[image_rel]),
                                   sort_keys=False, allow_unicode=True)
        want_prompt = build_prompt(r, n)
        if args.check:
            got_y = _read_no_translate(ypath)
            got_p = _read_no_translate(ppath)
            if got_y != want_yaml or got_p != want_prompt:
                drift.append(tid)
        else:
            ypath.write_text(want_yaml, encoding="utf-8")
            ppath.write_text(want_prompt, encoding="utf-8")

    cell_report = "\n".join(
        f"  {cap:<12} {dif:<7} 池 {len(cells[(cap, dif)]):>4} -> 分配 {alloc[(cap, dif)]:>3}"
        for cap, dif in sorted(cells))
    print(f"[{'check' if args.check else 'gen'}] 子集: {POOL_SIZE} 行 qs==1.0 池中"
          f"确定性抽 {N_TASKS} 题（seed={SEED}，按 (capability×difficulty) 最大余数法）")
    print(cell_report)
    if args.check:
        if drift:
            print(f"[check] 与镜像不一致的任务: {drift}（重跑生成器修复）")
            return 1
        print(f"[check] {N_TASKS} 个任务 YAML/题面与镜像一致 (assets {ASSETS_REVISION})")
        return 0
    print(f"[gen] {N_TASKS} tasks -> {TASKS_DIR}")
    print(f"      唯一图片 {len(digest_cache)} 张，逐图 sha256 锁定")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
