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
    QoiVerdict,
    cf_from_tau,
    compare_cf,
    convergence_report,
    dev_band_score,
    fully_turbulent_mean_cf,
    qoi_stationary,
    read_daten,
    read_reference,
    reference_zones,
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

    # ---- ok 与 strict_ok 必须能分开（2026-09-21 实测教训）----

    def test_still_drifting_turbulence_passes_ok_but_fails_strict(self):
        """复刻 273x193@6000：Tke 在最后 300 步仍净降 -10.44%（还差很远）。

        本门只抓「回升」，所以 ``ok`` 仍为 True——这正是它的设计本意；
        GCI 前必须叠加 ``strict_ok``，否则会把「还在往下走」的解当收敛解外推。
        """
        decay = 0.999632                     # 300 步净 -10.44%，对齐实测 -10.46%
        rows = [(i, 1.34e-7, 1.30e-3, 0.2767 / decay ** (6000 - i), 4.81e-7)
                for i in range(5701, 6001)]
        v = convergence_report(_log(rows), window=300, decay_tol=0.10)
        self.assertTrue(v.ok, v.summary())
        self.assertTrue(v.turbulence_stationary)
        self.assertFalse(v.drift_ok)
        self.assertFalse(v.strict_ok)
        self.assertLess(v.drift["tke"], -10.0)
        self.assertTrue(any("still drifting" in r for r in v.reasons), v.reasons)
        self.assertIn("still-drift", v.summary())

    def test_settled_turbulence_is_strict_ok(self):
        """复刻 137x97@6000：Tke 窗漂移 -0.02%（已趴平），Sdr -5.5%（在 10% 容差内）。"""
        sdr = 0.999812                       # 300 步净 -5.48%，对齐实测
        rows = [(i, 2.81e-7, 2.40e-3, 0.1158, 6.653e-8 / sdr ** (6000 - i))
                for i in range(5701, 6001)]
        v = convergence_report(_log(rows), window=300, decay_tol=0.10)
        self.assertTrue(v.ok, v.summary())
        self.assertTrue(v.drift_ok)
        self.assertTrue(v.strict_ok)
        self.assertAlmostEqual(v.drift["sdr"], -5.48, delta=0.1)

    def test_decay_tol_none_disables_still_drift_check(self):
        decay = 0.999632
        rows = [(i, 1.34e-7, 1.30e-3, 0.2767 / decay ** (6000 - i), 4.81e-7)
                for i in range(5701, 6001)]
        v = convergence_report(_log(rows), window=300, decay_tol=None)
        self.assertTrue(v.strict_ok)
        self.assertTrue(v.drift_ok)
        self.assertIsNone(v.decay_tol)


class QoiStationarityTests(unittest.TestCase):
    """QoI 平稳性判据——湍流残差量级不可靠时的主收敛判据。"""

    def test_settled_series_passes(self):
        v = qoi_stationary([0.002480, 0.002503, 0.002512, 0.0025145, 0.0025149],
                           tol_pct=1.0, window=3)
        self.assertIsInstance(v, QoiVerdict)
        self.assertTrue(v.ok, v.summary())
        self.assertEqual(v.n, 5)

    def test_still_rising_series_fails(self):
        """复刻 273x193 的 Cf 单调攀升：每 1000 步 +4% 左右，远未停住。"""
        v = qoi_stationary([0.002200, 0.002320, 0.002440, 0.002514, 0.002600],
                           tol_pct=1.0, window=3)
        self.assertFalse(v.ok)
        self.assertIn("增量", v.reason)

    def test_too_few_increments_fails_closed(self):
        v = qoi_stationary([0.0024, 0.0025], tol_pct=1.0, window=3)
        self.assertFalse(v.ok)
        self.assertIn("有效增量", v.reason)

    def test_net_drift_reported_even_when_passing(self):
        v = qoi_stationary([0.0030, 0.0030, 0.0030, 0.0030], tol_pct=1.0, window=3)
        self.assertTrue(v.ok)
        self.assertAlmostEqual(v.drift_pct, 0.0, places=6)

    def test_zero_baseline_reports_undefined_increments(self):
        """全零 QoI（τ 崩塌）不得被当成「平稳通过」。"""
        v = qoi_stationary([0.0, 0.0, 0.0, 0.0], tol_pct=1.0, window=3)
        self.assertFalse(v.ok)
        self.assertIn("有效增量", v.reason)

    def test_empty_series_fails_closed(self):
        v = qoi_stationary([], tol_pct=1.0, window=3)
        self.assertFalse(v.ok)
        self.assertIn("空序列", v.reason)


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


