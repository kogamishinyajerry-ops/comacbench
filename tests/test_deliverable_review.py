"""deliverable_review（artifacts.v1）的协议级测试：正例、五个命名负例、合法替代解。

方案 §5 的三组校准在这里落地：
  1. 参考实现（正例）：完整 manifest + 交付树 + evaluator 全过；
  2. 错误实现（负例）：manifest 缺失/损坏/路径逃逸/树不一致/内容断言失败——
     每个必须命中**各自的命名诊断**，不能混在一个笼统失败里；
  3. 合法替代解：不同代码结构、不同合法表达（列顺序不同、单位等价表述）
     不得被误杀。

不启动真实模型：直接构造 workspace 文件树后调用协议函数与 evaluator 通路。
"""
import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runners.deliverable_review import (  # noqa: E402
    PROTOCOL, actual_tree, declared_tree, evaluate_deliverables, read_manifest,
)
from runners.common import load_tasks  # noqa: E402

import tempfile


def _ws(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="artifacts-test-"))
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


GOOD_MANIFEST = {
    "protocol": PROTOCOL,
    "deliverables": [
        {"path": "outputs/results.csv", "kind": "result_table"},
        {"path": "outputs/rejected.csv", "kind": "rejection_list"},
    ],
}


def _good_files() -> dict[str, str]:
    return {
        "manifest.json": json.dumps(GOOD_MANIFEST),
        "outputs/results.csv": "part,qty\nP-01,2\n",
        "outputs/rejected.csv": "part,reason\nP-02,unit_missing\n",
    }


class ManifestTests(unittest.TestCase):

    def test_good_manifest_reads(self):
        m, issues = read_manifest(_ws(_good_files()))
        self.assertEqual(issues, [])
        self.assertEqual(m["protocol"], PROTOCOL)
        self.assertEqual(len(m["deliverables"]), 2)

    def test_missing_manifest_is_named(self):
        files = _good_files()
        del files["manifest.json"]
        m, issues = read_manifest(_ws(files))
        self.assertIsNone(m)
        self.assertEqual(issues, ["manifest_missing"])

    def test_wrong_protocol_is_named(self):
        files = _good_files()
        files["manifest.json"] = json.dumps({"protocol": "other", "deliverables": []})
        m, issues = read_manifest(_ws(files))
        self.assertEqual(issues, ["manifest_invalid"])

    def test_empty_deliverables_is_invalid(self):
        files = _good_files()
        files["manifest.json"] = json.dumps(
            {"protocol": PROTOCOL, "deliverables": []})
        m, issues = read_manifest(_ws(files))
        self.assertEqual(issues, ["manifest_invalid"])


class TreeTests(unittest.TestCase):

    def test_declared_matches_actual(self):
        root = _ws(_good_files())
        m, _ = read_manifest(root)
        declared, di = declared_tree(m, root)
        actual, ai = actual_tree(root, declared)
        self.assertEqual(di + ai, [])
        rel_d = sorted(p.relative_to(root).as_posix() for p in declared)
        rel_a = sorted(p.relative_to(root).as_posix() for p in actual)
        self.assertEqual(rel_d, rel_a)

    def test_path_escape_is_named(self):
        root = _ws({"manifest.json": json.dumps(
            {"protocol": PROTOCOL,
             "deliverables": [{"path": "../outside.csv",
                               "kind": "result_table"}]})})
        m, _ = read_manifest(root)
        declared, issues = declared_tree(m, root)
        self.assertEqual(issues, ["deliverable_path_escape"])
        self.assertEqual(declared, [])

    def test_undeclared_file_is_mismatch(self):
        files = _good_files()
        files["outputs/extra.txt"] = "undeclared"
        root = _ws(files)
        m, _ = read_manifest(root)
        declared, _ = declared_tree(m, root)
        rel_d = {p.relative_to(root).as_posix() for p in declared}
        rel_a = {p.relative_to(root).as_posix() for p in actual_tree(root, declared)[0]}
        self.assertEqual(rel_a - rel_d, {"outputs/extra.txt"})


