"""Revision prompts must expose the keys accepted by the unchanged grader."""
import hashlib
import unittest
import yaml
from runners import gen_tasks_awcom
from runners.hidden_runtime import load_hidden_pool


class RevisionInputContractTests(unittest.TestCase):
    def check_prompt(self, prompt, reference):
        keys = {'limit_load_factor', 'cabin_pressure_altitude_ft',
                'flap_limit_speed_ktas', 'fuel_tank_inerting_o2_pct'}
        for key in keys:
            self.assertTrue('`' + key + '`' in prompt, 'canonical key not declared: ' + key)
        self.assertTrue('the parameter names as printed' not in prompt)
        self.assertLessEqual(set(reference['changed_params']), keys)

    def test_public_revision_prompts_match_generator_and_declared_hash(self):
        mod = gen_tasks_awcom._load_gen_module()
        for i in range(1, 6):
            with self.subTest(task=i):
                prompt, ref = mod.gen_rev(1000 + i)
                task = gen_tasks_awcom.TASKS_DIR / f'awc_rev_{i:02d}.yaml'
                spec = yaml.safe_load(task.read_text())
                self.check_prompt(prompt, ref)
                self.assertEqual(task.with_suffix('.md').read_text(), prompt)
                self.assertEqual(spec['input']['prompt_sha256'],
                                 hashlib.sha256(prompt.encode()).hexdigest())
                self.assertEqual(spec['reference']['reference_json'], ref)

    def test_hidden_revision_prompts_pass_frozen_pool_integrity_and_expose_keys(self):
        tasks, prompts, _ = load_hidden_pool(gen_tasks_awcom.BENCH, gen_tasks_awcom.RID)
        revision_tasks = [t for t in tasks if t.id.startswith('awc_rev_')]
        self.assertEqual(len(revision_tasks), 15)
        for task in revision_tasks:
            with self.subTest(task=task.id):
                self.check_prompt(prompts[task.id], task['reference']['reference_json'])


if __name__ == '__main__':
    unittest.main()
