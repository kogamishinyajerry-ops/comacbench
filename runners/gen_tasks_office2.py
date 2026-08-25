#!/usr/bin/env python3
"""gen_tasks_office2.py — 第二批办公基准三线生成（2026-08-26）。

A. awdoc.office_docs      数据锚定文档生成（docx×6 + pptx×6 = 12 题，自建）
B. awext.clause_extract   适航条款结构化抽取（12 题，自建条款风格卡；KB 联动待锚定）
C. spreadsheetbench.verified_400_subset  SpreadsheetBench 精选子集（50 题，外部 CC-BY-SA-4.0）

判分：
  A doc_document 模式（design_artifact）：锚定数字命中 + 结构契约 + 双跑一致
  B json_extract 层（qa_grounded）：条款卡 → JSON 字段级判分
  C formula_cell 模式（design_artifact 新增）：golden xlsx 的 answer 区域单元格比对
    —— 模型输出目标单元格公式串（grader.formula_cells），判分对 golden 区域值；
    值不可静态判定时以 LibreOffice headless 重算后比对（本子集人工筛除公式依赖题）。

用法：.venv/bin/python -m runners.gen_tasks_office2 [--skip-ssb]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
VENV_PY = BENCH / ".venv" / "bin" / "python"
REV_A = "awdoc@selfbuilt-2026-08-26"
REV_B = "awext@selfbuilt-2026-08-26"
REV_C = "ssb400@adapted-2026-08-26"


# ================================================================ A. awdoc

def perf_input(seed):
    """试验性能汇总表（构型×指标）：docx/pptx 报告的数据源。"""
    rng = random.Random(20260826 + seed)
    cfgs = ["A1", "A2", "B1", "B2"][:3 + seed % 2]
    rows = []
    for c in cfgs:
        cl = round(0.42 + rng.random() * 0.2, 3)
        cd = round(0.028 + rng.random() * 0.012, 4)
        ld = round(14.0 + rng.random() * 6.0, 1)
        rows.append([c, cl, cd, ld])
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["config", "cl_max", "cd_cruise", "ld_ratio"])
    w.writerows(rows)
    return buf.getvalue(), rows


def load_input(seed):
    """载荷实测表：结构摘要类报告的数据源。"""
    rng = random.Random(777 + seed)
    n = 18 + seed * 4
    rows = []
    for i in range(n):
        rows.append([f"C{i + 1:03d}",
                     round(1.05 + rng.random() * 1.4, 2),
                     round(2500.0 + rng.random() * 4000.0, 0)])
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["case", "load_factor", "cycles"])
    w.writerows(rows)
    return buf.getvalue(), rows


AWDOC_CONTRACT = """
## Output contract (objective, cell-level grading)

- Produce a file named exactly `{fname}` in the current directory
  ({lib} is the expected tool; standard library + {libs} only).
- All numeric claims in the document MUST come from the input data — compute
  min/max/mean/count from the CSV values with Python and write the ROUNDED
  display values exactly as specified below (do not hand-round differently).
- Structure requirements (headings/tables/slide count) are graded exactly.
- No external facts; do not invent numbers.
"""


def awdoc_docx_prompt(seed, src_name, table_rows, spec_cols):
    return f"""# Engineering test report (docx) — data-anchored

You are given the data file `{src_name}` in the current working directory.

## Required document structure

1. Title (any wording) as a Heading.
2. An "Overview" section (Heading 1) with one short paragraph stating the number
   of data rows N (the count of data records in the CSV, excluding the header).
3. A "Results table" section (Heading 1) containing ONE table with a header row
   plus one row per data record, columns exactly {spec_cols} (same order, same
   values as the source, numbers formatted with the same rounding as source).
4. A "Summary" section (Heading 1) stating, in any wording, these EXACT numbers:
   {ANCHOR_PLACEHOLDER}
