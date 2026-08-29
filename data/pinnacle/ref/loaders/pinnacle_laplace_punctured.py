#!/usr/bin/env python3
"""pinnacle_laplace_punctured 冻结判分 loader。

用法: python3 pinnacle_laplace_punctured.py <pred.npy>  → 末行 stdout = JSON {"rel_l2": x}
参考: data/pinnacle/ref/laplace_ref_u.npy（poisson_classic.dat 第 3 列派生）。
"""
import json, sys
import numpy as np

def main() -> None:
    ref = np.load("data/pinnacle/ref/laplace_ref_u.npy")  # (1255,)
    pred = np.load(sys.argv[1])
    if pred.shape != ref.shape:
        raise SystemExit(f"shape mismatch: pred {pred.shape} vs ref {ref.shape}")
    if not np.isfinite(pred).all():
        raise SystemExit("pred has non-finite values")
    rel = float(np.linalg.norm(pred - ref) / np.linalg.norm(ref))
    print(json.dumps({"rel_l2": rel, "n": int(pred.size)}))

if __name__ == "__main__":
    main()
