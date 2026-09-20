"""gen_tasks_foambasic.py — 从镜像 FoamBench_basic.json 生成任务 YAML + 题面 + oracle 脚本。

生成物（幂等，--check 校验）：
  tasks/cfdllm.foam_basic/foam_<fam>_<var>.yaml
  tasks/cfdllm.foam_basic/foam_<fam>_<var>.md     题面（usr_requirement + 输出契约）
  data/cfdllm/foam_basic/oracle_scripts/...py     GT 文件逐字写出器（判分器自检）

任务口径：GT 批量预计算（gt_runs_status.json）ok 的任务才生成；失败任务如实排除。

用法：.venv/bin/python -m runners.gen_tasks_foambasic [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

from .common import sha256_file

BENCH = Path(__file__).resolve().parent.parent
DATA = BENCH / "data/cfdllm/foam_basic"
TASKS_DIR = BENCH / "tasks/cfdllm.foam_basic"
ORACLE_DIR = DATA / "oracle_scripts"
ASSETS_REVISION = "foambasic@3b46d30+kaggle_v1+gt_runs_2026-08-19"

_WEIGHTS = {"physics": 0.6, "requirements": 0.4, "objective": 0.0, "robustness": 0.0}

_PROMPT_TMPL = """{usr_requirement}

## Output contract

Write a single Python 3 script that creates the complete OpenFOAM case in the current working directory. The script must create (with os.makedirs / open().write(), plain string contents):

- system/blockMeshDict, system/controlDict, system/fvSchemes, system/fvSolution
- constant/ ... (all dictionaries the solver needs, e.g. momentumTransport, physicalProperties, turbulenceProperties, etc.)
- 0/ ... (initial fields the solver needs)
- Allrun  (shell script: source $WM_PROJECT_DIR/bin/tools/RunFunctions, then runApplication blockMesh and runApplication <solver>)

Requirements:
- OpenFOAM version 10 (Foundation) dict syntax.
- endTime / writeInterval chosen so the run finishes quickly (a few seconds to ~1 min) and writes at least one time directory.
- The solver name in controlDict (application) must match the Allrun invocation.
- Use only os, math and built-ins in the script. Do not execute OpenFOAM commands from the script — only write files.

