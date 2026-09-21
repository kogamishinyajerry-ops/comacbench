import tempfile
import unittest
from pathlib import Path
from studies.cfd_fourth_grid import area_integral, field_dictionary, write_case, expansion_allowed

class FourthGridTests(unittest.TestCase):
    def test_invalid_integral_bounds(self):
        for a,b in [(0,0),(.02,.01),(-.001,.01),(0,float('nan'))]:
            with self.assertRaises(ValueError): area_integral(a,b,.01)

    def test_invalid_field_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'U'
            for content in ['FoamFile { format binary; }', 'FoamFile { format ascii; } #include "x"', 'FoamFile { format ascii; } a 1; a 2;']:
                p.write_text(content)
                with self.assertRaises(ValueError): field_dictionary(p)
            q=Path(d)/'link'; q.symlink_to(p)
            with self.assertRaises(ValueError): field_dictionary(q)

    def test_incomplete_gate_rejected(self):
        for data in [{}, {'gate_passed':True}, {'reynolds':100,'gate_passed':True,'rows':[]}]:
            self.assertFalse(expansion_allowed(data))

    def test_integral_and_midpoint_bias(self):
        self.assertAlmostEqual(area_integral(.01,.02,.01),1e-4,places=15)
        for n in [20,40,80,160]:
            exact=sum(area_integral(.01+i*.01/n,.01+(i+1)*.01/n,.01) for i in range(n))
            sampled=sum(6*((i+.5)/n)*(1-(i+.5)/n)*1e-4/n for i in range(n))
            self.assertAlmostEqual(sampled/exact-1,1/(2*n*n),places=12)

    def test_fourth_grid_parameters(self):
        with tempfile.TemporaryDirectory() as d:
            config=write_case(Path(d)/'case',8,10,60,100)
            self.assertEqual(config['expected_cells'],506880)
            self.assertIn('(160', (Path(d)/'case/0/U').read_text().replace('\n','('))
            with self.assertRaises(ValueError): write_case(Path(d)/'bad',16,10,60,100)


class FourthGridEvidenceTests(unittest.TestCase):
    def test_new_protocol_source_cannot_use_legacy_cold_start_validation(self):
        from unittest.mock import patch
        from studies.analyze_cfd_fourth_grid import verify_origin
        from studies.cfd_fourth_grid import POLICY
        source=Path('/source');root=Path('/study')
        with patch('studies.analyze_cfd_fourth_grid.verify_new',return_value=({'valid':False,'status':'complete'},0)) as modern, patch('studies.analyze_cfd_fourth_grid.verify_case') as legacy:
            with self.assertRaises(ValueError):verify_origin(source,{'policy':POLICY},root)
            legacy.assert_not_called()
        with patch('studies.analyze_cfd_fourth_grid.verify_new',return_value=({'valid':True,'status':'complete'},1)) as modern, patch('studies.analyze_cfd_fourth_grid.verify_case') as legacy:
            verify_origin(source,{'policy':POLICY},root)
            modern.assert_called_once_with(source,root);legacy.assert_not_called()
        with patch('studies.analyze_cfd_fourth_grid.verify_new') as modern, patch('studies.analyze_cfd_fourth_grid.verify_case') as legacy:
            verify_origin(source,{},root)
            legacy.assert_called_once_with(source,{});modern.assert_not_called()

    def test_large_field_is_study_only(self):
        from runners.solvers.foam_text import dictionary
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'U';p.write_text('FoamFile { format ascii; } internalField uniform (0 0 0);'+' '*(17*1024*1024))
            with self.assertRaises(ValueError):dictionary(p)
            self.assertEqual(field_dictionary(p)['internalField'],['uniform',['0','0','0']])
            with p.open('wb') as f:f.truncate(128*1024*1024+1)
            with self.assertRaises(ValueError):field_dictionary(p)

    def test_decision_rejects_duplicate_domain_and_failing_diagnostics(self):
        from studies.analyze_cfd_fourth_grid import decide
        from studies.cfd_fourth_grid import DOMAINS
        rows=[]
        for u,d in DOMAINS:
            for scale in (1,2,4,8):
                rows.append({'id':str((u,d,scale)),'valid':True,'config':{'scale':scale,'upstream_h':u,'downstream_h':d,'reynolds':100},
                             'qoi':{'x_over_h':3-.01/scale**2},'inlet':{'passed':True,'relative_bias':0},
                             'wall':{'passed':True,'relative_native_gap':.0002/scale}})
        bridges=[{'bridge_passed':True}]*2
        self.assertTrue(decide(rows,bridges)['gate_passed'])
        rows[-1]['wall']['relative_native_gap']=.01
        self.assertFalse(decide(rows,bridges)['gate_passed'])
        rows[-1]=rows[-2]
        self.assertFalse(decide(rows,bridges)['gate_passed'])

    def test_bad_phi_cannot_pass_independent_inlet_check(self):
        from studies.cfd_fourth_grid import inlet_check
        with tempfile.TemporaryDirectory() as d:
            case=Path(d);(case/'1').mkdir();(case/'constant').mkdir()
            head='FoamFile { format ascii; } '
            (case/'1/U').write_text(head+'boundaryField { inlet { value uniform (1 0 0); } }')
            (case/'1/phi').write_text(head+'dimensions [0 3 -1 0 0 0 0]; boundaryField { inlet { value uniform -0.00011; } }')
            (case/'constant/transportProperties').write_text(head+'nu [0 2 -1 0 0 0 0] 0.0002;')
            mesh={'ranges':{'inlet':[0]},'points':[(-.05,.01,0),(-.05,.02,0),(-.05,.02,.01),(-.05,.01,.01)],'faces':[[0,1,2,3]]}
            self.assertFalse(inlet_check(case,mesh,1)['passed'])

