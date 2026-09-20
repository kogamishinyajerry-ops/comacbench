import unittest
import tempfile
from pathlib import Path
import json
from studies.cfd_wall_branch import match_diagnostic_branch
from studies.cfd_zero_crossing_audit import crossings


def association(curve,bracket):
    root=next(r for r in crossings(curve)['crossings'] if r['bracket_indices']==bracket)
    return {'selected':dict(root,primary_member=True)}


class WallBranchTests(unittest.TestCase):
    def test_corresponding_negative_branch_can_cross_a_sampling_interval(self):
        # Hand-worked roots: native 3.5, diagnostic 4.5; no reference value supplied.
        native=[[1.,1.],[2.,-1.],[3.,-1.],[4.,1.],[5.,1.]]
        diagnostic=[[1.,1.],[2.,-1.],[3.,-1.],[4.,-1.],[5.,1.]]
        r=match_diagnostic_branch(native,diagnostic,association(native,[2,3]))
        self.assertEqual(r['selected']['x_h'],4.5)
        self.assertEqual(r['native_branch_indices'],[1,2])
        self.assertEqual(r['diagnostic_branch_indices'],[1,3])
        self.assertEqual(r['overlap_indices'],[1,2])

    def test_invalid_missing_misaligned_and_zero_samples_are_rejected(self):
        native=[[1.,1.],[2.,-1.],[3.,-1.],[4.,1.]]
        for curve in [[],native[:-1],[[x+.1,y] for x,y in native],[[1.,1.],[2.,-1.],[3.,0.],[4.,1.]],[[1.,1.],[2.,float('nan')],[3.,-1.],[4.,1.]]]:
            with self.assertRaises(ValueError):match_diagnostic_branch(native,curve,association(native,[2,3]))

    def test_corner_upcrossing_is_retained_without_becoming_the_primary(self):
        native=[[float(i),v] for i,v in enumerate([-1,1,-1,-1,1,1])]
        diagnostic=[[float(i),v] for i,v in enumerate([-1,1,-1,-1,-1,1])]
        r=match_diagnostic_branch(native,diagnostic,association(native,[3,4]))
        self.assertEqual(r['selected']['x_h'],4.5)
        self.assertEqual([p['primary_member'] for p in r['all_upcrossings']],[False,True])

    def test_split_merged_absent_and_open_branches_are_rejected(self):
        native=[[float(i),v] for i,v in enumerate([1,-1,-1,-1,-1,1,1])]
        for values in [[1,-1,1,-1,-1,1,1],[1,1,1,1,1,-1,1],[1,-1,-1,-1,-1,-1,-1]]:
            with self.assertRaises(ValueError):match_diagnostic_branch(native,[[float(i),v] for i,v in enumerate(values)],association(native,[4,5]))
        native=[[float(i),v] for i,v in enumerate([-1,1,-1,-1,1])]
        merged=[[float(i),v] for i,v in enumerate([-1,-1,-1,-1,1])]
        with self.assertRaisesRegex(ValueError,'merges'):match_diagnostic_branch(native,merged,association(native,[3,4]))

    def test_unverified_or_forged_primary_root_is_rejected(self):
        native=[[1.,1.],[2.,-1.],[3.,-1.],[4.,1.]];a=association(native,[2,3])
        for key,value in [('primary_member',False),('x_h',99.),('bracket_indices',[0,1])]:
            bad={'selected':dict(a['selected'],**{key:value})}
            with self.assertRaises(ValueError):match_diagnostic_branch(native,native,bad)

    def test_matrix_gate_rejects_declared_counts_without_all_saved_cases(self):
        from studies.run_cfd_re300_v2 import compatibility_gate
        from studies.cfd_step_sensitivity import sha
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'protocol.json').write_text('{}')
            (p/'compatibility-verification.json').write_text(json.dumps({'passed':True,'cases':18,'snapshots':36,'protocol_sha256':sha(p/'protocol.json'),'files':{}}))
            with self.assertRaises(ValueError):compatibility_gate(p)


if __name__=='__main__':unittest.main()
