from pathlib import Path
import math
import json
import tempfile
import unittest

from studies.cfd_step_sensitivity import grid_convergence, write_case
from runners.solvers.foam_text import dictionary, field_values


class SensitivityTests(unittest.TestCase):
    def test_oscillating_diverging_missing_nonfinite_grids_are_not_gci(self):
        for values in ([3,2,3],[3,2,0],[3,3,3],[3,2],[3,2,float('nan')]):
            with self.subTest(values=values):
                self.assertFalse(grid_convergence(values)['applicable'])

    def test_known_second_order_sequence(self):
        r=grid_convergence([2.84,2.96,2.99])
        self.assertTrue(r['applicable'])
        self.assertAlmostEqual(r['observed_order'],2)
        self.assertAlmostEqual(r['extrapolated'],3)
        self.assertAlmostEqual(r['fine_gci'],1.25*.03/2.99/3)

    def test_mesh_cells_and_inlet_scale_while_near_domain_segments_stay_fixed(self):
        for level in (1,2,4):
            with tempfile.TemporaryDirectory() as tmp:
                info=write_case(Path(tmp),level,10,60,100)
                self.assertEqual(info['expected_cells'],(50+2*173)*20*level**2)
                u=dictionary(Path(tmp)/'0/U')['boundaryField']['inlet']['value']
                values=field_values(u,20*level,True)
                for i,v in enumerate(values):
                    eta=(i+.5)/(20*level)
                    self.assertAlmostEqual(v[0],6*eta*(1-eta))
                m=dictionary(Path(tmp)/'system/blockMeshDict')['blocks'][0]
                self.assertEqual([int(x) for x in m[2]],[50*level,20*level,1])
                self.assertAlmostEqual(float(m[9][0][0][0])*60,10)
                self.assertAlmostEqual(float(m[9][0][1][0])*60,20)
                self.assertEqual(len(m[9][0]),3)

    def test_unsupported_study_parameters_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args in [(0,5,30,100),(1,5,20,100),(1,7,30,100),(1,5,30,999)]:
                with self.subTest(args=args),self.assertRaises(ValueError):write_case(Path(tmp),*args)

    def test_empty_study_cannot_claim_verified(self):
        from studies.verify_cfd_study import verify
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'prior-artifacts.json').write_text('{}')
            with self.assertRaises(ValueError):verify(root)

    def test_failed_grid_gate_cannot_be_overridden_in_report(self):
        from studies.verify_cfd_study import verify_decision
        from studies.cfd_step_sensitivity import POLICY
        rows=[{'status':'complete','valid':True} for _ in range(12)]
        groups=[{'gci':{'applicable':True,'fine_gci':.009}} for _ in range(4)]
        decision={'gate_passed':True,'suggested_tolerance':.025,
                  'fine_domain_effect':.00001,'policy':POLICY}
        with self.assertRaises(ValueError):verify_decision(rows,groups,decision)

    def test_missing_runs_cannot_qualify_a_tolerance(self):
        from studies.verify_cfd_study import verify_decision
        from studies.cfd_step_sensitivity import POLICY
        decision={'gate_passed':True,'suggested_tolerance':.025,
                  'fine_domain_effect':.00001,'policy':POLICY}
        with self.assertRaises(ValueError):verify_decision([],[],decision)

    def test_wall_diagnostic_rejects_invalid_stencils(self):
        from studies.cfd_wall_gradient_diagnostic import wall_gradient
        for values in [(0,1,1,1),(1,1,1,1),(2,1,1,1),(1,2,float('nan'),1)]:
            with self.subTest(values=values),self.assertRaises(ValueError):wall_gradient(*values)

    def test_wall_diagnostic_recovers_quadratic_wall_derivative(self):
        from studies.cfd_wall_gradient_diagnostic import wall_gradient
        for y1,y2 in [(.1,.3),(.05,.15),(.025,.08)]:
            # u(y) = -2y + 7y², exact derivative at the wall is -2.
            self.assertAlmostEqual(wall_gradient(y1,y2,-2*y1+7*y1*y1,-2*y2+7*y2*y2),-2)

    def test_continuation_rejects_missing_checkpoint_or_log_gap(self):
        from studies.cfd_study_continuation import join_logs
        initial='Time = 500s\nSolving for Ux,\nSolving for Uy,\nSolving for p,\n'
        for next_log,checkpoint in [('Time = 502s\n',500),('Time = 501s\n',499)]:
            with self.subTest(next_log=next_log),self.assertRaises(ValueError):join_logs(initial,next_log,checkpoint)

    def test_continuation_discards_unsaved_iterations_without_rewriting_raw_logs(self):
        from studies.cfd_study_continuation import join_logs
        initial='Time = 500s\nSolving for Ux,\nSolving for Uy,\nSolving for p,\nTime = 501s\nUNSAVED_PARTIAL\n'
        continued='Time = 501s\nCONTINUED_NATIVE\n'
        merged=join_logs(initial,continued,500)
        self.assertNotIn('UNSAVED_PARTIAL',merged)
        self.assertTrue(merged.endswith(continued))
        self.assertIn('DERIVED',merged)

    def test_study_audit_rejects_viscosity_changed_without_config_change(self):
        from studies.verify_cfd_study import verify_inputs
        with tempfile.TemporaryDirectory() as tmp:
            case=Path(tmp);config=write_case(case,2,5,60,100)
            p=case/'constant/transportProperties';p.write_text(p.read_text().replace('0.0002','0.0003'))
            with self.assertRaises(ValueError):verify_inputs(case,config)


if __name__=='__main__':unittest.main()