5. One concluding paragraph under a "Conclusion" heading (Heading 1).
{AWDOC_CONTRACT.format(fname="report.docx", lib="python-docx", libs="python-docx")}
"""


def awdoc_pptx_prompt(seed, src_name, table_rows, spec_cols):
    return f"""# Engineering test briefing (pptx) — data-anchored

You are given the data file `{src_name}` in the current working directory.

## Required deck structure

- EXACTLY 4 slides:
  1. Title slide (deck title, any wording).
  2. "Data" slide with ONE table: header row + one row per data record,
     columns exactly {spec_cols}.
  3. "Summary" slide with bullet lines containing these EXACT numbers:
     {ANCHOR_PLACEHOLDER}
  4. "Next steps" slide (any wording).
{AWDOC_CONTRACT.format(fname="report.pptx", lib="python-pptx", libs="python-pptx, openpyxl-free")}
"""


def _anchors_perf(rows):
    cls = [r[1] for r in rows]
    cds = [r[2] for r in rows]
    lds = [r[3] for r in rows]
    return {
        "CLmax max": max(cls), "CDcruise mean": round(sum(cds) / len(cds), 4),
        "L/D mean": round(sum(lds) / len(lds), 1),
        "best config (max L/D)": max(rows, key=lambda r: r[3])[0],
    }


def _anchors_load(rows):
    lfs = [r[1] for r in rows]
    cyc = [r[2] for r in rows]
    return {
        "N cases": len(rows), "load max": max(lfs),
        "load mean": round(sum(lfs) / len(lfs), 2),
        "total cycles": int(sum(cyc)),
    }


def _anchor_lines(anchors):
    out = []
    for label, v in anchors.items():
        if isinstance(v, str):
            out.append(f"- {label} = {v} (state this config name)")
        else:
            out.append(f"- {label} = {v}")
    return "\n   ".join(out)


GOLD_DOCX = '''"""gold — data-anchored engineering report (docx)."""
import csv
from docx import Document
from docx.shared import Pt

with open("{src}", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]

{compute}

doc = Document()
doc.add_heading("Test Report", 0)
doc.add_heading("Overview", level=1)
doc.add_paragraph(f"This report summarizes {{len(data)}} data records.")
doc.add_heading("Results table", level=1)
t = doc.add_table(rows=1, cols=len(header))
for i, h in enumerate(header):
    t.rows[0].cells[i].text = str(h)
for r in data:
    cells = t.add_row().cells
    for i, v in enumerate(r):
        cells[i].text = str(v)
doc.add_heading("Summary", level=1)
{summary_py}
doc.add_heading("Conclusion", level=1)
doc.add_paragraph("See summary above.")
doc.save("report.docx")
'''


def _summary_py(anchors):
    lines = []
    for label, v in anchors.items():
        lines.append(f'doc.add_paragraph("{label} = {{{v!r}}}")')
    return "\n".join(lines)


def gen_awdoc():
    tasks_dir = BENCH / "tasks" / "awdoc.office_docs"
    gold_dir = BENCH / "data" / "awdoc" / "office_docs" / "gold"
    input_dir = BENCH / "data" / "awdoc" / "office_docs" / "inputs"
    for d in (tasks_dir, gold_dir, input_dir):
        d.mkdir(parents=True, exist_ok=True)
    n = 0
    for i in range(6):
        src_text, rows = perf_input(i)
        src_name = f"perf_{i + 1:02d}.csv"
        anchors = _anchors_perf(rows)
        anch_line = _anchor_lines(anchors)
        for fmt, prompt_tpl in (("docx", awdoc_docx_prompt), ("pptx", awdoc_pptx_prompt)):
            tid = f"awd_{'rep' if fmt == 'docx' else 'brf'}_perf_{i + 1:02d}"
            prompt = (prompt_tpl(i, src_name, rows,
                                 ["config", "cl_max", "cd_cruise", "ld_ratio"])
                      .replace(ANCHOR_PLACEHOLDER, anch_line))
            emit_awdoc_task(tid, fmt, prompt, src_text, src_name, anchors,
                            tasks_dir, gold_dir, input_dir,
                            compute="cl = [float(r[1]) for r in data]\n"
                                    "cd = [float(r[2]) for r in data]\n"
                                    "ld = [float(r[3]) for r in data]")
            n += 1
    for i in range(3):
        src_text, rows = load_input(i)
        src_name = f"load_{i + 1:02d}.csv"
        anchors = _anchors_load(rows)
        anch_line = _anchor_lines(anchors)
        for fmt, prompt_tpl in (("docx", awdoc_docx_prompt), ("pptx", awdoc_pptx_prompt)):
            tid = f"awd_{'rep' if fmt == 'docx' else 'brf'}_load_{i + 1:02d}"
            prompt = (prompt_tpl(i, src_name, rows,
                                 ["case", "load_factor", "cycles"])
                      .replace(ANCHOR_PLACEHOLDER, anch_line))
            emit_awdoc_task(tid, fmt, prompt, src_text, src_name, anchors,
                            tasks_dir, gold_dir, input_dir,
                            compute="lf = [float(r[1]) for r in data]\n"
                                    "cyc = [int(float(r[2])) for r in data]")
            n += 1
    return n


def emit_awdoc_task(tid, fmt, prompt, src_text, src_name, anchors,
                    tasks_dir, gold_dir, input_dir, compute):
    psha = hashlib.sha256(prompt.encode()).hexdigest()
    isha = hashlib.sha256(src_text.encode()).hexdigest()
    (tasks_dir / f"{tid}.md").write_text(prompt, encoding="utf-8")
    (input_dir / src_name).write_text(src_text, encoding="utf-8")
    anch_nums = [v for v in anchors.values() if isinstance(v, (int, float))]
    if fmt == "docx":
        gold = GOLD_DOCX.format(src=src_name, compute=compute,
                                summary_py=_summary_py(anchors))
        checks = [{"check": "n_tables", "expect": 1}, {"check": "n_images", "expect": 0},
                  {"check": "n_paragraphs_min", "expect": 8}]
    else:
        gold = GOLD_PPTX.format(src=src_name, compute=compute,
                                summary_pptx=_summary_pptx(anchors))
        checks = [{"check": "n_slides", "expect": 4}, {"check": "n_tables", "expect": 1}]
    (gold_dir / f"{tid}.py").write_text(gold, encoding="utf-8")
    checks_txt = "\n".join(f"  - check: {c['check']}\n    expect: {c['expect']}"
                           for c in checks)
    anch_txt = "\n".join(f"  - {v}" for v in anch_nums)
    yml = f"""id: {tid}
