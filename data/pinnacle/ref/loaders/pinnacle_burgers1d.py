#!/usr/bin/env python3
"""pinnacle_burgers1d 冻结判分 loader（cfdb qoi_script 同款协议）。

用法: python3 pinnacle_burgers1d.py <pred.npy>  → 末行 stdout = JSON {"rel_l2": x}
参考: data/pinnacle/ref/burgers1d.dat（COMSOL，% 注释；101 x × [t=0]+10 时刻列）。
纯 stdlib+numpy；形状/有限值不符退出非零，绝不编造数值。
"""
import json, sys
import numpy as np

def main() -> None:
    ref = np.loadtxt("data/pinnacle/ref/burgers1d.dat", comments="%")[:, 2:]  # (101,10)，剔除 t=0（IC 列）
    pred = np.load(sys.argv[1])
    if pred.shape != ref.shape:
        raise SystemExit(f"shape mismatch: pred {pred.shape} vs ref {ref.shape}")
    if not np.isfinite(pred).all():
        raise SystemExit("pred has non-finite values")
    rel = float(np.linalg.norm(pred - ref) / np.linalg.norm(ref))
    print(json.dumps({"rel_l2": rel, "n": int(pred.size)}))

if __name__ == "__main__":
    main()
