"""Replay must retain filtered task selection and the actual Harness inputs."""
from pathlib import Path
import copy
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class HarnessReplayTests(unittest.TestCase):
    def test_partial_oracle_replay_and_changed_companion_refusal(self):
        with tempfile.TemporaryDirectory(prefix='comac harness ') as temp:
            root = Path(temp)
            tasks = root/'tasks'/'fixture'
            tasks.mkdir(parents=True)
            prompt = tasks/'prompt.md'
            prompt.write_text('Write result.json containing value 42.')
            scaffold = root/'workflow notes.md'
            scaffold.write_text('Read the task and check your output.')
            oracle = root/'oracle.py'
            oracle.write_text('import json\nimport helper\n'
                              'open("result.json", "w").write(json.dumps({"value": helper.VALUE}))\n')
            companion = root/'helper.py'
            companion.write_text('VALUE = 42\n')
            source = sorted((ROOT/'tasks/aviary.transport_mission').glob('*.yaml'))[0]
            base = yaml.safe_load(source.read_text())
            base.update(registry_id='fixture.harness', input={'prompt_file':str(prompt), 'assets':[]})
            base['grader'].update(exec_kind='aviary_mission', result_keys=['value'],
                                  oracle_source=str(oracle), exact_keys=[])
            base['reference']['values'] = {'value':42}
            for n in range(3):
                spec = copy.deepcopy(base)
                spec['id'] = f'fixture_{n:03}'
                if n:
                    spec['grader']['oracle_source'] = None
                (tasks/f'{spec["id"]}.yaml').write_text(yaml.safe_dump(spec))
            out = root/'output'
            command = [sys.executable,'-m','runners.simulation_agent','--tasks',str(tasks),
                       '--out',str(out),'--provider','oracle','--iterate','2','--limit','2',
                       '--scaffold',str(scaffold),'--allow-partial-oracle']
            def execute(args):
                return subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=30)
            first = execute(command)
            self.assertEqual(first.returncode,0,first.stderr)
            mf = json.loads((out/'run_manifest.json').read_text())
            self.assertEqual(mf['n_tasks'],1)
            self.assertEqual(mf['extra']['selected_task_ids'],['fixture_000'])
            row = out/'result_fixture_000.json'
            self.assertEqual(json.loads(row.read_text())['score'],1)
            before = row.read_bytes()
            replay = shlex.split(mf['rerun_command'])
            replay = replay[replay.index('&&')+1:]
            self.assertEqual(replay[0],sys.executable)
            for flag, value in [('--iterate','2'),('--limit','2'),('--scaffold',str(scaffold))]:
                self.assertEqual(replay[replay.index(flag)+1],value)
            self.assertIn('--allow-partial-oracle',replay)
            self.assertEqual(execute(replay).returncode,0)
            self.assertEqual(row.read_bytes(),before)
            snapshot = {p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            for flag, value in [('--iterate','3'),('--limit','1')]:
                changed = replay.copy()
                changed[changed.index(flag)+1] = value
                self.assertNotEqual(execute(changed).returncode,0)
                self.assertEqual({p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')},snapshot)
            original_scaffold = scaffold.read_bytes()
            scaffold.write_text('Changed workflow instructions.')
            self.assertNotEqual(execute(replay).returncode,0)
            self.assertEqual({p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')},snapshot)
            scaffold.write_bytes(original_scaffold)
            companion.write_text('VALUE = 43\n')
            snapshot = {p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')}
            mismatch = execute(replay)
            self.assertNotEqual(mismatch.returncode,0,'changed oracle companion was silently reused')
            self.assertIn('[resume]',mismatch.stderr)
            self.assertEqual({p.name:p.read_bytes() for p in out.iterdir() if not p.name.startswith('.')},snapshot)
