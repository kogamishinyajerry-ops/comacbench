"""foam_nmse.py — OpenFOAM 场 NMSE 判分（官方 nmse_report.py 语义，pyvista 实现）。

官方语义（FoamBench/nmse_report.py @3b46d30）：
- .foam 触点文件 + pv.OpenFOAMReader；
- GT 取末时刻，模型取最近时刻；
- 边界不一致时平移+缩放对齐（align_and_scale_mesh）；
- 场集 [U, p, rho, T]，双方都有才比；cell 数不一致时 GT 网格（删该场后）
  interpolate 到模型网格再 point_data_to_cell_data；
- NMSE = Σ(a-b)²/Σa²；任一场异常记 9999；聚合 = 场均值；
- 阈值（score_calculation.py）：<0.1→1.0，<0.3→0.5，else 0。

运行前提：pyvista（benchmarks/.venv）。属 grader 可信侧，不入沙箱。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pyvista as pv

FIELDS = ["U", "p", "rho", "T"]


def _touch_foam(directory: Path) -> Path:
    p = directory / (directory.name + ".foam")
    p.write_text("", encoding="utf-8")
    return p


def _align_and_scale(gt_mesh, meta_mesh):
    gt_bounds = np.array(gt_mesh[0].bounds).reshape(3, 2)
    meta_bounds = np.array(meta_mesh[0].bounds).reshape(3, 2)
    if np.allclose(gt_bounds, meta_bounds, atol=1e-6):
        return meta_mesh
    shift = gt_bounds[:, 0] - meta_bounds[:, 0]
    gt_size = gt_bounds[:, 1] - gt_bounds[:, 0]
    meta_size = meta_bounds[:, 1] - meta_bounds[:, 0]
    scaling = np.divide(gt_size, meta_size, out=np.ones_like(gt_size),
                        where=meta_size != 0)
    aligned = meta_mesh[0].copy()
    aligned.points = (aligned.points - meta_bounds[:, 0]) * scaling + gt_bounds[:, 0]
    return [aligned]


def calculate_nmse(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.sum(np.asarray(a) ** 2))
    return float(np.sum((np.asarray(a) - np.asarray(b)) ** 2) / denom) if denom else 9999.0


def evaluate_nmse(gt_dir: Path, llm_dir: Path) -> tuple[float, dict[str, float]]:
    """返回 (聚合 NMSE, 逐场明细)。读失败/无公共场 => (9999, {})。"""
    gt_foam = _touch_foam(Path(gt_dir))
    llm_foam = _touch_foam(Path(llm_dir))
    try:
        gt_reader = pv.OpenFOAMReader(gt_foam)
        last_time = gt_reader.time_values[-1]
        gt_reader.set_active_time_value(last_time)
        meta_reader = pv.OpenFOAMReader(llm_foam)
        closest = min(meta_reader.time_values, key=lambda x: abs(x - last_time))
        meta_reader.set_active_time_value(closest)
    except Exception:
        return 9999.0, {}

    gt_mesh = gt_reader.read()
    meta_mesh = meta_reader.read()
    try:
        meta_mesh = _align_and_scale(gt_mesh, meta_mesh)
    except Exception:
        return 9999.0, {}

    per_field: dict[str, float] = {}
    scores: list[float] = []
    for field in FIELDS:
        if field in gt_mesh[0].cell_data and field in meta_mesh[0].cell_data:
            try:
                if gt_mesh[0].n_cells != meta_mesh[0].n_cells:
                    og = gt_mesh.copy()
                    if field in og[0].point_data:
                        del og[0].point_data[field]
                    if field in og[0].cell_data:
                        del og[0].cell_data[field]
                    proj = og[0].interpolate(meta_mesh[0], sharpness=0.1, n_points=50)
                    proj = proj.point_data_to_cell_data()
                    meta_data = proj[field]
                else:
                    meta_data = meta_mesh[0][field]
                gt_data = gt_mesh[0][field]
                s = calculate_nmse(gt_data, meta_data)
            except Exception:
                s = 9999.0
            per_field[field] = round(s, 6)
            scores.append(s)
    if not scores:
        return 9999.0, {}
    return float(np.mean(scores)), per_field


def nmse_to_score(nmse: float) -> float:
    """官方阈值映射：<0.1→1.0；<0.3→0.5；else 0。"""
    if nmse < 0.1:
        return 1.0
    if nmse < 0.3:
        return 0.5
    return 0.0
