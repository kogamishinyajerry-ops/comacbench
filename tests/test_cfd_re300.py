import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from studies.cfd_re300 import write_case,config_for,verify_flux_partition,decide
from runners.solvers.foam_text import dictionary


class Re300Tests(unittest.TestCase):
    def test_invalid_inputs_before_writing(self):
        with tempfile.TemporaryDirectory() as d:
            target=Path(d)/'case'
            for args in [(3,5,30,2),(8,7,30,2),(1,5,30,1)]:
                with self.assertRaises(ValueError):write_case(target,*args)
                self.assertFalse(target.exists())

    def test_new_viscosity_and_retention_only(self):
        from studies.cfd_fourth_grid import write_case as old_writer
        with tempfile.TemporaryDirectory() as d:
            old=Path(d)/'old';new=Path(d)/'new';old_writer(old,8,10,60,200)
            config=write_case(new,8,10,60)
            self.assertEqual(config,config_for(8,10,60))
            self.assertEqual(config['reynolds'],300)
            self.assertAlmostEqual(float(dictionary(new/'constant/transportProperties')['nu'][-1]),.02/300,places=16)
            self.assertEqual(dictionary(new/'system/controlDict')['purgeWrite'],['2'])
            for p in old.rglob('*'):
                if p.is_file() and str(p.relative_to(old)) not in ('system/controlDict','constant/transportProperties'):
                    self.assertEqual(p.read_bytes(),(new/p.relative_to(old)).read_bytes())

    def test_flux_missing_conflicting_and_bad_address_rejected(self):
        for shards in [[],[([1],[2.])],[([0],[1.])],[([1,1],[1.,1.])],[([1],[1.]),([-1],[-1.1])]]:
            with self.assertRaises(ValueError):verify_flux_partition([1.,2.],shards)

    def test_signed_processor_interfaces_agree(self):
        result=verify_flux_partition([1.,2.],[([1,2],[1.,2.]),([-1],[-1.])])
        self.assertEqual(result['verified_faces'],2)
        self.assertEqual(result['shared_faces'],1)

    def test_wrong_source_and_configuration_rejected_before_case_creation(self):
        from studies.run_cfd_re300 import run_case
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);cid='re300-u5-d30-g1'
            protocol={'legacy':str(out/'legacy'),'parent':str(out/'parent'),'minimum_start_free_bytes':0}
            with patch('studies.run_cfd_re300.identity',return_value=protocol):
                for config,source in [(config_for(1,5,30),out/'foreign/re200-u5-d30-g1'),
                                      (dict(config_for(1,5,30),reynolds=200),out/'legacy/re200-u5-d30-g1')]:
                    with self.assertRaises(ValueError):run_case(out,cid,config,source)
                    self.assertFalse((out/cid).exists())

    def test_empty_rank_face_cannot_hide_invalid_address(self):
        from studies.cfd_re300 import verify_phi
        with patch('studies.cfd_re300.phi_values',side_effect=[[1.],[None]]),patch('studies.cfd_re300.signed_addresses',return_value=[2]):
            with self.assertRaises(ValueError):verify_phi(Path('/unused'),100)

    def test_incomplete_and_duplicate_matrix_cannot_pass(self):
        self.assertFalse(decide([],True)['gate_passed'])
        row={'valid':True,'config':config_for(8,5,30),'qoi':{'x_over_h':6.75},'wall':{'relative_native_gap':0,'passed':True},'inlet':{'passed':True,'relative_bias':0},'relative_change':0}
        self.assertFalse(decide([row]*16,True)['gate_passed'])


if __name__=='__main__':unittest.main()
