"""Contribution input contracts: reject bad material before any agent executes."""
import copy
from pathlib import Path
import tempfile
import unittest
import yaml

from comacbench.pack import validate_pack


class PackValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        import shutil
        shutil.copytree(Path(__file__).resolve().parents[1] / 'packs/aviation-core-v1',
                        self.root, dirs_exist_ok=True)

    def change_task(self, change):
        p = self.root / 'tasks/enterprise.data/data_units_01.yaml'
        d = yaml.safe_load(p.read_text())
        change(d)
        p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False))

    def codes(self):
        return {i['code'] for i in validate_pack(self.root)['issues']}

    def test_missing_material(self):
        (self.root / 'tasks/enterprise.data/data_units_01.md').unlink()
        self.assertIn('missing_file', self.codes())
        self.assertFalse(validate_pack(self.root)['runnable'])

    def test_tampered_prompt(self):
        p = self.root / 'tasks/enterprise.data/data_units_01.md'
        p.write_text(p.read_text() + '\nChanged requirement')
        self.assertIn('digest_mismatch', self.codes())

    def test_vacuous_grader(self):
        self.change_task(lambda d: d['grader'].update(tests=['assert True']))
        self.assertIn('vacuous_test', self.codes())

    def test_bad_weights(self):
        self.change_task(lambda d: d['scoring'].update(weights={'physics': 0, 'requirements': 1}))
        self.assertIn('unscored_correctness', self.codes())

    def test_gold_leakage(self):
        from hashlib import sha256
        def change(d):
            f = d['grader']['oracle_source']
            d['input']['assets'] = [{'path': f, 'digest': sha256((self.root/f).read_bytes()).hexdigest()}]
        self.change_task(change)
        self.assertIn('reference_exposed', self.codes())

    def test_path_escape(self):
        self.change_task(lambda d: d['input'].update(prompt_file='../secret.txt'))
        self.assertIn('path_escape', self.codes())

    def test_empty_and_malformed_yaml(self):
        (self.root/'pack.yaml').write_text('[]')
        self.assertFalse(validate_pack(self.root)['runnable'])
        (self.root/'pack.yaml').write_text('x: [')
        self.assertFalse(validate_pack(self.root)['runnable'])

    def test_missing_reference_revision(self):
        self.change_task(lambda d: d['reference'].pop('revision'))
        self.assertIn('missing_reference', self.codes())

    def test_unknown_grader(self):
        self.change_task(lambda d: d['grader'].update(exec_kind='future_magic'))
        self.assertIn('unsupported_grader', self.codes())

    def test_duplicate_yaml_key(self):
        p=self.root/'pack.yaml'
        p.write_text(p.read_text()+'\nrevision: silently-overwritten\n')
        self.assertIn('invalid_yaml',self.codes())

    def test_output_contract_cannot_claim_unchecked_artifact(self):
        self.change_task(lambda d:d.update(output_contract=['script','audit.csv']))
        self.assertIn('unsupported_output',self.codes())

    def test_simulation_nonfinite_reference_and_invalid_tolerance(self):
        p=self.root/'tasks/aviation.structures/beam_static_01.yaml'
        d=yaml.safe_load(p.read_text());d['reference']['values']['tip_defl_mm']=float('nan')
        d['grader']['numeric_rel_tol']=1.5
        p.write_text(yaml.safe_dump(d))
        self.assertIn('nonfinite_reference',self.codes())
        self.assertIn('invalid_tolerance',self.codes())

    def test_malformed_nested_structures_never_escape_feedback(self):
        for value in (None,42,'bad',[],[None],{'x':[]}):
            with self.subTest(value=value):
                self.change_task(lambda d:d.update(grader=value))
                self.assertFalse(validate_pack(self.root)['runnable'])

    def test_positive_pack_still_requires_expert_review(self):
        r = validate_pack(self.root)
        self.assertTrue(r['runnable'], r['issues'])
        self.assertFalse(r['publishable'])
        self.assertEqual(r['task_count'], 3)


if __name__ == '__main__':
    unittest.main()