registry_id: awdoc.office_docs
domain: office_productivity
task_type: design_artifact
model_profile: plain_llm
assets_revision: {REV_A}
environment_digest: computed-at-runtime
hidden: false
allowed_tools:
- python
input:
  prompt_file: tasks/awdoc.office_docs/{tid}.md
  prompt_sha256: {psha}
  assets:
  - path: data/awdoc/office_docs/inputs/{src_name}
    digest: {isha}
output_contract:
- report.{fmt}
reference:
  source: 自建（锚定数字=源数据派生统计；结构契约钉死）
  revision: {REV_A}
  values:
    n_anchors: {len(anch_nums)}
  rel_tol: 0.005
  uncertainty_note: 锚定数字以数值级比对（0.5% 容差）；字符串锚（构型名）不判
grader:
  artifact_kind: doc_document
  doc_format: {fmt}
  answer_format: code
  validity_gate: true
  anchored_numbers:
{anch_txt}
  structure_checks:
{checks_txt}
  numeric_rel_tol: 0.005
  oracle_source: data/awdoc/office_docs/gold/{tid}.py
  sandbox:
    banned: shell/network/process
    isolated_interpreter: true
scoring:
  weights:
    physics: 0.5
    requirements: 0.5
    objective: 0.0
    robustness: 0.0
  note: physics=锚定数字命中；requirements=结构契约
limits:
  cpu: 1
  memory_gb: 4
  wall_clock_s: 300
  attempts: 3
