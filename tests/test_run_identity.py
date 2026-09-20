"""CLI regression tests: resume must never mix different evaluation identities."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
import copy
import yaml

ROOT = Path(__file__).resolve().parents[1]

class ResumeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='comac-resume-tests-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tasks = self.root / 'tasks' / 'fixture'
        self.tasks.mkdir(parents=True)
        self.out = self.root / 'output'
        self.spec = {
            'id': 'fixture_001', 'registry_id': 'fixture.qa', 'domain': 'knowledge',
            'task_type': 'qa_grounded', 'model_profile': 'plain_llm',
            'assets_revision': 'fixture-v1', 'hidden': False, 'allowed_tools': [],
            'input': {'prompt_file': str(self.tasks/'fixture_001.md'), 'assets': []},
            'output_contract': ['answer'], 'reference': {'correct_option_index': 1},
            'grader': {'answer_format': 'mcq', 'validity_gate': True},
            'scoring': {'weights': {'physics': 0, 'requirements': 1, 'objective': 0, 'robustness': 0}},
            'limits': {'wall_clock_s': 10, 'attempts': 1},
            'license_provenance': {'license': 'self-built', 'mirror_allowed': True},
        }
        (self.tasks/'fixture_001.md').write_text('Choose one: 1. correct 2. incorrect')
        self.write_spec()

    def write_spec(self):
        (self.tasks/'fixture_001.yaml').write_text(yaml.safe_dump(self.spec))

    def run_cli(self, *flags):
        return subprocess.run([sys.executable, '-m', 'runners.qa_grounded',
            '--tasks', str(self.tasks), '--out', str(self.out), '--provider', 'oracle',
            *flags], cwd=ROOT, text=True, capture_output=True, timeout=30)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.out.iterdir() if p.is_file() and not p.name.startswith('.')}

    def test_resume_rejects_changed_seed_without_modifying_existing_run(self):
        first = self.run_cli('--seed', '1')
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.snapshot()
        resumed = self.run_cli('--seed', '2', '--resume')
        self.assertNotEqual(resumed.returncode, 0, 'different seed was silently accepted')
        self.assertIn('resume', resumed.stderr.lower())
        self.assertEqual(self.snapshot(), before)

    def test_identical_resume_preserves_result_and_counts_cached_task(self):
        self.assertEqual(self.run_cli().returncode, 0)
        path = self.out/'result_fixture_001.json'
        before = path.read_bytes()
        resumed = self.run_cli('--resume')
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(json.loads((self.out/'run_manifest.json').read_text())['extra']['resumed_tasks'], 1)

    def test_cache_mismatches_are_rejected_before_any_write(self):
        self.assertEqual(self.run_cli().returncode, 0)
        result = self.out/'result_fixture_001.json'
        good = json.loads(result.read_text())
        for field, value in [('task_id', 'wrong'), ('registry_id', 'wrong'),
                             ('adapter', 'wrong'), ('environment_digest', 'wrong'),
                             ('assets_revision', 'wrong'), ('score', 2),
                             ('artifacts', {}), ('subscores', {}),
                             ('gate_failures', None), ('failure_mode', []),
                             ('timings', {}), ('logs', None)]:
            with self.subTest(field=field):
                row = copy.deepcopy(good)
                row[field] = value
                result.write_text(json.dumps(row))
                before = self.snapshot()
                r = self.run_cli('--resume')
                self.assertNotEqual(r.returncode, 0)
                self.assertIn('[resume]', r.stderr)
                self.assertEqual(self.snapshot(), before)

    def test_changed_model_prompt_or_grader_refuses_resume(self):
        self.assertEqual(self.run_cli().returncode, 0)
        before = self.snapshot()
        r = self.run_cli('--resume', '--model', 'another-model')
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(self.snapshot(), before)
        self.assertNotEqual(self.run_cli('--resume', '--provider', 'stub').returncode, 0)
        self.assertEqual(self.snapshot(), before)
        prompt = self.tasks/'fixture_001.md'
        original_prompt = prompt.read_text()
        prompt.write_text('A different effective prompt')
        self.assertNotEqual(self.run_cli('--resume').returncode, 0)
        self.assertEqual(self.snapshot(), before)
        prompt.write_text(original_prompt)
        self.spec['grader']['numeric_rel_tol'] = 0.5
        self.write_spec()
        self.assertNotEqual(self.run_cli('--resume').returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_legacy_manifest_or_corrupt_json_refuses_resume(self):
        self.assertEqual(self.run_cli().returncode, 0)
        mf = self.out/'run_manifest.json'
        original = mf.read_bytes()
        legacy = json.loads(original)
        legacy['extra'].pop('resume_identity')
        mf.write_text(json.dumps(legacy))
        before = self.snapshot()
        self.assertNotEqual(self.run_cli('--resume').returncode, 0)
        self.assertEqual(self.snapshot(), before)
        mf.write_bytes(original)
        (self.out/'result_fixture_001.json').write_text('{broken')
        before = self.snapshot()
        self.assertNotEqual(self.run_cli('--resume').returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_non_resume_cannot_overwrite_a_completed_run(self):
        self.assertEqual(self.run_cli().returncode, 0)
        before = self.snapshot()
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertEqual(self.snapshot(), before)

    def test_incomplete_run_finishes_without_changing_completed_result(self):
        second = copy.deepcopy(self.spec)
        second['id'] = 'fixture_002'
        (self.tasks/'fixture_002.yaml').write_text(yaml.safe_dump(second))
        self.assertEqual(self.run_cli().returncode, 0)
        first = (self.out/'result_fixture_001.json').read_bytes()
        (self.out/'result_fixture_002.json').unlink()
        r = self.run_cli('--resume')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.out/'result_fixture_001.json').read_bytes(), first)
        self.assertTrue((self.out/'result_fixture_002.json').exists())
        manifest = json.loads((self.out/'run_manifest.json').read_text())
        self.assertEqual(manifest['n_tasks'], 2)
        self.assertEqual(manifest['extra']['resumed_tasks'], 1)

    def test_changed_declared_oracle_file_refuses_resume(self):
        oracle = self.root/'reference.py'
        oracle.write_text('print(1)\n')
        self.spec['grader']['oracle_source'] = str(oracle)
        self.write_spec()
        self.assertEqual(self.run_cli().returncode, 0)
        before = self.snapshot()
        oracle.write_text('print(2)\n')
        r = self.run_cli('--resume')
        self.assertNotEqual(r.returncode, 0, 'changed declared file was ignored')
        self.assertEqual(self.snapshot(), before)

    def test_manifest_metadata_must_agree_with_its_identity(self):
        self.assertEqual(self.run_cli().returncode, 0)
        path = self.out/'run_manifest.json'
        original = json.loads(path.read_text())
        for field, value in [('seed', 123), ('provider','wrong'), ('n_tasks',123)]:
            with self.subTest(field=field):
                modified = copy.deepcopy(original)
                modified[field] = value
                path.write_text(json.dumps(modified))
                before = self.snapshot()
                r = self.run_cli('--resume')
                self.assertNotEqual(r.returncode,0)
                self.assertEqual(self.snapshot(),before)

    def test_unexpected_result_refuses_resume_before_rebuilding_manifest(self):
        self.assertEqual(self.run_cli().returncode, 0)
        (self.out/'result_unknown.json').write_bytes((self.out/'result_fixture_001.json').read_bytes())
        before = self.snapshot()
        r = self.run_cli('--resume')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('unexpected cached task', r.stderr)
        self.assertEqual(self.snapshot(), before)

if __name__ == '__main__':
    unittest.main()