class EvaluatorTests(unittest.TestCase):
    """独立 evaluator 通路：从文件内容复算，不信任 manifest 自评。"""

    @classmethod
    def setUpClass(cls):
        base = Path(__file__).parent
        cls.layout = base / "_eval_layout"
        (cls.layout / "tasks" / "enterprise.data").mkdir(parents=True, exist_ok=True)
        (cls.layout / "private").mkdir(parents=True, exist_ok=True)
        (cls.layout / "tasks" / "enterprise.data" / "t.yaml").write_text(
            "id: t\n", encoding="utf-8")
        shutil.copyfile(base / "_fixture_evaluator.py",
                        cls.layout / "private" / "_fixture_evaluator.py")
        cls._to_clean = cls.layout

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._to_clean, ignore_errors=True)

    @staticmethod
    def _task_with_layout(layout: Path, evaluator_module: str | None):
        grader = {"exec_kind": "file_package"}
        if evaluator_module is not None:
            grader["evaluator"] = {"module": evaluator_module}
        return {"id": "t", "grader": grader,
                "_yaml_path": str(layout / "tasks" / "enterprise.data" / "t.yaml")}

    def test_content_failure_is_named(self):
        files = _good_files()
        # 正确答案应是 qty=2；交付里写错成 3 —— evaluator 必须从文件读出来
        files["outputs/results.csv"] = "part,qty\nP-01,3\n"
        root = _ws(files)
        m, _ = read_manifest(root)
        task = self._task_with_layout(self.layout, "_fixture_evaluator")
        ev, issues = evaluate_deliverables(task, root, m)
        self.assertEqual(issues, ["deliverable_content_check_failed"])
        self.assertTrue(ev["evaluated"])
        self.assertEqual(ev["failed"], ["qty_row_P-01"])

    def test_valid_alternative_solution_not_killed(self):
        """合法替代解：列顺序不同、CSV 引号风格不同 —— 不能误杀。"""
        files = _good_files()
        files["outputs/results.csv"] = 'qty,part\n"2","P-01"\n'
        root = _ws(files)
        m, _ = read_manifest(root)
        task = self._task_with_layout(self.layout, "_fixture_evaluator")
        ev, issues = evaluate_deliverables(task, root, m)
        self.assertEqual(issues, [])
        self.assertEqual(ev.get("failed"), [])

    def test_missing_evaluator_module_reported_not_crashed(self):
        root = _ws(_good_files())
        m, _ = read_manifest(root)
        ev, issues = evaluate_deliverables(self._task_with_layout(self.layout, None), root, m)
        self.assertFalse(ev["evaluated"])
        self.assertEqual(issues, [])


