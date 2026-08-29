#!/usr/bin/env python3
"""pinnacle_helmholtz2d 冻结判分 loader（解析解参考）。

用法: python3 pinnacle_helmholtz2d.py <pred.npy>  → 末行 stdout = JSON {"rel_l2": x}
参考: u = sin(πx)sin(πy)，x/y = linspace(-1,1,101)（101×101，C 序 grid(ij)）。
"""
import json, sys
import numpy as np

def main() -> None:
    xs = np.linspace(-1.0, 1.0, 101)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    ref = (np.sin(np.pi * X) * np.sin(np.pi * Y)).ravel()
    pred = np.load(sys.argv[1])
    if pred.shape != ref.shape:
        raise SystemExit(f"shape mismatch: pred {pred.shape} vs ref {ref.shape}")
    if not np.isfinite(pred).all():
        raise SystemExit("pred has non-finite values")
    rel = float(np.linalg.norm(pred - ref) / np.linalg.norm(ref))
    print(json.dumps({"rel_l2": rel, "n": int(pred.size)}))

if __name__ == "__main__":
    main()
