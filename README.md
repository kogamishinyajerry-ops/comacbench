# COMACBench

**An engineering-agent benchmark harness with native solver evidence.**
Evaluate agents that *do* engineering work — they submit scripts and decks, your platform runs the real solver, recomputes every quantity of interest from raw evidence, and scores against independently calibrated references with fault-injection negative controls.

> COMACBench 评测的是"干工程活"的 agent：agent 只交脚本/算例，平台独立执行求解器、从原始证据重算每个指标、用独立校准的参考值与故障注入负例判分。

[![tests](https://img.shields.io/badge/tests-150%2B_passing-brightgreen)]() [![packs](https://img.shields.io/badge/packs-3_first--party-blue)]() [![suite](https://img.shields.io/badge/suite-31_integrated_benchmarks-purple)]() [![status](https://img.shields.io/badge/status-private_dev-orange)]()

## Why it is different

- **Not self-reporting.** Agents never submit QoI values. The harness runs CalculiX / OpenFOAM / LibreOffice itself and re-derives every number from native artifacts (`model.inp`, solver stdout, `.dat`, polyMesh fields, wall-shear curves).
- **Gates before scores.** A `ValidityGate` layer (input completeness → units/modeling → mesh → solve completion → convergence/conservation → numerical reconciliation) runs before any sub-score. Gate failures and their reasons are first-class results.
- **Calibrated, not trusted.** Every pack ships an oracle self-check (reference must score full) and fault negatives (wrong load, missing material, coarse mesh, unconverged solve, forged logs … each must trigger its named diagnosis). A zero score is not calibration success; hitting the `expected_issue` is.
- **Reproducible by identity.** Each run carries a resume identity (pack sha256, engine, seed, agent revision, judge source digest). Same identity → trusted resume; any change → new output directory, old evidence preserved.
- **Honest boundaries.** Static preflight finds formal contradictions, not semantic truth. `publishable=false` until expert review. Results state what they do *not* prove (no model ranking, no aircraft-level acceptance, no commercial-CFD closed loop yet).

## Quickstart

```bash
git clone https://github.com/kogamishinyajerry-ops/comacbench && cd comacbench
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e .

# 1) static preflight of a pack (exit 2 = blockers, zero agent calls)
comacbench validate packs/aviation-structures-v2

# 2) calibrate the grader: reference passes, every fault negative fires
comacbench calibrate packs/aviation-structures-v2 --out ./calib-01

# 3) interface probe with the built-in reference agent (NOT a model score)
comacbench run packs/aviation-structures-v2 --agent examples/agents/reference.json --out ./run-01

# 4) evaluate YOUR agent
comacbench run packs/aviation-structures-v2 --agent ./my-agent.json --out ./run-02
```

Open `run-02/report.html` — fully offline (no CDN/fonts/telemetry), per-check drill-down, evidence paths, and a copy-paste resume command. Exit codes: `0` runnable/done · `2` material/identity/run error · `3` calibration failed.

## First-party packs

| Pack | Domain | Agent delivers | Harness verifies |
| --- | --- | --- | --- |
| `aviation-structures-v2` | FEA (CalculiX) | script generating `model.inp` | 6 input-contract checks → native `ccx` solve → reaction-force reconciliation; 8 fault negatives with named diagnoses |
| `aviation-cfd-step-v1` | CFD (OpenFOAM 10, pinned image) | script generating a full `case/` | mesh/boundary/residual/mass-balance gates → reattachment length re-derived from bottom-wall shear; 6 fault-negative classes |
| `aviation-core-v1` | mixed smoke (3 tasks) | calc script / data transform / ontology rules | end-to-end pipeline check incl. a real CalculiX solve |

Research attachments (Re=100/200/300 backward-step studies, 48 cases) enter via `python -m comacbench.admission` with SHA-256-bound manifests — **research evidence, not scorable tasks**.

## Agent protocol (v1)

One trusted local process per task · request arrives as one JSON on stdin (prompt, public assets + digests, `output_contract`, `limits`) · response is one JSON on stdout: `{"protocol":"comacbench.agent.v1","task_id":"...","answer":"<source code>"}` · logs to stderr. API keys stay in environment variables and never enter archives. `revision_files` + `identity_env` feed the resume identity. Full contract: [docs/aviation-quickstart.md](docs/aviation-quickstart.md).

## The research suite (31 integrated benchmarks, ~2.7k tasks)

Beyond packs, the repo carries the full research harness that produced them — five adapter families, eleven capability dimensions, hidden dynamic pools, and a four-arm (H0–H3) scaffold protocol:

| Dimension | Benchmarks (tasks) | Dimension | Benchmarks (tasks) |
| --- | --- | --- | --- |
| knowledge | cfdquery 90 · aeroengqa 80 · mechvqa 180 · litbench 60 | structures | calculix.fea_basic 21 |
| coding | scicode 52 · cfdcode 15 · pinnacle 3 + 6 public anchors | propulsion | pycycle 28 |
| cad_geometry | cadgen 22 · sketch_lite 15 | flight_control | gtm 25 + gtm_hard 17 |
| cfd | foam_basic 110 · superwing 100 · hilift 100 · cfdb 34 | mdo_design | aviary 27 |
| office | engtable 19 · awdoc 18 · awext 12 · ssb 25 | airworthiness | awcom 15 (+45 hidden pool) |

SSOT: [registry/registry.yaml](registry/registry.yaml) · licenses: [registry/license-notes.md](registry/license-notes.md) · latest self-assessment: [report/2026-09-11-dev-status-and-beta-readiness.md](report/2026-09-11-dev-status-and-beta-readiness.md)

## Repository layout

```
comacbench/        # the pack harness: validate / run / calibrate / evidence / admission + offline report
packs/             # first-party benchmark packs (portable directories)
runners/           # five adapter families + solver backends (calculix/openfoam/matlab) — no runner forks
contracts/         # task YAML contract reference
scoring/           # gate-before-score discipline, dimension rubric
tasks/  data/      # research suite: 2645 task YAMLs + mirrored datasets (PROVENANCE + sha256)
plugin/            # DSH host/client plugins (comac_* tools, workbench UI)
report/  results/  # dated evidence reports + frozen result trees (git history = freeze)
docs/              # specs, quickstart, roadmap, windows-handoff
```

## Contributing a pack

```bash
comacbench init ./my-pack    # copies a fully runnable example, not a placeholder
comacbench validate ./my-pack --out ./feedback   # field-level blockers + fixes
comacbench calibrate ./my-pack --out ./calib     # reference full-pass + negatives fire
```

Pipeline: **preflight → fix blockers → explicit calibration → engineering expert review → version freeze**. The first three are implemented; `publishable` stays `false` until human review. Guidelines: [docs/aviation-quickstart.md](docs/aviation-quickstart.md#贡献新的评测集) · roadmap: [docs/aviation-benchmark-roadmap.md](docs/aviation-benchmark-roadmap.md).

## Status & roadmap

Private development. v0.3.1 = B-series grading fixes + aviation plugin v1 (packs, agent protocol, evidence admission) + Windows cross-platform locks. Next gates (see the self-assessment above): scoring-credibility residuals → engineer 15-min onboarding field test → controlled beta (2 packs, CFD as research annex) → file-level data/ontology line → contribution isolation.

## License

TBD — private repository. Third-party mirrored datasets in `data/` carry per-source licenses recorded in [registry/license-notes.md](registry/license-notes.md); do not redistribute without clearing that matrix.

---

Lab notebook (original build log & roadmap): [docs/lab-notebook.md](docs/lab-notebook.md) · Windows handoff: [docs/windows-handoff.md](docs/windows-handoff.md)