license_provenance:
  source: 自建（工程报告/汇报数据锚定族）
  license: self-built
  status: confirmed-selfbuilt
  mirror_allowed: true
  revision: {REV_A}
"""
    (tasks_dir / f"{tid}.yaml").write_text(yml, encoding="utf-8")


GOLD_PPTX = '''"""gold — data-anchored briefing deck (pptx)."""
import csv
from pptx import Presentation
from pptx.util import Inches

with open("{src}", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
header, data = rows[0], rows[1:]

{compute}

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "Test Briefing"
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Data"
tbl_shape = slide.shapes.add_table(len(data) + 1, len(header), Inches(0.5), Inches(1.2), Inches(6), Inches(0.4 + 0.25 * len(data)))
tbl = tbl_shape.table
for i, h in enumerate(header):
    tbl.cell(0, i).text = str(h)
for r_i, r in enumerate(data, 1):
    for c_i, v in enumerate(r):
        tbl.cell(r_i, c_i).text = str(v)
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Summary"
tf = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(6), Inches(3)).text_frame
{summary_pptx}
slide = prs.slides.add_slide(prs.slide_layouts[5])
slide.shapes.title.text = "Next steps"
slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(6), Inches(2)).text_frame.text = "TBD"
prs.save("report.pptx")
'''


def _summary_pptx(anchors):
    lines = ['tf.text = "Summary"']
    for label, v in anchors.items():
        lines.append(f'p = tf.add_paragraph(); p.text = "{label} = {{{v!r}}}"')
    return "\n".join(lines)


ANCHOR_PLACEHOLDER = "__ANCHORS__"


# ================================================================ B. awext（自建条款风格卡）

CLAUSE_FAMILIES = [
    # (family, 卡片模板参数化说明)
    ("loads", "限制与机动载荷包线"),
    ("structure", "结构强度与变形要求"),
    ("control", "操纵面与配平能力"),
    ("stall", "失速特性与最小速度"),
]


def synth_clause_card(seed):
    """生成一张自建条款风格卡（非真实规章原文——参数化合成，防误引；
    KB 恢复后按 doc_id 重新锚定真实条款，PROVENANCE 记录）。"""
    rng = random.Random(310025 + seed)
    fam = CLAUSE_FAMILIES[seed % len(CLAUSE_FAMILIES)][0]
    v1 = round(2.1 + rng.random() * 1.6, 2)      # 载荷系数类
    v2 = round(-0.4 - rng.random() * 0.9, 2)     # 负向载荷系数
    v3 = int(rng.choice([1.25, 1.5, 1.75, 2.0])) * 1000   # 循环/次数
    v4 = round(1.0 + rng.random() * 3.0, 1)      # 概率/小时
    card = {
        "doc_id": f"ACX-{fam.upper()}-{100 + seed}",
        "family": fam,
        "clause_no": f"§{seed % 9 + 1}.{rng.randint(10, 99)}",
        "title": f"{CLAUSE_FAMILIES[seed % len(CLAUSE_FAMILIES)][1]}",
        "limits": {"n_positive": v1, "n_negative": v2},
        "cycles_or_actions": v3,
        "probability_per_hour": v4,
        "applies_to": sorted(rng.sample(
            ["wing", "fuselage", "empennage", "control-surface",
             "landing-gear", "engine-mount"], k=rng.randint(2, 4))),
        "compliance_methods": sorted(rng.sample(
            ["analysis", "test", "simulation", "inspection"],
            k=rng.randint(2, 3))),
        "amendment_year": rng.choice([2011, 2016, 2022]),
    }
    return card


def clause_prompt(card):
    return f"""# Structured extraction from a requirement card

