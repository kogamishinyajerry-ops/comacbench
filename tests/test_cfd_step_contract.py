"""CFD native inputs and platform-owned evidence must fail closed."""
from pathlib import Path
import shutil
import tempfile
import unittest
import json
import os
from unittest.mock import patch
import yaml

ROOT=Path(__file__).resolve().parents[1]
TEMPLATES=ROOT/'packs/aviation-cfd-step-v1/templates'


class CFDContractTests(unittest.TestCase):
    def test_precomputed_qoi_is_rejected_before_solver(self):
        from runners.solvers.backward_step import audit_inputs
        with tempfile.TemporaryDirectory() as tmp:
            case=Path(tmp)/'case'
            shutil.copytree(TEMPLATES,case)
            (case/'qoi.json').write_text('{"reattachment_x_over_h":2.922}')
            result=audit_inputs(case)
            self.assertFalse(result['passed'])
            self.assertIn('precomputed_output', {i['code'] for i in result['issues']})

    def test_missing_boundary_wrong_viscosity_and_dynamic_code_rejected(self):
        from runners.solvers.backward_step import audit_inputs
        cases=[('0/p','outlet','lostOutlet','boundary_mismatch'),
               ('constant/transportProperties','2e-4','3e-4','fluid_mismatch'),
               ('system/controlDict','application','#include "foo"\napplication','unsupported_input')]
        for name,old,new,expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                case=Path(tmp)/'case';shutil.copytree(TEMPLATES,case)
                p=case/name;before=p.read_text();self.assertIn(old,before)
                p.write_text(before.replace(old,new))
                result=audit_inputs(case)
                self.assertFalse(result['passed'])
                self.assertIn(expected,{i['code'] for i in result['issues']})

    def test_reference_native_inputs_accepted(self):
        from runners.solvers.backward_step import audit_inputs
        result=audit_inputs(TEMPLATES)
        self.assertTrue(result['passed'],result['issues'])

    def test_exit_end_alone_is_not_convergence(self):
        from runners.solvers.backward_step import residuals
        log=''
        for i,r in [(1,.5),(20,1e-8)]:
            log+=f'Time = {i}s\n'+''.join(f'Solving for {k}, Initial residual = {r}, Final residual = 0\n' for k in ('p','Ux','Uy'))
        self.assertFalse(residuals(log+'\nEnd\n')['passed'])
        self.assertTrue(residuals(log+'SIMPLE solution converged in 20 iterations\nEnd\n')['passed'])
        self.assertFalse(residuals(log.replace('1e-08','0.1')+'SIMPLE solution converged in 20 iterations\nEnd\n')['passed'])

    def test_native_flux_imbalance_and_wrong_units_fail(self):
        from runners.solvers.backward_step import mass_balance
        from runners.solvers.foam_text import FoamError
        mesh={'ranges':{k:[0] for k in ('inlet','outlet','lowerWall','upperWall','frontAndBack')}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'20/phi';path.parent.mkdir()
            source='FoamFile {format ascii;} dimensions [0 3 -1 0 0 0 0]; boundaryField {'
            for k,v in [('inlet',-.0001),('outlet',.00009),('lowerWall',0),('upperWall',0)]:
                source+=f'{k} {{type calculated;value uniform {v};}}'
            source+='frontAndBack {type empty;} }'
            path.write_text(source)
            self.assertFalse(mass_balance(tmp,20,mesh)['passed'])
            path.write_text(source.replace('9e-05','0.0001'))
            self.assertTrue(mass_balance(tmp,20,mesh)['passed'])
            path.write_text(source.replace('[0 3 -1','[0 2 -1'))
            with self.assertRaises(FoamError):mass_balance(tmp,20,mesh)

    def test_wall_shear_uses_downstream_bottom_not_vertical_step(self):
        from runners.solvers.backward_step import reattachment
        from runners.solvers.foam_text import FoamError
        xs=[.05]+list(range(1,11))
        centres=[(0,.005,0)]+[(x*.01,0,0) for x in xs]
        mesh={'ranges':{'lowerWall':list(range(len(centres)))},'centres':centres}
        vals=[-999]+[3-x for x in xs]  # Native tau_x is opposite streamwise convention.
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'20/wallShearStress';p.parent.mkdir()
            source='FoamFile {format ascii;} dimensions [0 2 -2 0 0 0 0]; boundaryField {lowerWall {value nonuniform List<vector> '+str(len(vals))+' ('+' '.join(f'({v} 0 0)' for v in vals)+');}}'
            p.write_text(source)
            self.assertEqual(reattachment(tmp,20,mesh)['x_over_h'],3)
            p.write_text(source.replace('(2 0 0)','(nan 0 0)'))
            with self.assertRaises(FoamError):reattachment(tmp,20,mesh)

    def test_candidate_snapshot_survives_system_temp_directory_alias(self):
        from runners.solvers.cfd_step_runtime import evaluate
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{'COMAC_CFD_EVIDENCE_ROOT':tmp}), patch('runners.solvers.cfd_step_runtime.environment',return_value={}), patch('runners.solvers.cfd_step_runtime.native_step',return_value={'exit':1,'timeout':False}) as run:
            details=evaluate({'reference':{'values':{'reattachment_x_over_h':2.922}}},(TEMPLATES.parent/'private/reference.py').read_text(),30)
            run.assert_called_once()
            evidence=Path(details['evidence']['directory'])
            self.assertEqual((evidence/'submitted/0/U').read_text(),(TEMPLATES/'0/U').read_text())
            self.assertNotIn('functions',(evidence/'submitted/system/controlDict').read_text())
            self.assertIn('wallShearStress',(evidence/'case/system/controlDict').read_text())

    def test_bad_input_stops_before_native_environment(self):
        from runners.solvers.cfd_step_runtime import evaluate
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{'COMAC_CFD_EVIDENCE_ROOT':tmp}), patch('runners.solvers.cfd_step_runtime.environment') as env:
            r=evaluate({},(TEMPLATES.parent/'private/precomputed_qoi.py').read_text(),30)
            env.assert_not_called()
            self.assertFalse(r['solver_executed'])
            self.assertEqual(r['cfd_audit']['checks']['convergence'],'not_checked')
            self.assertIn('precomputed_output',[i['code'] for i in r['cfd_audit']['issues']])

    def test_contribution_missing_or_unreasonable_contract_has_actionable_feedback(self):
        from comacbench.pack import validate_pack
        cases=[('threshold',lambda t:t['grader']['cfd_contract']['thresholds'].pop('max_mass_imbalance'),'invalid_cfd_contract'),
               ('loose',lambda t:t['grader']['cfd_contract']['thresholds'].update(max_mass_imbalance=1),'invalid_cfd_contract'),
               ('truth',lambda t:t['reference']['values'].update(reattachment_x_over_h=30),'cfd_reference_mismatch'),
               ('doi',lambda t:t['reference'].pop('doi'),'cfd_reference_mismatch'),
               ('units',lambda t:t['evaluation'].pop('units'),'cfd_reference_mismatch'),
               ('trace',lambda t:t['evaluation']['requirements'].pop(),'missing_cfd_check'),
               ('missing_negative',lambda t:t['evaluation']['negative_controls'].pop(),'missing_cfd_negative'),
               ('unknown',lambda t:t['evaluation']['requirements'][0].update(check='cfd:fiction'),'unknown_check'),
               ('negative',lambda t:t['evaluation']['negative_controls'][0].update(expected_issue='fiction'),'unknown_expected_issue')]
        for name,mutate,expected in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'pack';shutil.copytree(TEMPLATES.parent,root)
                p=root/'tasks/aviation.cfd/backward_step_01.yaml';spec=yaml.safe_load(p.read_text());mutate(spec);p.write_text(yaml.safe_dump(spec,allow_unicode=True))
                v=validate_pack(root)
                self.assertFalse(v['runnable'])
                issues=[i for i in v['issues'] if i['code']==expected]
                self.assertTrue(issues,v['issues'])
                self.assertTrue(all(i['field'] and i['suggested_fix'] for i in issues))
        self.assertTrue(validate_pack(TEMPLATES.parent)['runnable'])
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'pack';shutil.copytree(TEMPLATES.parent,root)
            self.assertTrue(validate_pack(root)['runnable'],validate_pack(root)['issues'])


if __name__=='__main__':unittest.main()
