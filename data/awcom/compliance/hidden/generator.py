#!/usr/bin/env python3
"""hidden/generator.py — awcom.compliance 隐藏池（每族 15 题 × 3 族 = 45）。

判分侧可信代码（同 gold 信任模型）。本文件同时是公开任务与隐藏池的**单一事实源**
（gen_tasks_awcom.py 经 importlib 调用本文件的族生成器出公开题）。
gen() -> {"pool": [...], "rev": ...}；每项 {id, prompt, reference_json,
exact_keys, rel_tol, domain}。answers.b64 由 gen_tasks_awcom 冻结；运行时经
runners.hidden_runtime 校验后物化（题面不落盘）。
"""
import random

REV = "awcom@selfbuilt-2026-08-26"
POOL_PER_FAM = 15

MC_CATALOG = """Compliance method catalog (authoritative for this task; ACX fictional standard):
- MC0 = compliance statement (符合性声明)
- MC1 = descriptive documentation / drawings (说明性文件)
- MC2 = analysis / calculation (分析计算)
- MC3 = safety assessment (安全性评估)
- MC4 = laboratory test (试验室试验)
- MC5 = ground test on the aircraft (地面试验)
- MC6 = flight test (试飞验证)
- MC7 = aircraft inspection (航空器检查)
- MC8 = simulator test (模拟器试验)
- MC9 = equipment qualification (设备合格性)

Selection rules (apply exactly):
1. Each available evidence item maps to exactly one method as stated on the card.
2. primary_method = the available method with the HIGHEST precedence, where
   precedence (high to low) is:
   MC6 > MC5 > MC4 > MC8 > MC9 > MC3 > MC2 > MC7 > MC1 > MC0.
3. secondary_methods = all OTHER available methods, sorted by method code ascending.
4. witnesses_required = true if and only if primary_method is MC6 (flight test
   requires certification witnesses).
5. documented_only = true if and only if every available method is MC0 or MC1."""

EVIDENCE_MAP = [
    ("a supplier compliance statement is on record", "MC0"),
    ("a descriptive drawing set is complete", "MC1"),
    ("a stress analysis report is available", "MC2"),
    ("a system safety assessment exists", "MC3"),
    ("a laboratory coupon test campaign is complete", "MC4"),
    ("a ground test on the prototype aircraft is planned", "MC5"),
    ("a certification flight test campaign is planned", "MC6"),
    ("a physical aircraft inspection is scheduled", "MC7"),
    ("a full-flight simulator session is available", "MC8"),
    ("the equipment holds a qualification certificate", "MC9"),
]
_CLAUSE_AREAS = ["LOAD", "STALL", "EWIS", "FUEL", "HYD", "LANDING", "PRESS", "FIRE"]
_PARAMS = [("limit_load_factor", 2.1, 3.0, 0.1),
           ("cabin_pressure_altitude_ft", 6000.0, 10000.0, 250.0),
           ("flap_limit_speed_ktas", 160.0, 220.0, 5.0),
           ("fuel_tank_inerting_o2_pct", 9.0, 12.0, 0.5)]
_APPS = ["wing", "fuselage", "empennage", "landing-gear", "engine-mount",
         "flight-deck", "cabin", "cargo"]

PROMPT_ACAM = """# Compliance method selection (ACAM) — {cid}

Read the requirement card and the available evidence, then respond with ONE
```json code block containing EXACTLY these fields (no extra fields):

{{
  "clause_id": string,
  "primary_method": "MC<n>",
  "secondary_methods": sorted list of "MC<n>" strings (ascending),
  "witnesses_required": boolean,
  "documented_only": boolean
}}

Field boundary: `clause_id` is the Document identifier only, without the Section
number or its title. Copy the Document identifier verbatim.

{catalog}

## Requirement card

---
Document: {cid}
Section: §{sec} — {area} category certification requirement
The design shall demonstrate compliance for this clause using the evidence
listed below. Available evidence:
{ev_lines}
---
"""