class GeometricInletTests(unittest.TestCase):
    def test_reversed_native_normal_is_rejected(self):
        from studies.analyze_cfd_fourth_grid import geometric_inlet
        with tempfile.TemporaryDirectory() as d:
            case=Path(d);(case/'1').mkdir();head='FoamFile { format ascii; } '
            (case/'1/U').write_text(head+'boundaryField { inlet { value uniform (1.5 0 0); } }')
            (case/'1/phi').write_text(head+'boundaryField { inlet { value uniform -0.00015; } }')
            mesh={'ranges':{'inlet':[0]},'points':[(-.05,.01,0),(-.05,.02,0),(-.05,.02,.01),(-.05,.01,.01)],'faces':[[0,1,2,3]]}
            with self.assertRaises(ValueError):geometric_inlet(case,mesh,1)
            mesh['faces']=[[3,2,1,0]]
            result=geometric_inlet(case,mesh,1)
            self.assertTrue(result['passed'])
            self.assertAlmostEqual(result['gauss_integral_m3_s'],1e-4)



class ExecutionVersionTests(unittest.TestCase):
    def test_acceleration_changes_only_relaxation_not_physics_or_thresholds(self):
        from studies.cfd_fourth_grid_balanced import write_case as paired
        from runners.solvers.foam_text import dictionary
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b'
            self.assertEqual(write_case(a,8,10,60,100),paired(b,8,10,60,100))
            changes=[p.relative_to(a).as_posix() for p in a.rglob('*') if p.is_file() and p.read_bytes()!=(b/p.relative_to(a)).read_bytes()]
            self.assertEqual(changes,['system/fvSolution'])
            old=dictionary(a/'system/fvSolution');new=dictionary(b/'system/fvSolution')
            self.assertEqual(new['relaxationFactors'],{'fields':{'p':['0.05']},'equations':{'U':['0.95']}})
            new['relaxationFactors']=old['relaxationFactors']
            self.assertEqual(old,new)



class Re200GateTests(unittest.TestCase):
    def test_failed_gate_creates_no_output_and_makes_no_native_call(self):
        from unittest.mock import patch
        from studies.expand_cfd_re200 import run
        import json
        with tempfile.TemporaryDirectory() as d:
            parent=Path(d)/'parent';parent.mkdir();out=Path(d)/'re200'
            data={'reynolds':100,'gate_passed':False};(parent/'analysis.json').write_text(json.dumps(data))
            with patch('studies.expand_cfd_re200.verify_re100',return_value=data),patch('studies.expand_cfd_re200.run_case') as native:
                with self.assertRaisesRegex(ValueError,'scientific gate'):run(parent,out)
                self.assertFalse(out.exists());native.assert_not_called()

    def test_forged_passed_flag_is_rejected(self):
        from unittest.mock import patch
        from studies.expand_cfd_re200 import run
        import json
        with tempfile.TemporaryDirectory() as d:
            parent=Path(d)/'parent';parent.mkdir();out=Path(d)/'re200'
            (parent/'analysis.json').write_text(json.dumps({'reynolds':100,'gate_passed':True}))
            with patch('studies.expand_cfd_re200.verify_re100',return_value={'reynolds':100,'gate_passed':False}),patch('studies.expand_cfd_re200.run_case') as native:
                with self.assertRaisesRegex(ValueError,'analysis drift'):run(parent,out)
                self.assertFalse(out.exists());native.assert_not_called()

if __name__=='__main__': unittest.main()
