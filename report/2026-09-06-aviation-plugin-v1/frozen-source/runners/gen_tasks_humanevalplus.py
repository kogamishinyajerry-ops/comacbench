"""gen_tasks_humanevalplus.py — 从官方 HumanEval+ NoExtreme release 生成任务 YAML + 题面 + oracle。

数据源（2026-08-21 两次裁定）：
  1) 换源：官方 GitHub release evalplus/humanevalplus_release v0.1.10 NoExtreme 变体
     （md5 413980104ee0339c147ac09653cee3db）——HF evalplus/humanevalplus 卡片版本存在
     转换缺陷（HumanEval/32 断言行损坏，证据见 PROVENANCE.md）；
  2) NoExtreme 变体：全量版的极端输入题（如 /15 string_sequence(1e6) 输出 6.9M 字符、
     /83 大整数）使冻结 gold 与任务 YAML 膨胀至 ~300MB，且官方本就提供 NoExtreme 变体
     专治此类病态输入——采用之（口径如实标注为 HumanEval+ NoExtreme）。

判分语义（官方 EvalPlus 复刻，活体 GT——不冻结期望输出）：
  1) release `test`（原版 check 断言）AST 拆分逐条 case；
  2) base_input + plus_input 全量输入：canonical（可信侧）现场执行计算期望，
     候选输出与 GT 双侧 _nb 归一（tuple/set 打标记保类型，numpy→内置）后比对：
     相等通过；不等且数值型则 np.allclose(rtol=1e-7, atol=官方逐题 atol)。
  活体 GT 与官方运行时比对同构，且天然规避巨输出存储问题（源码仅数百字节）。

生成物（幂等，--check 校验）：
  tasks/humaneval.python_plus/humaneval_plus_<NNN>.yaml/.md
  data/humaneval/python_plus/oracle/humaneval_plus_<NNN>.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

from .common import sha256_file
from .gen_tasks_humaneval import PROMPT_SUFFIX, split_tests

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/humaneval/python_plus"
ORIG = BENCH / "data/humaneval/python"
TASKS_DIR = BENCH / "tasks/humaneval.python_plus"
ORACLE_DIR = DATA / "oracle"
ASSETS_REVISION = "humanevalplus@release_v0.1.10-noextreme_20260821"

# gold/判分共用归一函数源（tuple/set 打标记保类型——JSON 不可用时双侧同款归一即可）
_NORM_SRC = (
    "def _nb(x):\n"
    "    import numpy as _np\n"
    "    if isinstance(x,(bool,int,float,str,type(None))): return x\n"
    "    if isinstance(x,_np.bool_): return bool(x)\n"
    "    if isinstance(x,_np.integer): return int(x)\n"
    "    if isinstance(x,_np.floating): return float(x)\n"
    "    if isinstance(x,_np.ndarray): return [_nb(v) for v in x.tolist()]\n"
    "    if isinstance(x,tuple): return {'__T__': [_nb(v) for v in x]}\n"
    "    if isinstance(x,list): return [_nb(v) for v in x]\n"
    "    if isinstance(x,(set,frozenset)): return {'__S__': sorted((_nb(v) for v in x),key=repr)}\n"
    "    if isinstance(x,dict): return {str(k):_nb(v) for k,v in x.items()}\n"
    "    return repr(x)\n"
)


def _lit(x) -> str:
    """安全字面量 repr：inf/nan 浮点 -> float('inf') 等构造式（裸 inf 是 NameError）。"""
    if isinstance(x, float):
        if x != x:
            return "float('nan')"
        if x == float("inf"):
            return "float('inf')"
        if x == float("-inf"):
            return "float('-inf')"
        return repr(x)
    if isinstance(x, list):
        return "[" + ", ".join(_lit(v) for v in x) + "]"
    return repr(x)


def build_plus_batch_case(entry_point: str, canonical_src: str,
                          inputs: list, atol) -> str:
    """活体 GT 批量比对 case：canonical 现场执行 -> 双侧 _nb 归一比对。"""
    return (
        _NORM_SRC + "\n"
        f"_gt_ns = {{}}\n"
        f"exec({canonical_src!r}, _gt_ns)\n"
        f"_gt = _gt_ns[{entry_point!r}]\n"
        f"_inputs = {_lit(inputs)}\n"
        f"_atol = {atol!r}\n"
        f"for _inp in _inputs:\n"
        f"    _exp = _nb(_gt(*_inp))\n"
        f"    _got = _nb({entry_point}(*_inp))\n"
        f"    if not (_got == _exp):\n"
        f"        import numpy as _np\n"
        f"        try:\n"
        f"            assert _np.allclose(_got, _exp, rtol=1e-07, atol=_atol)\n"
        f"        except Exception:\n"
        f"            assert False, f'mismatch on {{_inp!r}}'\n"
    )


def build_prompt_md(official_prompt: str) -> str:
    return official_prompt.rstrip() + "\n" + PROMPT_SUFFIX


def task_yaml(idx: int, spec: dict, cases: list[str], mode: str,
              data_digest: str, orig_digest: str,
              oracle_digest: str, prompt_sha: str) -> dict:
    tid = f"humaneval_plus_{idx:03d}"
    return {
        "id": tid,
        "registry_id": "humaneval.python_plus",
        "domain": "coding",
        "task_type": "code_exec",
        "model_profile": "plain_llm",
        "assets_revision": ASSETS_REVISION,
        "environment_digest": "computed-at-runtime",
        "hidden": False,
        "allowed_tools": ["python"],
        "input": {
            "prompt_file": f"tasks/humaneval.python_plus/{tid}.md",
            "prompt_sha256": prompt_sha,
            "assets": [
                {"path": "data/humaneval/python_plus/HumanEvalPlus-NoExtreme.jsonl",
                 "digest": data_digest},
                {"path": "data/humaneval/python/HumanEval.jsonl",
                 "digest": orig_digest},
                {"path": f"data/humaneval/python_plus/oracle/{tid}.py",
                 "digest": oracle_digest},
            ],
        },
        "output_contract": ["function:" + spec["entry_point"]],
        "reference": {
            "source": "HumanEval+ 官方 release v0.1.10 NoExtreme 变体（Apache-2.0）",
            "revision": ASSETS_REVISION,
            "task_id": spec["task_id"],
            "entry_point": spec["entry_point"],
            "n_test_cases": len(cases),
            "test_note": "原版断言逐条拆分 + base/plus 全量输入活体 GT 比对（官方语义，"
                         "canonical 判分时现场执行，双侧 _nb 归一 tuple/set 保类型）",
            "uncertainty_note": "断言二值判定无比对不确定度；atol 由官方 release 逐题给出",
        },
        "grader": {
            "answer_format": "code",
            "exec_kind": "unit_tests_problem",
            "validity_gate": True,
            "entry_point": spec["entry_point"],
            "tests": cases,
            "test_split_mode": mode,
            "test_imports": [],
            "determinism_runs": 2,
            "sandbox": {"banned": "network/process/ctypes/sys.path",
                        "isolated_interpreter": True},
            "oracle_source": f"data/humaneval/python_plus/oracle/{tid}.py",
        },
        "scoring": {
            "weights": {"physics": 0.5, "requirements": 0.2, "objective": 0.0,
                        "robustness": 0.3},
            "note": "objective=N/A 权重 0；robustness=两次执行确定性；"
                    "pass@1（=physics==1.0）为 HumanEval+ NoExtreme 口径",
        },
        "limits": {"cpu": 4, "memory_gb": 4, "wall_clock_s": 600, "attempts": 3},
        "license_provenance": {
            "source": "evalplus/humanevalplus_release v0.1.10 NoExtreme（GitHub）",
            "license": "Apache-2.0（数据）/ MIT（复用原版 prompt）",
            "status": "confirmed-split",
            "revision": ASSETS_REVISION,
            "mirror_allowed": True,
        },
    }


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if hasattr(sys, "set_int_max_str_digits"):
        sys.set_int_max_str_digits(0)   # repr() 大整数输入题

    rows = [json.loads(l) for l in
            (DATA / "HumanEvalPlus-NoExtreme.jsonl").read_text(encoding="utf-8").splitlines()]
    orig_rows = [json.loads(l) for l in
                 (ORIG / "HumanEval.jsonl").read_text(encoding="utf-8").splitlines()]
    data_digest = sha256_file(DATA / "HumanEvalPlus-NoExtreme.jsonl")
    orig_digest = sha256_file(ORIG / "HumanEval.jsonl")

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    ORACLE_DIR.mkdir(parents=True, exist_ok=True)
    drift, n = [], 0
    for r in rows:
        idx = int(r["task_id"].split("/")[1])
        o = next(x for x in orig_rows if x["task_id"] == r["task_id"])
        base_cases, mode = split_tests(r["test"], r["entry_point"])
        oracle_src = o["prompt"] + r["canonical_solution"] + "\n"
        inputs = list(r["base_input"]) + list(r["plus_input"])
        batch = build_plus_batch_case(r["entry_point"], oracle_src,
                                      inputs, r["atol"])
        cases = base_cases + [batch]
        mode = mode + "+live_gt_batch"
        prompt_md = build_prompt_md(o["prompt"])       # 原版 prompt（含 /115）
        prompt_sha = hashlib.sha256(prompt_md.encode()).hexdigest()
        tid = f"humaneval_plus_{idx:03d}"
        oracle_digest = hashlib.sha256(oracle_src.encode()).hexdigest()
        want = yaml.safe_dump(task_yaml(idx, r, cases, mode, data_digest,
                                        orig_digest, oracle_digest, prompt_sha),
                              sort_keys=False, allow_unicode=True, width=10**9)
        ypath, ppath = TASKS_DIR / f"{tid}.yaml", TASKS_DIR / f"{tid}.md"
        opath = ORACLE_DIR / f"{tid}.py"
        if args.check:
            if (_read_no_translate(ypath) != want
                    or _read_no_translate(ppath) != prompt_md
                    or _read_no_translate(opath) != oracle_src):
                drift.append(tid)
        else:
            ypath.write_text(want, encoding="utf-8")
            ppath.write_text(prompt_md, encoding="utf-8")
            opath.write_text(oracle_src, encoding="utf-8")
        n += 1
    if args.check:
        if drift:
            print(f"[check] 不一致: {drift[:5]}... 共 {len(drift)}")
            return 1
        print(f"[check] {n} 个任务与镜像一致")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR}（活体 GT，无冻结 gold）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
