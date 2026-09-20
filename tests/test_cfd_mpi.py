import unittest
from studies.cfd_mpi_reconstruction import verify_partition

class PartitionTests(unittest.TestCase):
    def test_missing_duplicate_wrong_and_nonfinite_partition_rejected(self):
        for shards in [[([0],[1])],[([0,0],[1,1])],[([0,1],[1,3])],[([0,1],[1,float('nan')])],[([-1,1],[1,2])]]:
            with self.subTest(shards=shards),self.assertRaises(ValueError):verify_partition([1,2],shards)

    def test_reordered_vector_partition_is_exact(self):
        result=verify_partition([(1,2,3),(4,5,6),(7,8,9)],[([2],[(7,8,9)]),([0,1],[(1,2,3),(4,5,6)])])
        self.assertEqual(result,{'verified_entries':3,'max_absolute_error':0.0})

    def test_re200_rejects_invalid_or_mismatched_source_before_creating_case(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from studies.cfd_mpi_re200 import run
        config={'scale':8,'reynolds':200,'upstream_h':5,'downstream_h':30,'expected_cells':390400,'near_step_dx_h':.0125,'spanwise_layers':1,'grading_sections':[[10,100,1],[20,40,4]]}
        source_config=dict(config,scale=4,expected_cells=97600,near_step_dx_h=.025)
        for base in [{'valid':False,'status':'complete','config':source_config},
                     {'valid':True,'status':'failed','config':source_config},
                     {'valid':True,'status':'complete','config':dict(source_config,reynolds=100)},
                     {'valid':True,'status':'complete','config':dict(source_config,upstream_h=10)}]:
            with tempfile.TemporaryDirectory() as d, patch('studies.cfd_mpi_re200.verify_new',return_value=(base,1)), patch('studies.cfd_mpi_re200.native') as native:
                with self.assertRaises(ValueError):run(Path(d),'candidate',Path(d)/'source',config)
                self.assertFalse((Path(d)/'candidate').exists());native.assert_not_called()

if __name__=='__main__':unittest.main()
