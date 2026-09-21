"""starccm.py 执行后端契约测试（不启动 STAR-CCM+，只验证接口与失败路径）。

纪律对齐 test_cfd_step_contract.py：负例必须命中预期失败信号；
真求解冒烟（批处理通道+许可）另行在环境就绪时以 headless 实测收口，
不在单元测试层占许可座席。
"""
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch


class StarCCMBinaryTests(unittest.TestCase):
    def test_binary_located_by_install_probe(self):
        from runners.solvers.starccm import starccm_binary, _CANDIDATE_BINS
        # 本机（Windows dev 终端）应命中安装探测路径
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("STARCCM_BIN", None)
            self.assertEqual(starccm_binary(), _CANDIDATE_BINS[0])

    def test_env_override_wins(self):
        from runners.solvers.starccm import starccm_binary
        fake = Path(tempfile.gettempdir()) / "fake-starccm.bat"
        fake.write_text("@echo off")
        self.addCleanup(fake.unlink)
        with patch.dict(os.environ, {"STARCCM_BIN": str(fake)}):
            self.assertEqual(starccm_binary(), str(fake))

    def test_missing_binary_raises_with_actionable_hint(self):
        from runners.solvers.starccm import starccm_binary
        with patch.dict(os.environ, {"STARCCM_BIN": r"C:\no\such\starccm.bat"}):
            with patch("runners.solvers.starccm._CANDIDATE_BINS", ()):
                with patch("shutil.which", return_value=None):
                    with self.assertRaisesRegex(RuntimeError, "STARCCM_BIN"):
                        starccm_binary()


class StarCCMSolverContractTests(unittest.TestCase):
    """Solver 接口契约（runners/solvers/__init__.py）：缺 macro 即 fail-fast。"""

    def test_missing_macro_fails_closed_without_invoking_binary(self):
        from runners.solvers.starccm import StarCCMSolver
        with tempfile.TemporaryDirectory() as d:
            s = StarCCMSolver()
            r = s.run_case(Path(d), 10.0)
            self.assertFalse(r["ok"])
            self.assertEqual(r["exit"], 2)
            self.assertIn("macro.java missing", r["stderr"])

    def test_run_case_builds_batch_command_with_optional_sim(self):
        from runners.solvers.starccm import StarCCMSolver
        with tempfile.TemporaryDirectory() as d:
            case = Path(d)
            (case / "macro.java").write_text("// macro")
            (case / "case.sim").write_text("placeholder")
            captured = {}

            def fake_popen(cmd, **kw):
                captured["cmd"] = cmd
                captured["cwd"] = kw.get("cwd")

                class _P:
                    returncode = 0

                    def communicate(self, timeout=None):
                        return ("... Server disconnected ...", None)

                return _P()

            with patch("runners.solvers.starccm.subprocess.Popen", side_effect=fake_popen):
                r = s = StarCCMSolver().run_case(case, 30.0)
            self.assertTrue(r["ok"])
            cmd = captured["cmd"]
            self.assertIn("-batch", cmd)
            self.assertEqual(cmd[cmd.index("-batch") + 1], "macro.java")
            self.assertEqual(cmd[cmd.index("-sim") + 1], str(case / "case.sim"))

    def test_execution_ok_requires_disconnect_and_rejects_fatal_tail(self):
        from runners.solvers.starccm import StarCCMSolver
        with tempfile.TemporaryDirectory() as d:
            case = Path(d)
            log = case / "macro.solver.log"
            log.write_text("... running ...\nServer disconnected\n")
            self.assertTrue(StarCCMSolver().execution_ok(case))
            log.write_text("...\nFatal error in macro\nServer disconnected\n")
            self.assertFalse(StarCCMSolver().execution_ok(case))
            self.assertFalse(StarCCMSolver().execution_ok(case / "nonexistent"))


class GetSolverRoutingTests(unittest.TestCase):
    def test_starccm_backend_registered(self):
        from runners.solvers.openfoam import get_solver
        s = get_solver("starccm-19.02.009-batch")
        self.assertEqual(s.name, "starccm-19.02.009-batch")

    def test_unknown_backend_still_refuses(self):
        from runners.solvers.openfoam import get_solver
        with self.assertRaisesRegex(ValueError, "未知求解器后端"):
            get_solver("fluent-2020r2")  # fluent.py 尚未实现——拒绝而非静默


if __name__ == "__main__":
    unittest.main()
