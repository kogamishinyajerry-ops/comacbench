#!/usr/bin/env python3
"""UniFoil transi 系数层抽取（可重放）。

用法: python3 extract_from_zip.py <airfoil_data_from_simulations.zip> <out_csv>
源: HF rkanchi/UniFoil transi/airfoil_data_from_simulations.zip (342,859,366B,
    sha256 ac2ea66c96f30ddf680dcba1550a4bc05b4810c5386de9bdbf7cf20940b1d84a)
格式: 每 case 一个 _analysis.csv = 键值头(Airfoil/Case Number/Mach/AoA/Reynolds)
      + CL,CD 单行数据（float 宽容解析，科学计数法兼容）。
"""
import csv
import sys
import zipfile
from pathlib import Path


def main() -> None:
    zp, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows, bad = [], 0
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            if not n.endswith("_analysis.csv"):
                continue
            try:
                text = z.read(n).decode("utf-8", "replace")
                kv, clcd = {}, None
                for ln in text.splitlines():
                    parts = ln.strip().split(",")
                    if not parts[0]:
                        continue
                    if parts[0] in ("Airfoil", "Case Number", "Mach", "AoA", "Reynolds"):
                        kv[parts[0]] = parts[1]
                    elif parts[0] == "CL":
                        continue
                    elif len(parts) == 2:
                        try:
                            clcd = (float(parts[0]), float(parts[1]))
                        except ValueError:
                            pass
                if clcd is None or len(kv) < 5:
                    bad += 1
                    continue
                rows.append({
                    "airfoil": int(float(kv["Airfoil"])),
                    "case": int(float(kv["Case Number"])),
                    "mach": float(kv["Mach"]), "aoa_deg": float(kv["AoA"]),
                    "reynolds": float(kv["Reynolds"]),
                    "cl": clcd[0], "cd": clcd[1],
                    "case_file": n.split("/")[-1],
                })
            except Exception:
                bad += 1
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"rows={len(rows)} bad={bad} -> {out}")


if __name__ == "__main__":
    main()