class EndToEndOracleTests(unittest.TestCase):
    """oracle 路径端到端：写交付的正例脚本全绿；manifest 缺失负例命中命名诊断。"""

    ROOT = Path(__file__).resolve().parents[1]

    @staticmethod
    def _pack(tmp: Path):
        pack = tmp / "pack"
        (pack / "private").mkdir(parents=True)
        (pack / "tasks" / "enterprise.data").mkdir(parents=True)
        (pack / "pack.yaml").write_text(
            "protocol: comacbench.pack.v1\nid: artifacts-e2e\ntitle: t\nrevision: '1'\n"
            "license: x\nsource: x\n"
            "suites:\n- id: enterprise.data\n  family: enterprise_data\n"
            "  tasks:\n  - tasks/enterprise.data/pkg_01.yaml\n",
            encoding="utf-8")
        (pack / "private" / "pkg_eval.py").write_text(
            Path(__file__).with_name("_fixture_evaluator.py").read_text(encoding="utf-8"),
            encoding="utf-8")
        oracle = (
            "import json, pathlib\n"
            "w = pathlib.Path.cwd()\n"
            "(w / 'outputs').mkdir(exist_ok=True)\n"
            "(w / 'outputs' / 'results.csv').write_text('part,qty\\nP-01,2\\n')\n"
            "(w / 'outputs' / 'rejected.csv').write_text('part,reason\\nP-02,unit_missing\\n')\n"
            "(w / 'manifest.json').write_text(json.dumps({\n"
            f"  'protocol': '{PROTOCOL}',\n"
            "  'deliverables': [\n"
            "    {'path': 'outputs/results.csv', 'kind': 'result_table'},\n"
            "    {'path': 'outputs/rejected.csv', 'kind': 'rejection_list'}]}))\n"
        )
        (pack / "private" / "pkg_oracle.py").write_text(oracle, encoding="utf-8")
        task_yaml = (
            "id: pkg_01\nregistry_id: enterprise.data\ndomain: data\n"
            "task_type: deliverable_review\nmodel_profile: plain_llm\n"
            "assets_revision: artifacts-e2e@1\nenvironment_digest: computed-at-runtime\n"
            "hidden: false\nallowed_tools: [python]\n"
            "input:\n  prompt_file: tasks/enterprise.data/pkg_01.md\n"
            "  prompt_sha256: 0000000000000000000000000000000000000000000000000000000000000000\n"
            "  assets: []\n"
            "output_contract:\n- manifest.json\n"
            "reference:\n  source: synthetic\n  revision: r1\n  uncertainty_note: exact\n"
            "license_provenance:\n  license: CC0-1.0\n  source: synthetic\n  revision: r1\n"
            "grader:\n  answer_format: code\n  exec_kind: file_package\n"
            "  validity_gate: true\n"
            "  evaluator: {module: pkg_eval}\n"
            "  deliverable_kinds: [result_table, rejection_list]\n"
            "  oracle_source: private/pkg_oracle.py\n"
            "limits: {cpu: 1, memory_gb: 1, wall_clock_s: 60, attempts: 1}\n"
            "scoring:\n  weights: {physics: 0.55, requirements: 0.45, objective: 0, robustness: 0}\n"
            "evaluation:\n  requirements:\n  - {id: r1, text: deliver files, check: 'evaluator:qty_row_P-01'}\n"
            "  negative_controls:\n  - {script: private/no_manifest.py, max_score: 0,"
            " expected_issue: manifest_missing}\n"
        )
        (pack / "tasks" / "enterprise.data" / "pkg_01.yaml").write_text(
            task_yaml, encoding="utf-8")
        (pack / "tasks" / "enterprise.data" / "pkg_01.md").write_text(
            "deliver\n", encoding="utf-8")
        return pack

    def test_oracle_run_scores_full(self):
        import tempfile
        from runners import deliverable_review as dr
        with tempfile.TemporaryDirectory() as tmp:
            pack = self._pack(Path(tmp))
            tasks = load_tasks(str(pack / "tasks" / "enterprise.data"))
            self.assertEqual(len(tasks), 1)
            prompt_cache = {t.id: "p" for t in tasks}
            oracle_cache = {
                t.id: (pack / "private" / "pkg_oracle.py").read_text(encoding="utf-8")
                for t in tasks}
            r = dr.run_task(tasks[0], provider="oracle", model=None, seed=0,
                            env_digest="e", prompt_cache=prompt_cache,
                            assets_root=pack / "tasks",
                            oracle_cache=oracle_cache)
            self.assertEqual(r["validity_gate"], 1, r.get("gate_failures"))
            self.assertEqual(r["score"], 1.0)
            self.assertEqual(r["failure_mode"], None)

    def test_missing_manifest_negative_hits_named_code(self):
        import tempfile
        from runners import deliverable_review as dr
        with tempfile.TemporaryDirectory() as tmp:
            pack = self._pack(Path(tmp))
            tasks = load_tasks(str(pack / "tasks" / "enterprise.data"))
            # 负例脚本：写部分交付但**不写 manifest** → 必须命中 manifest_missing
            bad = ("import pathlib\nw = pathlib.Path.cwd()\n"
                   "(w / 'outputs').mkdir(exist_ok=True)\n"
                   "(w / 'outputs' / 'results.csv').write_text('part,qty\\nP-01,2\\n')\n")
            prompt_cache = {t.id: "p" for t in tasks}
            oracle_cache = {t.id: bad for t in tasks}
            r = dr.run_task(tasks[0], provider="oracle", model=None, seed=0,
                            env_digest="e", prompt_cache=prompt_cache,
                            assets_root=pack / "tasks",
                            oracle_cache=oracle_cache)
            self.assertEqual(r["validity_gate"], 0)
            self.assertIn("manifest_missing", r["gate_failures"])
            self.assertEqual(r["failure_mode"], "manifest_missing")


if __name__ == "__main__":
    unittest.main()
