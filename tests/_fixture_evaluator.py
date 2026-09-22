"""测试用 evaluator fixture：从交付文件内容独立复算（artifacts.v1 判分侧资产示例）。

判分原则：
  - 只读 workspace 与 deliverables 声明；
  - 语义/数值级断言（CSV 解析后查行），不做字节比较；
  - 合法替代表达（列序不同、引号风格不同）等价接受。
"""
import csv
from pathlib import Path


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def evaluate(task, workspace: Path, deliverables: list[dict]) -> dict:
    checks = []
    by_kind = {d["kind"]: workspace / d["path"] for d in deliverables}

    rt = by_kind.get("result_table")
    if rt is None or not rt.is_file():
        checks.append({"name": "result_table_present", "passed": False,
                       "expected": "results.csv", "actual": "missing"})
    else:
        rows = _read_csv(rt)
        row = next((r for r in rows if r.get("part") == "P-01"), None)
        checks.append({
            "name": "qty_row_P-01",
            "passed": bool(row) and str(row.get("qty", "")).strip() == "2",
            "expected": "qty=2", "actual": row,
        })

    rl = by_kind.get("rejection_list")
    if rl is None or not rl.is_file():
        checks.append({"name": "rejection_list_present", "passed": False,
                       "expected": "rejected.csv", "actual": "missing"})
    else:
        rows = _read_csv(rl)
        ok = any(r.get("part") == "P-02" and r.get("reason") == "unit_missing"
                 for r in rows)
        checks.append({"name": "rejection_row_P-02", "passed": ok,
                       "expected": "P-02 rejected for unit_missing",
                       "actual": rows})

    return {"checks": checks, "summary": "fixture evaluator over file contents"}