Respond with a single ```python code block and nothing else.
"""


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def build_prompt(usr_req: str) -> str:
    return _PROMPT_TMPL.format(usr_requirement=usr_req.strip()) + "\n"


def build_oracle_script(files: dict[str, str]) -> str:
    """GT 文件逐字写出器：repr 转义内容，运行时写回。"""
    entries = {k: v for k, v in files.items() if k != "usr_requirement"}
    lines = ["# oracle: GT 文件逐字写出（FoamBench_basic.json，repr 转义）",
             "import os", "", "FILES = {"]
    for path, content in sorted(entries.items()):
        lines.append(f"    {path!r}: {content!r},")
    lines.append("}")
    lines.append("""
for rel, content in FILES.items():
    p = os.path.join(os.curdir, rel)
    os.makedirs(os.path.dirname(p) or os.curdir, exist_ok=True)
    with open(p, 'w', newline='') as f:
        f.write(content)
import os as _os
_os.chmod('Allrun', 0o755)
""")
    return "\n".join(lines)


def _read_no_translate(p: Path) -> str:
    if not p.exists():
        return ""
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    data = json.loads((DATA / "FoamBench_basic.json").read_text())
    status = json.loads((DATA / "gt_runs_status.json").read_text())
    digests = {"data/cfdllm/foam_basic/FoamBench_basic.json":
               sha256_file(DATA / "FoamBench_basic.json"),
               "data/cfdllm/foam_basic/gt_runs_status.json":
               sha256_file(DATA / "gt_runs_status.json")}

    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    ORACLE_DIR.mkdir(parents=True, exist_ok=True)
    n, skipped, drift = 0, [], []
    for key in sorted(data):
        fam, var = key.split("/")
        rel = f"{fam}/{var}"
        st = status.get(rel, {})
        if not st.get("ok"):
            skipped.append((rel, st.get("err", "gt_not_ok")[:60]))
            continue
        files = data[key]
        tid = f"foam_{_slug(fam)}_{var}"
        prompt = build_prompt(files["usr_requirement"])
        prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()

        oracle_rel = f"data/cfdllm/foam_basic/oracle_scripts/{tid}.py"
        oracle_code = build_oracle_script(files)

        spec = {
            "id": tid,
            "registry_id": "cfdllm.foam_basic",
            "domain": "cfd",
            "task_type": "simulation_agent",
            "model_profile": "plain_llm",
            "assets_revision": ASSETS_REVISION,
            "environment_digest": "computed-at-runtime",
            "hidden": False,
            "allowed_tools": ["python", "openfoam"],
            "input": {
                "prompt_file": f"tasks/cfdllm.foam_basic/{tid}.md",
                "prompt_sha256": prompt_sha,
                "assets": [{"path": p, "digest": d} for p, d in digests.items()],
            },
            "output_contract": ["case_directory"],
            "reference": {
                "source": "FoamBench_basic.json GT 文件（BSD-3）+ gt_runs 预计算参考场",
                "revision": ASSETS_REVISION,
                "family": fam,
                "variant": int(var),
                "gt_case_dir": f"data/cfdllm/foam_basic/gt_cases/{fam}/{var}",
                "gt_run_dir": f"data/cfdllm/foam_basic/gt_runs/{fam}/{var}",
                "gt_last_time": st.get("last_time"),
                "uncertainty_note": "参考场为 GT 算例 docker v10 单次确定性运行（NMSE 语义）",
            },
            "grader": {
                "answer_format": "code",
                "exec_kind": "foam_basic",
                "validity_gate": True,
                "solver_backend": "openfoam10-docker",
                "convergence_check": "official_log_end_marker",
                "field_compare": "official_nmse_pyvista_last_time",
                "nmse_thresholds": {"full": 0.1, "half": 0.3},
                "oracle_source": oracle_rel,
                "sandbox": {"banned": "network/process/ctypes", "isolated_interpreter": True},
            },
            "scoring": {
                "weights": _WEIGHTS,
                "note": "physics=NMSE 阈值分（官方映射）；requirements=结构契约；"
                        "objective/robustness=N/A（基础题无目标函数/扰动）权重 0",
            },
            "limits": {"cpu": 4, "memory_gb": 8, "wall_clock_s": 900, "attempts": 3},
            "license_provenance": {
                "source": "NREL-Theseus/cfdllmbench + Kaggle nithinsekhar/foambench",
                "license": "BSD-3-Clause",
                "status": "confirmed-repo",
                "revision": ASSETS_REVISION,
                "mirror_allowed": True,
            },
        }
        want = yaml.safe_dump(spec, sort_keys=False, allow_unicode=True)
        ypath = TASKS_DIR / f"{tid}.yaml"
        ppath = TASKS_DIR / f"{tid}.md"
        opath = ORACLE_DIR / f"{tid}.py"
        if args.check:
            if (_read_no_translate(ypath) != want
                    or _read_no_translate(ppath) != prompt
                    or _read_no_translate(opath) != oracle_code):
                drift.append(tid)
        else:
            ypath.write_text(want, encoding="utf-8")
            ppath.write_text(prompt, encoding="utf-8")
            opath.write_text(oracle_code, encoding="utf-8")
        n += 1
    if args.check:
        if drift:
            print(f"[check] 不一致: {drift}")
            return 1
        print(f"[check] {n} 个任务与镜像一致（排除 {len(skipped)}）")
        return 0
    print(f"[gen] {n} tasks -> {TASKS_DIR}（GT 不可用排除 {len(skipped)}："
          f"{[s[0] for s in skipped][:8]}{'…' if len(skipped) > 8 else ''}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
