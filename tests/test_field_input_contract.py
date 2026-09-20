"""Field boundaries must be declared and regenerated prompts must match their tasks."""
import hashlib
import unittest
from pathlib import Path
import yaml
from runners import gen_tasks_awcom, gen_tasks_office2
from runners.hidden_runtime import load_hidden_pool

ROOT=Path(__file__).resolve().parents[1]


class FieldInputContractTests(unittest.TestCase):
    def test_family_and_section_boundaries_are_explicit(self):
        for path in sorted((ROOT/'tasks/awext.clause_extract').glob('*.yaml')):
            with self.subTest(task=path.stem):
                spec=yaml.safe_load(path.read_text())
                card=gen_tasks_office2.synth_clause_card(int(path.stem.rsplit('_',1)[1])-1)
                prompt=gen_tasks_office2.clause_prompt(card)
                self.assertIn('`family`',prompt)
                self.assertIn('parentheses',prompt)
                self.assertIn('`clause_no`',prompt)
                self.assertIn('including the §',prompt)
                self.assertEqual(prompt,path.with_suffix('.md').read_text())
                self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(),spec['input']['prompt_sha256'])
                self.assertEqual(gen_tasks_office2.clause_ref_json(card),spec['reference']['reference_json'])

    def test_document_and_clause_reference_boundaries_cover_public_and_hidden(self):
        mod=gen_tasks_awcom._load_gen_module()
        tasks,prompts,_=load_hidden_pool(ROOT,'awcom.compliance')
        checks=[(t.id,prompts[t.id]) for t in tasks if t.id.startswith(('awc_acam_','awc_trc_'))]
        for family in ['acam','trc']:
            for i in range(1,6):
                tid=f'awc_{family}_{i:02d}'
                path=ROOT/'tasks/awcom.compliance'/f'{tid}.yaml'
                spec=yaml.safe_load(path.read_text())
                prompt,ref=mod.GENS[family](1000+i)
                self.assertEqual(prompt,path.with_suffix('.md').read_text())
                self.assertEqual(hashlib.sha256(prompt.encode()).hexdigest(),spec['input']['prompt_sha256'])
                self.assertEqual(ref,spec['reference']['reference_json'])
                checks.append((tid,prompt))
        for tid,prompt in checks:
            with self.subTest(task=tid):
                if tid.startswith('awc_acam_'):
                    self.assertTrue('`clause_id`' in prompt and 'Document' in prompt and
                                    'without the Section' in prompt, tid+' lacks document field boundary')
                else:
                    self.assertTrue('`clause_ref`' in prompt and 'including the §' in prompt,
                                    tid+' lacks clause reference boundary')


if __name__=='__main__':unittest.main()
