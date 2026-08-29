#!/usr/bin/env python3
"""pinnacle_poisson1d 冻结判分 loader（解析解参考）。

用法: python3 pinnacle_poisson1d.py <pred.npy>  → 末行 stdout = JSON {"rel_l2": x}
参考: u = sin(x)，x = linspace(0, 2π, 256)。
"""
import json, sys
import numpy as np

def main() -> None:
    x = np.linspace(0.0, 2.0 * np.pi, 256)
    ref = np.sin(x)
    pred = np.load(sys.argv[1])
    if pred.shape != ref.shape:
        raise SystemExit(f"shape mismatch: pred {pred.shape} vs ref {ref.shape}")
    if not np.isfinite(pred).all():
        raise SystemExit("pred has non-finite values")
    rel = float(np.linalg.norm(pred - ref) / np.linalg.norm(ref))
    print(json.dumps({"rel_l2": rel, "n": int(pred.size)}))

if __name__ == "__main__":
    main()
