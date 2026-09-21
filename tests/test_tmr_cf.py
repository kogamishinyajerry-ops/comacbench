"""tmr_cf.py 契约测试（纯读数，不启动 STAR-CCM+，不占许可座席）。

覆盖两件事：
1. 残差表解析 + 收敛门——**必须能区分「残差收敛」与「k 方程振荡」**，
   后者正是 2026-09-21 细网格 Cf 出现「准层流」假象的根因；
2. TMR 参考/导出场 Cf 比对——分 bin 偏差 + 插值逐点偏差 + 误差带评分。
"""
import math
import tempfile
import unittest
from pathlib import Path

from runners.tmr_cf import (
    CfComparison,
    ConvergenceVerdict,
    cf_from_tau,
    compare_cf,
    convergence_report,
    dev_band_score,
    read_daten,
    read_reference,
    residual_history,
)

HEADER = ("     Iteration     Continuity     X-momentum     Y-momentum     Z-momentum"
          "         Energy            Tke            Sdr ")


def _row(it: int, cont: float, xmom: float, tke: float, sdr: float) -> str:
    return (f"    {it:>6}   {cont:.6e}   {xmom:.6e}   1.000000e-03   3.000000e-05"
            f"   0.000000e+00   {tke:.6e}   {sdr:.6e} ")


def _log(rows) -> str:
    out = [HEADER]
    for it, cont, xmom, tke, sdr in rows:
        out.append(_row(it, cont, xmom, tke, sdr))
    return "\n".join(out) + "\n"


class ResidualHistoryTests(unittest.TestCase):
    def test_header_driven_column_mapping(self):
        text = _log([(1, 1.0, 1.0, 1.0, 1.0), (2, 1e-2, 3e-1, 4e-1, 5e-1)])
        rows = residual_history(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].iteration, 1)
        self.assertAlmostEqual(rows[1].get("continuity"), 1e-2)
        self.assertAlmostEqual(rows[1].get("x_momentum"), 3e-1)
        self.assertAlmostEqual(rows[1].get("tke"), 4e-1)

    def test_repeated_headers_do_not_break_parsing(self):
        text = _log([(1, 1e-1, 1e-1, 1e-1, 1e-1)]) + HEADER + "\n" + _row(2, 1e-2, 1e-2, 1e-2, 1e-2)
        rows = residual_history(text)
        self.assertEqual([r.iteration for r in rows], [1, 2])

    def test_non_numeric_and_ragged_lines_ignored(self):
        text = HEADER + "\n" + "macro done\n" + _row(1, 1e-3, 1e-3, 1e-3, 1e-3) + "\n   7  1e-3\n"
        rows = residual_history(text)
        self.assertEqual(len(rows), 1)

    def test_empty_log_returns_empty(self):
        self.assertEqual(residual_history("no table here\n"), [])


class ConvergenceGateTests(unittest.TestCase):
    def test_decaying_residuals_pass(self):
        rows = [(i, 10.0 ** (-2 - i / 100.0), 1e-3, 0.60 * (0.999 ** i), 2.6e-7)
                for i in range(1, 1001)]
        v = convergence_report(_log(rows), window=300)
        self.assertIsInstance(v, ConvergenceVerdict)
        self.assertTrue(v.ok, v.summary())
        self.assertTrue(v.turbulence_stationary)
        self.assertEqual(v.n_iter, 1000)

    def test_rising_turbulence_residual_fails_as_nonstationary(self):
        """复刻 273x193 实测：Tke 在窗内由 0.577 回升到 0.826（+43%）。"""
        settled = [(i, 1.74e-6, 1.32e-3, 0.40, 1.05e-6) for i in range(1, 701)]
        rising = [(700 + k, 1.74e-6, 1.32e-3, 0.577 + 0.249 * k / 299.0, 1.05e-6)
                  for k in range(1, 301)]
        v = convergence_report(_log(settled + rising), window=300)
        self.assertFalse(v.ok)
        self.assertFalse(v.turbulence_stationary)
        self.assertTrue(any("non-stationary" in r for r in v.reasons), v.reasons)

    def test_bad_continuity_fails_gate(self):
        rows = [(i, 5e-3, 1e-3, 0.5 * (0.999 ** i), 1e-7) for i in range(1, 401)]
        v = convergence_report(_log(rows), window=300)
        self.assertFalse(v.ok)
        self.assertFalse(v.continuity_ok)
        self.assertTrue(any("continuity" in r for r in v.reasons))

    def test_momentum_above_tolerance_fails_gate(self):
        rows = [(i, 1e-6, 5e-1, 0.5 * (0.999 ** i), 1e-7) for i in range(1, 401)]
        v = convergence_report(_log(rows), window=300, momentum_tol=1e-2)
        self.assertFalse(v.ok)
        self.assertFalse(v.momentum_ok)

    def test_no_table_fails_closed(self):
        v = convergence_report("server disconnected\n")
        self.assertFalse(v.ok)
        self.assertEqual(v.n_iter, 0)
        self.assertEqual(v.reasons, ["no residual table found"])

    def test_drift_reported_for_turbulence_columns(self):
        rows = [(i, 1e-6, 1e-3, 0.6 * (0.999 ** i), 1e-7) for i in range(1, 401)]
        v = convergence_report(_log(rows), window=300)
        self.assertIn("tke", v.drift)
        self.assertLess(v.drift["tke"], 0.0)


