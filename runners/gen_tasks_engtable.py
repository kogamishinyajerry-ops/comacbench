#!/usr/bin/env python3
"""gen_tasks_engtable.py — engtable.office_basic 任务生成 + gold + 判分自检。

office_productivity 维首批（2026-08-25 用户裁决：自建工程表格加工族先行）。
工程办公画像：原始试验数据（CSV）→ 规范工作簿（xlsx，静态值）——BOM 合并/
透视汇总/单位换算/越限标记/超差清单。判分 100% 本地复现（openpyxl 单元格级
比对 gold 工作簿；无 LLM judge、无 GUI、无外部依赖——内网可移植）。

协议：模型写单个 ```python（openpyxl/casv/标准库），读 cwd 下题面给定的输入
CSV，产出 output.xlsx（契约：sheet 名/表头精确、静态值无公式、数值四舍五入
到指定位数）。判分 = design_artifact xlsx_table 模式（双跑确定性 gate +
gold 非空单元格命中 − 多余惩罚 + 结构契约）。

族（5 族 19 题，全部参数化确定性生成）：
  bom    杂乱 BOM（重复件号跨行/备注干扰列）→ 规范 BOM（件号排序、数量合并）
  pivot  长表试验数据（构型×通道×值）→ 宽表汇总（构型行×通道列，按规格取均值/最大）
  si     混合单位表（lbf/in/°F 混排）→ SI 规范表（固定换算系数，round 3）
  flag   时序测量 → 增列 status（OK/OVER/MISSING）+ 摘要 sheet（min/max/mean）
  exceed 时序载荷 → 超差事件清单（阈值过滤 + 降序 top-K）

用法：.venv/bin/python -m runners.gen_tasks_engtable   （幂等；生成后 gold 全链自检）
"""
from __future__ import annotations

import csv
import hashlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
RID = "engtable.office_basic"
TASKS_DIR = BENCH / "tasks" / RID
DATA_DIR = BENCH / "data" / "engtable" / "office_basic"
GOLD_DIR = DATA_DIR / "gold"
INPUT_DIR = DATA_DIR / "inputs"
GOLDOUT_DIR = DATA_DIR / "gold_output"
REV = "engtable@selfbuilt-2026-08-25"

LBF_N = 4.4482216152605
IN_MM = 25.4
F_C = lambda f: (f - 32.0) * 5.0 / 9.0  # noqa: E731


# ---------------------------------------------------------------- 输入数据族