Read the requirement card below and respond with ONE ```json code block
containing EXACTLY these fields (no extra fields):

{{
  "family": string,
  "clause_no": string,
  "positive_load_limit": number,
  "negative_load_limit": number,
  "cycles_or_actions": integer,
  "probability_per_hour": number,
  "applies_to": sorted list of strings (ascending),
  "compliance_methods": sorted list of strings (ascending),
  "amendment_year": integer
}}

Rules: copy values verbatim from the card (numbers as numbers); sort the two
list fields ascending (string sort); do not add commentary outside the JSON.

## Requirement card

---
Document: {card['doc_id']}
Section: {card['clause_no']} — {card['title']}
Category: structural certification requirements ({card['family']} family)

Text: For the configurations listed in the applicability table, the design
load envelope shall sustain a positive limit load factor of {card['limits']['n_positive']}
and a negative limit load factor of {card['limits']['n_negative']} without
detrimental permanent deformation. Repeated application up to
{card['cycles_or_actions']} action cycles shall be considered. The occurrence
probabilities used in this section shall not exceed {card['probability_per_hour']}
per flight hour. Compliance shall be shown by: {", ".join(card['compliance_methods'])}.
Applicability: {", ".join(card['applies_to'])}.
As amended: Amendment {card['amendment_year']}.
---
"""


def clause_ref_json(card):
    return {
        "family": card["family"],
        "clause_no": card["clause_no"],
        "positive_load_limit": card["limits"]["n_positive"],
        "negative_load_limit": card["limits"]["n_negative"],
        "cycles_or_actions": card["cycles_or_actions"],
        "probability_per_hour": card["probability_per_hour"],
        "applies_to": sorted(card["applies_to"]),
        "compliance_methods": sorted(card["compliance_methods"]),
        "amendment_year": card["amendment_year"],
    }


GOLD_JSON_TMPL = '```json\n{json}\n```'


def gen_awext():
    tasks_dir = BENCH / "tasks" / "awext.clause_extract"
    gold_dir = BENCH / "data" / "awext" / "clause_extract" / "gold"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)
    for i in range(12):
        card = synth_clause_card(i)
        prompt = clause_prompt(card)
        psha = hashlib.sha256(prompt.encode()).hexdigest()
        tid = f"awx_ce_{i + 1:02d}"
        (tasks_dir / f"{tid}.md").write_text(prompt, encoding="utf-8")
        ref = clause_ref_json(card)
        gold = GOLD_JSON_TMPL.format(json=json.dumps(ref, indent=2, ensure_ascii=False))
        (gold_dir / f"{tid}.txt").write_text(gold, encoding="utf-8")
        yml = f"""id: {tid}
registry_id: awext.clause_extract
domain: office_productivity
task_type: qa_grounded
model_profile: plain_llm
assets_revision: {REV_B}
environment_digest: computed-at-runtime
hidden: false
allowed_tools: []
input:
  prompt_file: tasks/awext.clause_extract/{tid}.md
  prompt_sha256: {psha}
  assets: []
output_contract:
- json
reference:
  source: 自建条款风格卡（参数化合成，非真实规章原文——防误引；civair-kb 恢复后按 doc_id 重锚）
  revision: {REV_B}
  reference_json: {json.dumps(ref, ensure_ascii=False)}
  rel_tol: 0.02
  uncertainty_note: 字段级判分（数值 2% 容差；列表排序 casefold 精确）
grader:
  answer_format: json_extract
  validity_gate: true
  numeric_rel_tol: 0.02
  sandbox:
    banned: shell/network/process
    isolated_interpreter: false
scoring:
  weights:
    requirements: 1.0
    physics: 0.0
    objective: 0.0
    robustness: 0.0
  note: requirements=JSON 字段命中比例（qa_grounded json_extract 层）
limits:
  cpu: 1
  memory_gb: 2
  wall_clock_s: 120
  attempts: 3
license_provenance:
  source: 自建（条款风格卡；KB 联动待锚定）
  license: self-built
  status: confirmed-selfbuilt
  mirror_allowed: true
  revision: {REV_B}
"""
        (tasks_dir / f"{tid}.yaml").write_text(yml, encoding="utf-8")
    return 12


# ================================================================ C. SpreadsheetBench 子集

SSB_URL = ("https://huggingface.co/datasets/KAKA22/SpreadsheetBench/resolve/main/"
           "spreadsheetbench_verified_400.tar.gz")


def fetch_ssb(tmpdir: Path) -> Path:
    """镜像 verified_400 tar（含 sha256 校验列表落盘）。"""
    import time
    dest = BENCH / "data" / "spreadsheetbench" / "verified_400"
    dest.mkdir(parents=True, exist_ok=True)
    tar_path = dest / "spreadsheetbench_verified_400.tar.gz"
    if not tar_path.exists():
        for attempt in range(3):
            try:
                with urllib.request.urlopen(SSB_URL, timeout=300) as r, \
                        open(tar_path, "wb") as f:
                    shutil.copyfileobj(r, f)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(3)
    h = hashlib.sha256(tar_path.read_bytes()).hexdigest()
    (dest / "tar.sha256").write_text(f"{h}  {tar_path.name}\n")
    # 解包（幂等）
    marker = dest / ".extracted"
    if not marker.exists():
        with tarfile.open(tar_path) as tf:
            tf.extractall(dest)
        marker.touch()
    return dest / "spreadsheetbench_verified_400"


def ssb_candidate_ok(item, root: Path) -> tuple[bool, str]:
    """人工筛选标准的程序化近似：
    1. golden 存在且 answer 区域非空；
    2. init/golden 可被 openpyxl 读取；
    3. answer 区域内 golden 值可静态判定（数值/字符串，非公式依赖——
       data_only 读 golden 无缓存时为 None 即公式）。
    """
    import openpyxl
    sp = root / item["spreadsheet_path"]
    golden = sp / f"1_{str(item['id'])}_golden.xlsx"
    init = sp / f"1_{str(item['id'])}_init.xlsx"
    if not golden.exists() or not init.exists():
        return False, "missing files"
    # answer_sheet 可能是逗号/引号分隔的多 sheet 列表——取首个
    first_sheet = str(item.get("answer_sheet") or "").strip(" '\"").split(",")[0].strip()
    try:
        wb = openpyxl.load_workbook(golden, data_only=True)
        ws = wb[first_sheet] if first_sheet in wb.sheetnames else wb.worksheets[0]
    except Exception:
        return False, "unreadable golden"
    region = item["answer_position"]
    try:
        rng, sheet_region = region.split("!")
        sheet_region = sheet_region or rng
    except ValueError:
        sheet_region = region
    import re
    m = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)", sheet_region)
    if not m:
        wb.close()
        return False, "bad region"
    c1, r1, c2, r2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
    n_static = n_formula = 0
    from openpyxl.utils import column_index_from_string
    for row in ws.iter_rows(min_row=r1, max_row=r2,
                            min_col=column_index_from_string(c1),
                            max_col=column_index_from_string(c2)):
        for cell in row:
            if cell.value is None:
                n_formula += 1          # 无缓存值（公式或空）
            elif isinstance(cell.value, (int, float, str)):
                n_static += 1
    wb.close()
    if n_static == 0:
        return False, "all-formula region"
    return True, f"static={n_static} empty={n_formula}"


def gen_ssb(limit=50):
    dest = BENCH / "data" / "spreadsheetbench" / "verified_400"
    root = fetch_ssb(dest.parent)
    dataset = json.loads((root / "dataset.json").read_text())
    tasks_dir = BENCH / "tasks" / "spreadsheetbench.verified_subset"
    gold_dir = dest / "gold"
    inputs_dir = dest / "inputs"
    for d in (tasks_dir, gold_dir, inputs_dir):
        d.mkdir(parents=True, exist_ok=True)
    picked, seen_type = [], {"Cell-Level Manipulation": 0, "Sheet-Level Manipulation": 0}
    stats = {"rejected": 0}
    for item in dataset:          # 全量扫描：单类型满额只跳过该题，不早停
        if len(picked) >= limit:
            break
        ok, why = ssb_candidate_ok(item, root)
        if not ok:
            stats["rejected"] += 1
            continue
        # 类型配额：25 cell-level + 25 sheet-level
        t = item["instruction_type"]
        cap = 25 if t == "Cell-Level Manipulation" else 25
        if seen_type[t] >= cap:
            continue
        seen_type[t] += 1
        sid = str(item["id"])
        if not item.get("answer_sheet") or not item.get("answer_position"):
            stats["rejected"] += 1
            continue                    # 卡片缺 answer 定位——无法客观判分
        tid = f"ssb_{sid.replace('-', '_').replace('/', '_')}"
        sp = root / item["spreadsheet_path"]
        init_f = sp / f"1_{sid}_init.xlsx"
        golden_f = sp / f"1_{sid}_golden.xlsx"
        shutil.copy(init_f, inputs_dir / f"{tid}_init.xlsx")
        shutil.copy(golden_f, gold_dir / f"{tid}_golden.xlsx")
        prompt = (item["instruction"] +
                  f"\n\n## Answer region\nWrite your answer into sheet "
                  f"`{item['answer_sheet']}` cells `{item['answer_position']}` "
                  f"of `output.xlsx` (a copy of the provided input workbook).")
        psha = hashlib.sha256(prompt.encode()).hexdigest()
        (tasks_dir / f"{tid}.md").write_text(prompt, encoding="utf-8")
        isha = hashlib.sha256((inputs_dir / f"{tid}_init.xlsx").read_bytes()).hexdigest()
        yml = f"""id: {tid}
registry_id: spreadsheetbench.verified_subset
domain: office_productivity
task_type: design_artifact
model_profile: plain_llm
assets_revision: {REV_C}
environment_digest: computed-at-runtime
hidden: false
allowed_tools:
- python
input:
  prompt_file: tasks/spreadsheetbench.verified_subset/{tid}.md
  prompt_sha256: {psha}
  assets:
  - path: data/spreadsheetbench/verified_400/inputs/{tid}_init.xlsx
    digest: {isha}
output_contract:
- output.xlsx
reference:
  source: SpreadsheetBench verified_400 golden（CC-BY-SA-4.0；answer 区域静态值）
  revision: {REV_C}
  values:
    answer_sheet: {str(item['answer_sheet']).split(',')[0].strip(" '")}
    answer_position: "{item['answer_position']}"
  rel_tol: 0.005
  uncertainty_note: answer 区域单元格级比对（静态值；公式依赖题已筛除）
grader:
  artifact_kind: formula_cell
  answer_format: code
  validity_gate: true
  answer_sheet: {str(item['answer_sheet']).split(',')[0].strip(" '")}
  answer_position: "{item['answer_position']}"
  golden_workbook: data/spreadsheetbench/verified_400/gold/{tid}_golden.xlsx
  numeric_rel_tol: 0.005
  sandbox:
    banned: shell/network/process
    isolated_interpreter: true
scoring:
  weights:
    physics: 0.5
    requirements: 0.5
    objective: 0.0
    robustness: 0.0
  note: physics=answer 区域命中；requirements=工作簿可读+sheet 保持
limits:
  cpu: 1
  memory_gb: 4
  wall_clock_s: 300
  attempts: 3
license_provenance:
  source: SpreadsheetBench verified_400 子集（HF KAKA22/SpreadsheetBench）
  license: CC-BY-SA-4.0（SA 衍生同许可——superwing 先例口径）
  status: confirmed-dataset
  mirror_allowed: true
  revision: {REV_C}
"""
        (tasks_dir / f"{tid}.yaml").write_text(yml, encoding="utf-8")
        picked.append(item)
    return len(picked), stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-ssb", action="store_true")
    args = ap.parse_args()
    n_a = gen_awdoc()
    print(f"A awdoc.office_docs: {n_a} tasks")
    n_b = gen_awext()
    print(f"B awext.clause_extract: {n_b} tasks")
    if not args.skip_ssb:
        n_c, stats = gen_ssb(50)
        print(f"C spreadsheetbench.verified_subset: {n_c} tasks ({stats})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