class DatanAndReferenceTests(unittest.TestCase):
    def _write(self, text: str) -> Path:
        d = Path(tempfile.mkdtemp())
        p = d / "sample.daten"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: p.unlink(missing_ok=True))
        return p

    def test_read_daten_parses_and_sorts_by_x(self):
        p = self._write(
            "# Shell Id, Centroid[X], Wall Shear Stress X, Wall Shear Stress Y, Wall Shear Stress Z\n"
            "         3       0.50000000000000       2.00000000000000       0.0       0.0\n"
            "         1       1.50000000000000       1.00000000000000       0.0       0.0\n")
        x, tau = read_daten(p)
        self.assertEqual(x, [0.5, 1.5])
        self.assertEqual(tau, [2.0, 1.0])

    def test_read_daten_rejects_empty(self):
        p = self._write("# only a header\n")
        with self.assertRaises(ValueError):
            read_daten(p)

    def test_read_reference_skips_variables_and_zone(self):
        d = Path(tempfile.mkdtemp())
        p = d / "ref.dat"
        p.write_text('variables="x","cf"\nzone, t="CFL3D"\n'
                     " -3.228320479E-01 0.000000000E+00\n"
                     "  1.000000050E-03 1.553966380E-02\n", encoding="utf-8")
        self.addCleanup(lambda: p.unlink(missing_ok=True))
        x, cf = read_reference(p)
        self.assertAlmostEqual(x[0], -0.3228320479)
        self.assertAlmostEqual(cf[1], 1.553966380e-02)

    def test_read_reference_accepts_fortran_d_exponent(self):
        d = Path(tempfile.mkdtemp())
        p = d / "ref.dat"
        p.write_text('variables="x","cf"\n1.5D-03  2.5D-02\n', encoding="utf-8")
        self.addCleanup(lambda: p.unlink(missing_ok=True))
        x, cf = read_reference(p)
        self.assertAlmostEqual(x[0], 1.5e-3)
        self.assertAlmostEqual(cf[0], 2.5e-2)


class MultiZoneReferenceTests(unittest.TestCase):
    """TMR 的 Cf 参考文件常把多个求解器装在同一个 .dat 里（实测 cf_plate_sstv.dat
    同时含 CFL3D 与 FUN3D）。按行拼接会得到一条**混合曲线**——必须 fail-closed。"""

    TWO_ZONE = ('variables="x","cf"\n'
                'zone, t="CFL3D"\n'
                " 0.5  2.0E-03\n 1.0  1.8E-03\n"
                'zone, t="FUN3D"\n'
                " 0.5  1.9E-03\n 1.0  1.7E-03\n")

    def _write(self, text: str) -> Path:
        d = Path(tempfile.mkdtemp())
        p = d / "twozone.dat"
        p.write_text(text, encoding="utf-8")
        self.addCleanup(lambda: p.unlink(missing_ok=True))
        return p

    def test_reference_zones_lists_names_in_order(self):
        from runners.tmr_cf import reference_zones
        self.assertEqual(reference_zones(self._write(self.TWO_ZONE)), ["CFL3D", "FUN3D"])

    def test_read_reference_without_zone_fails_closed(self):
        p = self._write(self.TWO_ZONE)
        with self.assertRaisesRegex(ValueError, "必须用 zone="):
            read_reference(p)

    def test_read_reference_selects_zone_by_index_and_name(self):
        p = self._write(self.TWO_ZONE)
        for sel in (0, "CFL3D"):
            x, cf = read_reference(p, zone=sel)
            self.assertEqual(len(x), 2)
            self.assertAlmostEqual(cf[0], 2.0e-3)
        x, cf = read_reference(p, zone="FUN3D")
        self.assertAlmostEqual(cf[0], 1.9e-3)

    def test_read_reference_rejects_unknown_zone(self):
        p = self._write(self.TWO_ZONE)
        with self.assertRaisesRegex(ValueError, "不存在"):
            read_reference(p, zone="SU2")

    def test_mixed_reference_would_bias_the_comparison(self):
        """把两 zone 混起来的后果：插值取到邻近的另一个 zone 值 -> 偏差被污染。"""
        p = self._write(self.TWO_ZONE)
        x_m, cf_m = [0.5, 1.0], [2.0e-3, 1.8e-3]
        cfl = read_reference(p, zone="CFL3D")
        clean = compare_cf(x_m, cf_m, *cfl, x_min=0.0, x_max=2.0, n_bins=2)
        self.assertAlmostEqual(clean.mean_dev_pct, 0.0, places=9)


