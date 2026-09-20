import math
import unittest

from studies.cfd_zero_crossing_audit import crossings


class ZeroCrossingAuditTests(unittest.TestCase):
    def test_rejects_malformed_nonfinite_and_unsorted_curves(self):
        for curve in ([], [[0, 1]], [[0, 1], [0, -1]], [[1, 1], [0, -1]],
                      [[0, math.nan], [1, 1]], [[0, 1], [math.inf, -1]],
                      [[0, True], [1, -1]], [[0, 1, 2], [1, -1]]):
            with self.subTest(curve=curve), self.assertRaises(ValueError):
                crossings(curve)

    def test_preserves_multiple_reversals_without_selecting_a_primary_root(self):
        result=crossings([[0, -1], [1, 1], [2, -1], [3, 1]])
        self.assertEqual([r['x_h'] for r in result['crossings']], [.5, 1.5, 2.5])
        self.assertEqual([r['direction'] for r in result['crossings']],
                         ['negative_to_positive', 'positive_to_negative', 'negative_to_positive'])
        self.assertTrue(result['ambiguous_for_first_upcrossing_rule'])
        self.assertNotIn('primary_root', result)

    def test_zero_samples_are_explicitly_ambiguous_and_not_interpolated_away(self):
        result=crossings([[0, -1], [1, 0], [2, 0], [3, 1]])
        self.assertEqual(result['crossings'], [])
        self.assertEqual(result['zero_samples_x_h'], [1, 2])
        self.assertTrue(result['ambiguous_for_first_upcrossing_rule'])

    def test_direction_and_interpolation_do_not_depend_on_signal_scale(self):
        for factor in (1e-300, 1, 1e300):
            result=crossings([[0, -factor], [1, 3*factor]])
            self.assertAlmostEqual(result['crossings'][0]['x_h'], .25)
            self.assertFalse(result['ambiguous_for_first_upcrossing_rule'])


if __name__=='__main__':unittest.main()
