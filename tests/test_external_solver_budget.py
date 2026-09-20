"""External agent generation has its own timeout; it must not consume solver time."""
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import yaml

from runners.common import TaskSpec
from runners.simulation_agent import _run_ccx_task


class SolverBudgetTests(unittest.TestCase):
    def test_external_agent_latency_does_not_make_solver_budget_negative(self):
        root=Path(__file__).resolve().parents[1]
        p=root/'packs/aviation-core-v1/tasks/aviation.structures/beam_static_01.yaml'
        task=TaskSpec(yaml.safe_load(p.read_text()),p)
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            (directory/'model.inp').write_text('test deck')
            class Workspace:
                dir=directory
                def write(self,*_):return directory/'candidate.py'
                def run(self,*_):return {'exit':0,'timeout':False,'duration_s':.01,'stderr':''}
            with patch('runners.simulation_agent.IsolatedRun',return_value=Workspace()), \
                 patch('runners.solvers.calculix.run_ccx',return_value={'exit':0,'timeout':False,'duration_s':.1,'stdout_tail':''}) as solver, \
                 patch('runners.solvers.calculix.parse_dat',return_value=task['reference']['values']):
                result=_run_ccx_task(task,'pass',{'provider':'external'},time.time()-400,
                                    'test-env',[],{},300)
            self.assertGreater(solver.call_args.args[2],290)
            self.assertEqual(result['score'],1)


if __name__=='__main__':unittest.main()
