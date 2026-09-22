"""Static starter-pack checks; these do not substitute for runtime calibration."""
import hashlib
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'packs/aviation-data-starter-v1'
CORE = ROOT / 'packs/aviation-core-v1'


class DataStarterTest(unittest.TestCase):
    def test_exact_two_existing_tasks(self):
        manifest = yaml.safe_load((PACK / 'pack.yaml').read_text(encoding='utf-8'))
        paths = [p for suite in manifest['suites'] for p in suite['tasks']]
        self.assertEqual(paths, ['tasks/enterprise.data/data_units_01.yaml',
                                 'tasks/enterprise.ontology/ontology_trace_01.yaml'])
        self.assertEqual({s['family'] for s in manifest['suites']},
                         {'enterprise_data', 'knowledge_ontology'})

    def test_all_reused_sources_are_byte_identical(self):
        files = sorted((PACK / 'tasks').rglob('*')) + sorted((PACK / 'private').rglob('*'))
        files = [p for p in files if p.is_file() and '__pycache__' not in p.parts]
        self.assertEqual(len(files), 9)
        for path in files:
            with self.subTest(path=path.relative_to(PACK)):
                self.assertFalse(path.is_symlink())
                self.assertEqual(path.read_bytes(), (CORE / path.relative_to(PACK)).read_bytes())

    def test_no_solver_task_or_public_answer_exposure(self):
        for path in (PACK / 'tasks').rglob('*.yaml'):
            task = yaml.safe_load(path.read_text(encoding='utf-8'))
            self.assertEqual(task['task_type'], 'code_exec')
            self.assertEqual(task['grader']['exec_kind'], 'unit_tests_problem')
            self.assertEqual(task['input']['assets'], [])
            self.assertEqual(task['output_contract'], ['script'])
            prompt = PACK / task['input']['prompt_file']
            self.assertEqual(hashlib.sha256(prompt.read_bytes()).hexdigest(),
                             task['input']['prompt_sha256'].removeprefix('sha256:'))

    def test_controls_and_reference_sources_exist(self):
        count = 0
        for path in (PACK / 'tasks').rglob('*.yaml'):
            task = yaml.safe_load(path.read_text(encoding='utf-8'))
            self.assertTrue((PACK / task['grader']['oracle_source']).is_file())
            self.assertEqual(task['reference']['n_test_cases'], 7)
            for control in task['evaluation']['negative_controls']:
                self.assertTrue((PACK / control['script']).is_file())
                count += 1
        self.assertEqual(count, 4)


if __name__ == '__main__':
    unittest.main()
