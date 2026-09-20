import tempfile
import unittest
from pathlib import Path
from runners.solvers.foam_text import dictionary,FoamError
from studies.cfd_re300_mesh_io import read_initial_inlet


class LargeInitialFieldTests(unittest.TestCase):
    def test_missing_symlink_and_over_128_mib_initial_field_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            case=Path(d);(case/'0').mkdir();p=case/'0/U'
            with self.assertRaises(FoamError):read_initial_inlet(case,2)
            p.symlink_to(case/'elsewhere')
            with self.assertRaises(FoamError):read_initial_inlet(case,2)
            p.unlink()
            with p.open('wb') as f:f.truncate(128*1024**2+1)
            with self.assertRaises(FoamError):read_initial_inlet(case,2)

    def test_valid_large_field_preserves_values_without_changing_public_limit(self):
        with tempfile.TemporaryDirectory() as d:
            case=Path(d);(case/'0').mkdir();p=case/'0/U'
            p.write_text('/*'+'x'*(16*1024**2)+'*/\nFoamFile { format ascii; }\nboundaryField { inlet { type fixedValue; value nonuniform List<vector> 2 ((1 0 0) (1.25 0 0)); } }')
            with self.assertRaises(FoamError):dictionary(p)
            self.assertEqual([list(v) for v in read_initial_inlet(case,2)],[[1.,0.,0.],[1.25,0.,0.]])


if __name__=='__main__':unittest.main()