class FieldSanityTests(unittest.TestCase):
    """场侧 sanity：从二维切片反推 nu，并检查算例是否真的跑在它自称的 Re 上。

    这条门存在的理由（2026-09-21 实测）：写的是「U=50 / nu=1e-5 -> Re=5e6」，
    但反推得 nu=1.56659e-5（= STAR-CCM+ 默认空气 mu/rho），实际 Re_unit=3.19e6，
    比 TMR 目标低 36%。**残差门和 Cf 门都发现不了这种口径错误，只有场侧反推能。**
    """

    NU = 1.56659e-05

    def _slice(self, specs, *, nu=NU, header=None):
        """specs: (x, z, k, tvr, u, w) -> 自动派生 omega = k/(nu*tvr)。"""
        hdr = header or ["Shell Id", "Centroid[X]", "Centroid[Z]",
                         "Specific Dissipation Rate", "Turbulent Kinetic Energy",
                         "Turbulent Viscosity Ratio", "Velocity[i]", "Velocity[k]"]
        lines = ["# " + ", ".join(hdr)]
        for i, (x, z, k, tvr, u, w) in enumerate(specs, start=1):
            om = k / (nu * tvr)
            vals = {"Shell Id": f"{i}", "Centroid[X]": f"{x:.12f}",
                    "Centroid[Z]": f"{z:.12e}",
                    "Specific Dissipation Rate": f"{om:.12e}",
                    "Turbulent Kinetic Energy": f"{k:.12e}",
                    "Turbulent Viscosity Ratio": f"{tvr:.12e}",
                    "Velocity[i]": f"{u:.6f}", "Velocity[k]": f"{w:.6e}"}
            lines.append("  " + "  ".join(vals[c] for c in hdr))
        p = Path(tempfile.mkdtemp()) / "slice.daten"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.addCleanup(lambda: p.unlink(missing_ok=True))
        return p

    def test_read_field_slice_looks_up_columns_by_name(self):
        from runners.tmr_cf import read_field_slice
        # 列序被打乱，且多余列夹杂其中——必须按名字取值
        hdr = ["Turbulent Kinetic Energy", "Centroid[X]", "Velocity[i]", "Centroid[Z]",
               "Specific Dissipation Rate", "Turbulent Viscosity Ratio", "Velocity[k]"]
        p = self._slice([(0.5, 1.0e-6, 0.25, 12.0, 48.0, 1.0e-3)], header=hdr)
        rows = read_field_slice(p)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0].x, 0.5)
        self.assertAlmostEqual(rows[0].z, 1.0e-6)
        self.assertAlmostEqual(rows[0].k, 0.25)
        self.assertAlmostEqual(rows[0].tvr, 12.0)
        self.assertAlmostEqual(rows[0].u, 48.0)

    def test_recovers_nu_and_re_unit_from_self_consistent_slice(self):
        from runners.tmr_cf import field_sanity, read_field_slice
        p = self._slice([
            (1.90, 9.7e-1, 0.0299, 8.17, 50.000, 0.0),      # 出口远场
            (0.001, 2.78e-3, 89.7, 617.0, 20.7, 0.0),        # 板前缘近壁
            (1.00, 5.0e-7, 1.0e-5, 1.0e-3, 0.3, 0.0),        # 贴壁
        ])
        s = field_sanity(read_field_slice(p), u_inf=50.0, re_target=3.19e6)
        self.assertTrue(s.ok, s.reasons)
        self.assertAlmostEqual(s.nu_median / self.NU, 1.0, places=4)
        self.assertLess(s.nu_spread_pct, 1.0e-6)
        self.assertAlmostEqual(s.re_unit, 50.0 / self.NU, places=2)

    def test_re_unit_mismatch_is_caught_and_fix_suggested(self):
        """U=50 + nu=1.5666e-5 -> Re_unit=3.19e6, 距 5e6 目标 -36%。"""
        from runners.tmr_cf import field_sanity, read_field_slice
        p = self._slice([(1.0, 9.7e-1, 0.359, 9.97, 50.0, 0.0),
                         (1.0, 5.0e-7, 1.0e-5, 1.0e-3, 0.3, 0.0)])
        s = field_sanity(read_field_slice(p), u_inf=50.0, re_target=5.0e6)
        self.assertFalse(s.ok)
        self.assertTrue(s.nu_consistent)   # 场本身自洽，是 Re 口径错了
        self.assertLess(s.re_gap_pct, -30.0)
        self.assertIn("Re_unit", s.reasons[0])
        self.assertIn("78.3", s.reasons[0])  # 建议的修正速度 5e6*nu

    def test_re_check_can_be_skipped(self):
        from runners.tmr_cf import field_sanity, read_field_slice
        p = self._slice([(1.0, 9.7e-1, 0.359, 9.97, 50.0, 0.0),
                         (1.0, 5.0e-7, 1.0e-5, 1.0e-3, 0.3, 0.0)])
        s = field_sanity(read_field_slice(p), u_inf=50.0, re_target=0.0)
        self.assertTrue(s.ok, s.reasons)
        self.assertTrue(math.isnan(s.re_gap_pct))

    def test_inconsistent_nu_is_flagged(self):
        """同一片场里 nu 差 10 倍 => 场不自洽，必须 fail-closed。"""
        from runners.tmr_cf import field_sanity, read_field_slice
        rows = [(1.0, 9.7e-1, 0.359, 9.97, 50.0, 0.0)] * 5
        rows.append((0.5, 5.0e-7, 0.36, 99.7, 50.0, 0.0))
        # 用同一个 nu 派生 omega，再把其中一行的 omega 人为改坏
        p = self._slice(rows)
        text = p.read_text(encoding="utf-8").replace("9.970000000000e+01", "1.000000000000e+04")
        p.write_text(text, encoding="utf-8")
        s = field_sanity(read_field_slice(p), u_inf=50.0, re_target=0.0)
        self.assertFalse(s.ok)
        self.assertFalse(s.nu_consistent)
        self.assertGreater(s.nu_spread_pct, 2.0)

    def test_tvr_contrast_reported(self):
        from runners.tmr_cf import field_sanity, read_field_slice
        p = self._slice([
            (1.9, 9.7e-1, 0.0299, 10.0, 50.0, 0.0),    # 远场 mu_t/mu = 10
            (0.001, 1.0e-6, 89.7, 600.0, 20.7, 0.0),   # 前缘近壁 600
        ])
        s = field_sanity(read_field_slice(p), u_inf=50.0, re_target=0.0)
        self.assertAlmostEqual(s.tvr_far, 10.0, places=6)
        self.assertAlmostEqual(s.tvr_near_max, 600.0, places=6)
        self.assertAlmostEqual(s.tvr_contrast, 60.0, places=6)
        self.assertAlmostEqual(s.tvr_max, 600.0, places=6)
        self.assertAlmostEqual(s.k_max, 89.7, places=6)

    def test_empty_slice_fails_closed(self):
        from runners.tmr_cf import field_sanity
        s = field_sanity([], u_inf=50.0, re_target=5.0e6)
        self.assertFalse(s.ok)
        self.assertIn("空切片", s.reasons)


if __name__ == "__main__":
    unittest.main()
