import csv, json, os
from pathlib import Path
_c = Path(os.environ["WORKLOAD_CASE"]) if os.environ.get("WORKLOAD_CASE") else sorted(Path("inputs").rglob("*_case.json"))[0]
case = json.loads(_c.read_text(encoding="utf-8"))
w = Path.cwd(); (w/"outputs").mkdir(exist_ok=True)
rows = []
for r in case["rows"]:
    alt = r.get("altitude_m", r.get("altitude", 0))   # 负例：缺单位就猜 0/原值
    rows.append({"point": r["point"], "altitude_m": float(alt),
                 "mass_flow_kg_s": float(r["mass_flow_kg_s"])})
(w/"outputs"/"normalized.json").write_text(json.dumps({"case_id": case["case_id"], "rows": rows}), encoding="utf-8")
with (w/"outputs"/"run_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
    wr = csv.DictWriter(fh, fieldnames=["point","case_id","version"]); wr.writeheader()
    for r in rows: wr.writerow({"point": r["point"], "case_id": case["case_id"], "version": case.get("version","")})
(w/"outputs"/"exceptions.csv").write_text("point,reason_code,reason,detail\n", encoding="utf-8")
(w/"manifest.json").write_text(json.dumps({"protocol": "comacbench.artifacts.v1", "deliverables": [
  {"path": "outputs/normalized.json", "kind": "normalized"},
  {"path": "outputs/run_manifest.csv", "kind": "run_manifest"},
  {"path": "outputs/exceptions.csv", "kind": "exceptions"}]}), encoding="utf-8")