PROMPT_REV = """# Clause revision impact analysis

Compare the two amendments of the requirement below and respond with ONE
```json code block containing EXACTLY these fields (no extra fields):

{{
  "changed_params": {{"<param_name>": {{"old": number, "new": number}}, ...}} ({{}} if none),
  "changed_param_count": integer,
  "added_applicability": sorted list of strings ({{}} -> []),
  "removed_applicability": sorted list of strings,
  "severity": "major" or "minor",
  "compliance_recheck": boolean
}}

Rules: severity = "major" if and only if any parameter value changed OR any
applicability item was added/removed (renumbering/editorial notes alone are
"minor"); compliance_recheck = (severity == "major"). In changed_params, use
ONLY the canonical JSON keys below for parameters whose numeric values changed;
old/new are the verbatim numbers (no unit conversion). Omit unchanged parameters.

| Parameter wording in the amendments | Canonical JSON key |
| --- | --- |
| limit load factor | `limit_load_factor` |
| cabin pressure altitude (ft) | `cabin_pressure_altitude_ft` |
| flap limit speed (ktas) | `flap_limit_speed_ktas` |
| fuel tank inerting O2 (percent) | `fuel_tank_inerting_o2_pct` |

## Amendment A (2016)

---
{a}
---

## Amendment B (2022)

---
{b}
---
"""

PROMPT_TRC = """# Certification traceability extraction

Read the three document excerpts and respond with ONE ```json code block
containing EXACTLY these fields (no extra fields):

{{
  "requirement_id": string,
  "clause_ref": string,
  "evidence_ids": sorted list of strings (ascending),
  "verified_params": sorted list of strings,
  "test_only_params": sorted list of strings,
  "coverage_complete": boolean
}}

Rules: evidence_ids = every evidence document id cited by or citing the
requirement; verified_params = parameters covered by BOTH the test report and
the analysis note; test_only_params = covered by the test report but NOT the
analysis note; coverage_complete = every parameter listed in the requirement
is in verified_params.
Copy `clause_ref` verbatim from the requirement, including the § symbol and
the complete clause number; omit the sentence-ending punctuation.

## Requirement

---
{req}: The system shall verify {params} per {clause}.
Compliance evidence: see {tr} and {an}.
---

## Test report

---
{tr}: covers {tr_p} at representative conditions.
---

## Analysis note

---
{an}: analytical verification of {an_p}.
---
"""


# ---------------------------------------------------------------- 族生成器

def gen_acam(seed: int):
    rng = random.Random(9100 + seed)
    area = _CLAUSE_AREAS[seed % len(_CLAUSE_AREAS)]
    cid = f"ACX-{area}-{200 + seed % 60}"
    k = rng.randint(2, 4)
    idxs = rng.sample(range(len(EVIDENCE_MAP)), k)
    ev = [EVIDENCE_MAP[i] for i in sorted(idxs)]
    methods = sorted({m for _, m in ev})
    prec = ["MC6", "MC5", "MC4", "MC8", "MC9", "MC3", "MC2", "MC7", "MC1", "MC0"]
    primary = max(methods, key=lambda m: -prec.index(m))
    secondary = sorted(m for m in methods if m != primary)
    prompt = PROMPT_ACAM.format(
        cid=cid, sec=f"{seed % 9 + 1}.{seed % 90 + 10}", area=area,
        ev_lines="\n".join(f"{i + 1}. {t} -> {m}" for i, (t, m) in enumerate(ev)),
        catalog=MC_CATALOG)
    ref = {"clause_id": cid, "primary_method": primary,
           "secondary_methods": secondary,
           "witnesses_required": primary == "MC6",
           "documented_only": all(m in ("MC0", "MC1") for m in methods)}
    return prompt, ref


