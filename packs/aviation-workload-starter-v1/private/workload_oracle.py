"""workload oracle（参考实现）：从 assets 工况文件写出全部交付物。"""
import csv
import json
import os
from pathlib import Path

env_case = os.environ.get("WORKLOAD_CASE")
if env_case:
    case_path = Path(env_case)
else:
    cands = sorted(Path("inputs").rglob("*_case.json")) if Path("inputs").is_dir() else []
    case_path = cands[0] if cands else None
if case_path is None:
    raise SystemExit("no case file found (WORKLOAD_CASE or inputs/)")
case = json.loads(case_path.read_text(encoding="utf-8"))
w = Path.cwd()
(w / "outputs").mkdir(exist_ok=True)

rows_out = []
exc = []
seen = {}
for r in case.get("rows", []):
    pt = r.get("point")
    if "altitude_m" not in r and "altitude" in r:
        exc.append({"point": pt, "reason": "missing_unit:altitude",
                    "detail": "高度缺单位，需澄清后处理"})
        continue
    if pt in seen:
        exc.append({"point": pt, "reason": "conflicting_duplicate",
                    "detail": f"{pt} 两行数值矛盾，需人工裁决"})
        rows_out = [x for x in rows_out if x["point"] != pt]
        continue
    seen[pt] = r
    rows_out.append({"point": pt, "altitude_m": float(r["altitude_m"]),
                     "mass_flow_kg_s": float(r["mass_flow_kg_s"]),
                     "source_version": case.get("version")})

for s in case.get("stale_results", []):
    exc.append({"point": s["point"], "reason": "stale_output",
                "detail": "旧修订结果，不进入本次运行清单"})

(w / "outputs" / "normalized.json").write_text(
    json.dumps({"case_id": case["case_id"], "rows": rows_out},
               ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
with (w / "outputs" / "run_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=["point", "case_id", "version"])
    wr.writeheader()
    for r in rows_out:
        wr.writerow({"point": r["point"], "case_id": case["case_id"],
                     "version": case.get("version")})
with (w / "outputs" / "exceptions.csv").open("w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=["point", "reason", "detail"])
    wr.writeheader()
    for e in exc:
        wr.writerow(e)
(w / "manifest.json").write_text(json.dumps(
    {"protocol": "comacbench.artifacts.v1",
     "deliverables": [
         {"path": "outputs/normalized.json", "kind": "normalized"},
         {"path": "outputs/run_manifest.csv", "kind": "run_manifest"},
         {"path": "outputs/exceptions.csv", "kind": "exceptions"}]},
    ensure_ascii=False, indent=1), encoding="utf-8")
print("deliverables written")