class CfTests(unittest.TestCase):
    def test_cf_from_tau_uses_dynamic_pressure(self):
        q = 0.5 * 1.18415 * 50.0 ** 2
        self.assertAlmostEqual(cf_from_tau([q, 2 * q])[0], 1.0)
        self.assertAlmostEqual(cf_from_tau([q, 2 * q])[1], 2.0)

    def test_compare_cf_identical_data_gives_zero_deviation(self):
        x = [i * 0.05 for i in range(1, 39)]
        cf = [0.06 / (i ** 0.2) for i in range(1, 39)]
        r = compare_cf(x, cf, x, cf, x_min=0.05, x_max=1.91, n_bins=4)
        self.assertIsInstance(r, CfComparison)
        self.assertAlmostEqual(r.mean_dev_pct, 0.0, places=9)
        self.assertAlmostEqual(r.median_dev_pct, 0.0, places=9)
        self.assertEqual(r.n_model, len(x))
        self.assertAlmostEqual(r.max_abs_dev_pct, 0.0, places=9)

    def test_compare_cf_detects_systematic_undershoot(self):
        x = [i * 0.05 for i in range(1, 39)]
        ref = [0.06 / (i ** 0.2) for i in range(1, 39)]
        model = [c * 0.8 for c in ref]
        r = compare_cf(x, model, x, ref, x_min=0.05, x_max=1.91, n_bins=4)
        self.assertAlmostEqual(r.mean_dev_pct, -20.0, places=6)
        for b in r.bins:
            self.assertAlmostEqual(b.dev_pct, -20.0, places=6)

    def test_compare_cf_skips_reference_zeros_below_floor(self):
        """参考在 x<0 处 cf=0（对称段），不得被当成 100% 偏差纳入统计。"""
        x_ref = [-0.3, -0.1, 0.5, 1.0]
        cf_ref = [0.0, 0.0, 0.002, 0.002]
        x_m = [0.5, 1.0]
        cf_m = [0.002, 0.002]
        r = compare_cf(x_m, cf_m, x_ref, cf_ref, x_min=0.0, x_max=2.0, n_bins=2)
        self.assertEqual(r.n_points, 2)
        self.assertAlmostEqual(r.mean_dev_pct, 0.0, places=9)

    def test_compare_cf_raises_when_no_model_points_in_window(self):
        with self.assertRaises(ValueError):
            compare_cf([3.0], [0.002], [0.5, 1.0], [0.002, 0.002], x_min=0.0, x_max=2.0)

    def test_compare_cf_bins_hold_model_point_counts(self):
        x = [i * 0.1 for i in range(1, 20)]
        cf = [0.002] * 19
        r = compare_cf(x, cf, [0.5, 1.0], [0.002, 0.002], x_min=0.0, x_max=2.0, n_bins=4)
        self.assertEqual(sum(b.n for b in r.bins), len(x))

    def test_dev_band_score_thresholds(self):
        band = [(10.0, 1.0), (20.0, 0.5), (40.0, 0.2)]
        self.assertEqual(dev_band_score(-17.4, band), 0.5)
        self.assertEqual(dev_band_score(5.0, band), 1.0)
        self.assertEqual(dev_band_score(41.0, band), 0.0)
        self.assertEqual(dev_band_score(math.nan if False else -20.0, band), 0.5)


class RichardsonGciTests(unittest.TestCase):
    """GCI 外推：先在合成解上验证阶次反推正确，再覆盖两个拒绝路径。"""

    def test_recovers_second_order_and_exact_value(self):
        from runners.tmr_cf import richardson_gci
        a, b = 0.0022, 0.0003
        fine, medium, coarse = a + b * 0.25 ** 2, a + b * 0.5 ** 2, a + b * 1.0 ** 2
        r = richardson_gci([fine, medium, coarse], (2.0, 2.0))
        self.assertTrue(r.ok)
        self.assertAlmostEqual(r.observed_order, 2.0, places=2)
        self.assertAlmostEqual(r.extrapolated, a, places=5)
        self.assertGreater(r.gci_fine, 0.0)
        self.assertIn("p=", r.summary())

    def test_oscillatory_convergence_is_refused(self):
        from runners.tmr_cf import richardson_gci
        # 273 档式的非单调行为：中间档比粗细两档都低
        r = richardson_gci([0.0010, 0.0020, 0.0012], (2.0, 2.0))
        self.assertFalse(r.ok)
        self.assertTrue(r.oscillatory)
        self.assertIn("n/a", r.summary())

    def test_identical_values_reported_not_crashed(self):
        from runners.tmr_cf import richardson_gci
        r = richardson_gci([0.002, 0.002, 0.002], (2.0, 2.0))
        self.assertFalse(r.ok)
        self.assertFalse(r.oscillatory)
        self.assertIn("完全相同", r.reason)

    def test_requires_exactly_three_solutions(self):
        from runners.tmr_cf import richardson_gci
        with self.assertRaises(ValueError):
            richardson_gci([0.001, 0.002], (2.0, 2.0))

    def test_gci_direction_for_monotone_undershoot(self):
        """模型随网格加密单调逼近参考（粗网格偏低）：外推值应高于细网格值。"""
        from runners.tmr_cf import richardson_gci
        r = richardson_gci([0.00205, 0.00190, 0.00160], (2.0, 2.0))
        self.assertTrue(r.ok)
        self.assertGreater(r.extrapolated, 0.00205)


if __name__ == "__main__":
    unittest.main()