def gen_rev(seed: int):
    rng = random.Random(4200 + seed)
    pnames = rng.sample([p[0] for p in _PARAMS], k=3)
    steps = {p[0]: p[3] for p in _PARAMS}
    base = {p[0]: round(rng.uniform(p[1], p[2]), 1) for p in _PARAMS}
    v1, v2 = dict(base), dict(base)
    n_changed = rng.choice([0, 1, 1, 2])
    changed = {}
    for name in rng.sample(pnames, n_changed):
        delta = rng.choice([-1, 1]) * rng.choice([0.5, 1.0, 2.0])
        v2[name] = round(max(0.1, v1[name] + delta * steps[name]), 1)
        changed[name] = {"old": v1[name], "new": v2[name]}
    a1 = sorted(rng.sample(_APPS, k=rng.randint(3, 5)))
    a2 = list(a1)
    if rng.random() < 0.5:
        a2.append(rng.choice([a for a in _APPS if a not in a1]))
    if rng.random() < 0.4:
        a2.remove(rng.choice(a1))
    a2 = sorted(a2)
    added = sorted(set(a2) - set(a1))
    removed = sorted(set(a1) - set(a2))
    severity = "major" if (changed or added or removed) else "minor"

    def text(v, apps, amd):
        return (f"ACX-{_CLAUSE_AREAS[seed % 8]}-{300 + seed % 50} / Amendment {amd}\n"
                f"For the configurations listed, the design shall satisfy: "
                f"limit load factor {v['limit_load_factor']}, cabin pressure altitude "
                f"{v['cabin_pressure_altitude_ft']} ft, flap limit speed "
                f"{v['flap_limit_speed_ktas']} ktas, fuel tank inerting O2 "
                f"{v['fuel_tank_inerting_o2_pct']} percent. "
                f"Applicability: {', '.join(apps)}. Editorial note: this clause was "
                f"renumbered for readability.")

    prompt = PROMPT_REV.format(a=text(v1, a1, 2016), b=text(v2, a2, 2022))
    ref = {"changed_params": changed, "changed_param_count": len(changed),
           "added_applicability": added, "removed_applicability": removed,
           "severity": severity, "compliance_recheck": severity == "major"}
    return prompt, ref


def gen_trc(seed: int):
    rng = random.Random(7300 + seed)
    n = rng.randint(2, 4)
    params = [f"PARAM_{chr(65 + i)}{rng.randint(1, 9)}" for i in range(n)]
    req_id = f"SPEC-{rng.randint(10, 99)}"
    clause = f"§25.{rng.randint(101, 499)}"
    tr_id, an_id = f"TR-{rng.randint(10, 99)}", f"AN-{rng.randint(1, 9)}"
    tr_cov = set(rng.sample(params, k=rng.randint(1, n)))
    an_cov = set(rng.sample(params, k=rng.randint(1, n)))
    prompt = PROMPT_TRC.format(
        req=req_id, clause=clause, tr=tr_id, an=an_id,
        params=", ".join(params), tr_p=", ".join(sorted(tr_cov)),
        an_p=", ".join(sorted(an_cov)))
    ref = {"requirement_id": req_id, "clause_ref": clause,
           "evidence_ids": sorted([tr_id, an_id]),
           "verified_params": sorted(tr_cov & an_cov),
           "test_only_params": sorted(tr_cov - an_cov),
           "coverage_complete": set(params) == (tr_cov & an_cov)}
    return prompt, ref


EXACT = {"acam": ["clause_id", "primary_method"],
         "rev": ["changed_param_count", "old", "new", "severity"],
         "trc": ["requirement_id", "clause_ref"]}
GENS = {"acam": gen_acam, "rev": gen_rev, "trc": gen_trc}


def gen():
    """隐藏池全量（每族 POOL_PER_FAM 题，seed 与公开题不重叠）。"""
    pool = []
    for fam, g in GENS.items():
        for j in range(1, POOL_PER_FAM + 1):
            seed = 2000 + j * 7 + (sum(ord(c) for c in fam) % 100)
            prompt, ref = g(seed)
            pool.append({"id": f"awc_{fam}_h{j:02d}", "prompt": prompt,
                         "reference_json": ref, "exact_keys": EXACT[fam],
                         "rel_tol": 0.02, "domain": "airworthiness"})
    return {"pool": pool, "rev": REV}