def _csv_text(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def bom_input(seed):
    """杂乱 BOM：件号跨行重复、数量分散、干扰列（备注/批次）。确定性参数化。"""
    parts = ["P-1001", "P-1002", "P-1003", "P-1004", "P-1005", "P-1006",
             "P-1007", "P-1008"][:4 + (seed % 5)]
    names = {"P-1001": "bracket", "P-1002": "fastener", "P-1003": "gusset",
             "P-1004": "spacer", "P-1005": "rib", "P-1006": "clip",
             "P-1007": "bushing", "P-1008": "plate"}
    rows = []
    for i, p in enumerate(parts):
        for k in range(1 + (i + seed) % 3):
            rows.append([p, names[p], 1 + ((i * 3 + k * 2 + seed) % 9),
                         "pcs", f"lot-{(i + k) % 4}", "scrap note" if k == 0 and i % 2 else ""])
    return _csv_text(["part_no", "desc", "qty", "unit", "batch", "note"], rows)


def pivot_input(seed):
    """长表：构型×通道×值（每格 2-3 个重复测量行，供按规格聚合）。"""
    configs = ["CFG-A", "CFG-B", "CFG-C", "CFG-D", "CFG-E"][:3 + seed % 3]
    channels = ["lift", "drag", "moment"]
    rows = []
    for ci, c in enumerate(configs):
        for ch in channels:
            for rep in range(2 + (ci + seed) % 2):
                base = {"lift": 120.0, "drag": 24.0, "moment": -8.5}[ch]
                v = round(base + ci * 6.5 + rep * 1.25 + (seed % 3) * 0.5, 2)
                rows.append([c, ch, rep + 1, v])
    return _csv_text(["config", "channel", "rep", "value"], rows)


def si_input(seed):
    """混合单位测量行：force(lbf) / length(in) / temp(°F) 混排（unit 列标明）。"""
    rows = []
    for i in range(8 + seed % 5):
        f = round(85.0 + i * 17.5 + seed, 2)
        l = round(2.5 + i * 0.75, 2)
        t = round(68.0 + i * 3.6, 1)
        rows.append([f"RUN-{i + 1:02d}", f, l, t])
    return _csv_text(["run", "force_lbf", "length_in", "temp_f"], rows)


def flag_input(seed):
    """时序测量：3 通道，植入越限点与缺失点（EMPTY 字段）。"""
    rows = []
    n = 14 + seed * 3
    for i in range(n):
        alt = round(10000.0 + 800.0 * i + (i % 5) * 120.0, 1)
        spd = round(140.0 + (i % 7) * 9.0, 1)
        load = round(1.10 + (i % 4) * 0.35, 2)
        if i == 4 + seed % 3:
            load = ""            # 植入缺失
        if i == n - 2:
            spd = round(spd + 55.0, 1)   # 植入越限
        if i == 3:
            alt = round(alt + 1500.0, 1)
        rows.append([f"T{i:03d}", alt, spd, load])
    return _csv_text(["time", "alt_ft", "ias_kt", "load_g"], rows)


def exceed_input(seed):
    """时序载荷：峰值事件供 top-K 提取。"""
    rows = []
    n = 20 + seed * 4
    for i in range(n):
        v = round(1.0 + 0.8 * ((i * 7 + seed * 3) % 10) / 9.0
                  + (0.55 if i % 6 == 0 else 0.0), 2)
        rows.append([f"E{i:03d}", round(2000.0 + 37.5 * i, 1), v])
    return _csv_text(["event", "t_s", "load_factor"], rows)


# ---------------------------------------------------------------- 变换（gold 与题面规格同源）

def bom_transform(hdr_text):
    rows = list(csv.reader(io.StringIO(hdr_text)))[1:]
    agg = {}
    for p, desc, qty, unit, batch, note in rows:
        agg.setdefault(p, [desc, 0, unit])
        agg[p][1] += int(qty)
    out = [[p, v[0], v[1], v[2]] for p, v in sorted(agg.items())]
    return ["BOM", ["part_no", "desc", "qty_total", "unit"], out]


def pivot_transform(hdr_text, agg):
    rows = list(csv.reader(io.StringIO(hdr_text)))[1:]
    cells = {}
    for c, ch, rep, v in rows:
        cells.setdefault((c, ch), []).append(float(v))
    configs, channels = [], []
    for c, ch in cells:
        if c not in configs:
            configs.append(c)
        if ch not in channels:
            channels.append(ch)
    configs.sort()
    channels.sort()
    f = (lambda xs: sum(xs) / len(xs)) if agg == "mean" else max
    out = [[c] + [round(f(cells[(c, ch)]), 3) for ch in channels] for c in configs]
    return ["SUMMARY", ["config"] + channels, out]


def si_transform(hdr_text):
    rows = list(csv.reader(io.StringIO(hdr_text)))[1:]
    out = []
    for run, f, l, t in rows:
        out.append([run, round(float(f) * LBF_N, 3), round(float(l) * IN_MM, 3),
                    round(F_C(float(t)), 3)])
    return ["SI", ["run", "force_n", "length_mm", "temp_c"], out]


def flag_thresholds(seed):
    return {"alt_ft": (9000.0, 18000.0), "ias_kt": (135.0, 210.0),
            "load_g": (1.00 + 0.05 * (seed % 2), 2.20)}


def flag_transform(hdr_text, seed):
    th = flag_thresholds(seed)
    rows = list(csv.reader(io.StringIO(hdr_text)))[1:]
    out_rows = []
    stats = {}
    for t, alt, spd, load in rows:
        vals = {"alt_ft": alt, "ias_kt": spd, "load_g": load}
        statuses = []
        for ch, v in vals.items():
            if v == "":
                statuses.append("MISSING")
            else:
                lo, hi = th[ch]
                statuses.append("OVER" if not (lo <= float(v) <= hi) else "OK")
        out_rows.append([t, alt, spd, load] + statuses)
        for ch, v in vals.items():
            if v != "":
                stats.setdefault(ch, []).append(float(v))
    summary = [[ch, round(min(vs), 3), round(max(vs), 3), round(sum(vs) / len(vs), 3)]
               for ch, vs in sorted(stats.items())]
    return [("DATA", ["time", "alt_ft", "ias_kt", "load_g",
                      "status_alt", "status_ias", "status_load"], out_rows),
            ("STATS", ["channel", "min", "max", "mean"], summary)]


def exceed_transform(hdr_text, k):
    rows = list(csv.reader(io.StringIO(hdr_text)))[1:]
    vals = [(r[0], r[1], float(r[2])) for r in rows if float(r[2]) >= 1.60]
    vals.sort(key=lambda x: -x[2])
    out = [[e, t, round(v, 2)] for e, t, v in vals[:k]]
    return ["EXCEED", ["event", "t_s", "load_factor"], out]


# ---------------------------------------------------------------- gold 工作簿脚本

GOLD_HEADER = '''"""gold — write the required normalized workbook (STATIC values, no formulas)."""
import csv
import openpyxl

with open("input.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))

wb = openpyxl.Workbook()
wb.remove(wb.active)
'''


def _sheet_py(sheet):
    name, header, data = sheet
    lines = [f'ws = wb.create_sheet("{name}")',
             f'ws.append({header!r})']
    for row in data:
        lines.append(f"ws.append({row!r})")
    return "\n".join(lines)


def gold_script(sheets, input_name="input.csv"):
    body = "\n".join(_sheet_py(s) for s in sheets)
    return (GOLD_HEADER.replace('"input.csv"', f'"{input_name}"')
            + body + '\nwb.save("output.xlsx")\n')


# ---------------------------------------------------------------- 任务定义与 prompt

CONTRACT = """
## Output contract (grading is cell-level and objective)

- Produce a file named exactly `output.xlsx` in the current directory (openpyxl
  Workbook is the expected tool; you may use only the Python standard library
  plus openpyxl).
- Write STATIC values only — NO formulas in any cell (the grader reads values,
  a formula cell reads as None and scores as a miss).
- Sheet names and header rows (row 1) must match the specification EXACTLY
  (names, spelling, order). Extra sheets, extra columns, or extra populated
  cells outside the specified tables are penalized.
- Round every computed numeric cell to {round} decimal places (Python round()).
- No formatting requirements (colors/bold are ignored by the grader).
"""


def tasks_def():
    T = []

    def add(tid, fam, input_text, input_name, sheets, spec_text, round_n=3):
        T.append(dict(tid=tid, fam=fam, input_text=input_text,
                      input_name=input_name, sheets=sheets,
                      spec_text=spec_text, round_n=round_n))

    for i in range(4):
        it = bom_input(i)
        add(f"eng_bom_{i + 1:02d}", "bom", it, f"eng_bom_{i + 1:02d}.csv",
            [bom_transform(it)],
            """1. Read `INPUTFILE` (columns: part_no, desc, qty, unit, batch, note).
2. The source has duplicate part numbers spread across rows.
3. Output ONE sheet named `BOM` with header exactly:
   ["part_no", "desc", "qty_total", "unit"]
4. One row per unique part_no: desc and unit from the source, qty_total = SUM of
   all qty values for that part_no.
5. Sort rows by part_no ascending (string sort).
6. Do not carry over batch/note columns.""", 0)

    for i in range(4):
        it = pivot_input(i)
        agg = "mean" if i % 2 == 0 else "max"
        add(f"eng_pivot_{i + 1:02d}", "pivot", it, f"eng_pivot_{i + 1:02d}.csv",
            [pivot_transform(it, agg)],
            f"""1. Read `INPUTFILE` (columns: config, channel, rep, value) — long format:
   each (config, channel) pair has 2-4 repeat measurements.
2. Output ONE sheet named `SUMMARY` with header exactly:
   ["config"] + sorted channel names from the data (e.g. ["config", "drag",
   "lift", "moment"] — alphabetical order).
3. One row per config (sorted ascending). Each cell = the {agg.upper()} of all
   values for that (config, channel), rounded to 3 decimals.
4. Keep the original measured values as-is when aggregating (no pre-rounding).""", 3)

    for i in range(4):
        it = si_input(i)
        add(f"eng_si_{i + 1:02d}", "si", it, f"eng_si_{i + 1:02d}.csv",
            [si_transform(it)],
            """1. Read `INPUTFILE` (columns: run, force_lbf, length_in, temp_f).
2. Output ONE sheet named `SI` with header exactly:
   ["run", "force_n", "length_mm", "temp_c"]
3. Convert per row using EXACTLY these factors:
   force_n = force_lbf * 4.4482216152605
   length_mm = length_in * 25.4
   temp_c = (temp_f - 32.0) * 5.0 / 9.0
4. Round every converted value to 3 decimals; keep the run id string unchanged.
5. Preserve source row order.""", 3)

    for i in range(3):
        it = flag_input(i)
        th = flag_thresholds(i)
        sheets = flag_transform(it, i)
        add(f"eng_flag_{i + 1:02d}", "flag", it, f"eng_flag_{i + 1:02d}.csv", sheets,
            f"""1. Read `INPUTFILE` (columns: time, alt_ft, ias_kt, load_g). Some load_g
   cells are EMPTY (missing measurements).
2. Output TWO sheets.

Sheet `DATA`, header exactly:
["time", "alt_ft", "ias_kt", "load_g", "status_alt", "status_ias", "status_load"]
- Copy the four source columns unchanged (empty stays empty — do NOT write
  anything, not even 0 or a blank string, into an empty cell).
- For each channel add a status column with exactly one of "OK" / "OVER" /
  "MISSING": "MISSING" if the source cell is empty; otherwise "OVER" if the
  value is outside the inclusive limit range, "OK" if inside.

Limits (inclusive [lo, hi]):
- alt_ft: [{th['alt_ft'][0]}, {th['alt_ft'][1]}]
- ias_kt: [{th['ias_kt'][0]}, {th['ias_kt'][1]}]
- load_g: [{th['load_g'][0]}, {th['load_g'][1]}]

Sheet `STATS`, header exactly: ["channel", "min", "max", "mean"]
- One row per channel name sorted ascending (alt_ft, ias_kt, load_g);
  min/max/mean computed over NON-EMPTY values only, rounded to 3 decimals.
- The status columns are NOT part of stats.""", 3)

    for i in range(4):
        it = exceed_input(i)
        k = 4 + i
        add(f"eng_exceed_{i + 1:02d}", "exceed", it, f"eng_exceed_{i + 1:02d}.csv",
            [exceed_transform(it, k)],
            f"""1. Read `INPUTFILE` (columns: event, t_s, load_factor).
2. Select all rows with load_factor >= 1.60.
3. Sort the selected rows by load_factor DESCENDING (largest first); for equal
   values keep source order.
4. Output ONE sheet named `EXCEED` with header exactly:
   ["event", "t_s", "load_factor"]
   containing the FIRST {k} rows of that sorted selection (top-{k}).
5. Copy event/t_s as strings unchanged; load_factor as the original number
   (already 2-decimal source data — do not re-round).""", 3)

    return T


# ---------------------------------------------------------------- prompt/yaml

def render_prompt(t):
    return (f"# Engineering table task — {t['fam']} family\n\n"
            "You are given an input file `" + t["input_name"] +
            "` in the current working directory.\n\n"
            "## Transformation specification\n\n"
            + t["spec_text"].replace("INPUTFILE", t["input_name"])
            + "\n## Workbooks and cells\n\n"
            "Respond with ONE complete ```python code block that performs the "
            "transformation and writes the workbook."
            + CONTRACT.format(round=t["round_n"]))


def emit_yaml(t, prompt_sha, input_sha):
    sheets_meta = []
    for name, header, _ in t["sheets"]:
        sheets_meta.append((name, header))
    sheet_names = [s[0] for s in sheets_meta]
    checks = [{"check": "sheet_names", "expect": sheet_names}]
    for name, header in sheets_meta:
        checks.append({"check": "header_row", "sheet": name, "expect": header})
    checks_txt = "\n".join(
        f"  - check: {c['check']}\n    expect: {c['expect']}"
        + (f"\n    sheet: {c['sheet']}" if "sheet" in c else "")
        for c in checks)
    n_sheets = len(sheets_meta)
    return f"""id: {t['tid']}
registry_id: {RID}
domain: office_productivity
task_type: design_artifact
model_profile: plain_llm
assets_revision: {REV}
environment_digest: computed-at-runtime
hidden: false
allowed_tools:
- python
input:
  prompt_file: tasks/{RID}/{t['tid']}.md
  prompt_sha256: {prompt_sha}
  assets:
  - path: data/engtable/office_basic/inputs/{t['tid']}.csv
    digest: {input_sha}
output_contract:
- output.xlsx
reference:
  source: gold 脚本实跑产出（openpyxl 静态值；自建任务，确定性变换）
  revision: {REV}
  values:
    n_sheets: {n_sheets}
  rel_tol: 0.005
  uncertainty_note: 单元格级比对（数值 0.5% 相对容差+3 位小数契约；字符串精确）
grader:
  artifact_kind: xlsx_table
  answer_format: code
  validity_gate: true
  gold_workbook: data/engtable/office_basic/gold_output/{t['tid']}.xlsx
  structure_checks:
{checks_txt}
  numeric_rel_tol: 0.005
  oracle_source: data/engtable/office_basic/gold/{t['tid']}.py
  sandbox:
    banned: shell/network/process
    isolated_interpreter: true
scoring:
  weights:
    physics: 0.5
    requirements: 0.5
    objective: 0.0
    robustness: 0.0
  note: physics=gold 非空单元格命中−多余惩罚；requirements=结构契约（sheet/表头）
limits:
  cpu: 1
  memory_gb: 4
  wall_clock_s: 240
  attempts: 3
license_provenance:
  source: 自建（工程表格加工族；航空试验数据风格，无外部数据）
  license: self-built
  status: confirmed-selfbuilt
  mirror_allowed: true
  revision: {REV}
"""


# ---------------------------------------------------------------- gold 全链自检

def gold_selfcheck(t):
    from runners.design_artifact import _xlsx_cells, _xlsx_match, _xlsx_structure_checks
    with tempfile.TemporaryDirectory(prefix="engt_") as td:
        Path(td, t["input_name"]).write_text(t["input_text"], encoding="utf-8")
        Path(td, "model.py").write_text(gold_script(t["sheets"], t["input_name"]),
                                        encoding="utf-8")
        r = subprocess.run([sys.executable, "model.py"], cwd=td,
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(f"{t['tid']} gold 失败: {r.stderr[-400:]}")
        got = _xlsx_cells(Path(td, "output.xlsx"))
        # gold_output 落盘（判分 GT）
        gold_out = GOLDOUT_DIR / f"{t['tid']}.xlsx"
        gold_out.write_bytes(Path(td, "output.xlsx").read_bytes())
        gold = _xlsx_cells(gold_out)
        m = _xlsx_match(gold, got, 0.005)
        checks = [{"check": "sheet_names",
                   "expect": [s[0] for s in t["sheets"]]}]
        for name, header, _ in t["sheets"]:
            checks.append({"check": "header_row", "sheet": name,
                           "expect": header})
        sc = _xlsx_structure_checks(checks, Path(td, "output.xlsx"))
        ok = (m["physics"] == 1.0 and all(c["ok"] for c in sc))
        return {"tid": t["tid"], "physics": m["physics"],
                "cells": m["n_gold"], "checks_ok": all(c["ok"] for c in sc),
                "pass": ok}


def main() -> int:
    for d in (TASKS_DIR, GOLD_DIR, INPUT_DIR, GOLDOUT_DIR):
        d.mkdir(parents=True, exist_ok=True)
    rows = []
    for t in tasks_def():
        prompt = render_prompt(t)
        psha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        isha = hashlib.sha256(t["input_text"].encode("utf-8")).hexdigest()
        (TASKS_DIR / f"{t['tid']}.md").write_text(prompt, encoding="utf-8")
        (TASKS_DIR / f"{t['tid']}.yaml").write_text(
            emit_yaml(t, psha, isha), encoding="utf-8")
        (INPUT_DIR / f"{t['tid']}.csv").write_text(t["input_text"], encoding="utf-8")
        (GOLD_DIR / f"{t['tid']}.py").write_text(
            gold_script(t["sheets"], t["input_name"]), encoding="utf-8")
        rows.append(gold_selfcheck(t))
        print(f"gen {t['tid']:<16} {t['fam']:<8} sheets={len(t['sheets'])}")
    print("\ngold 全链自检（判分管线对 gold 实跑）：")
    n_ok = 0
    for r in rows:
        n_ok += r["pass"]
        print(f"  {'PASS' if r['pass'] else 'FAIL'}  {r['tid']:<16} "
              f"physics={r['physics']} cells={r['cells']} checks={r['checks_ok']}")
    print(f"\n{n_ok}/{len(rows)} 通过；任务 -> {TASKS_DIR}")
    return 0 if n_ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
