import unittest
from comacbench.evidence import catalog, verify_study

class RetentionTests(unittest.TestCase):
    def test_deleted_native_evidence_cannot_report_full_verification(self):
        study = dict(catalog()[0], native_evidence_state='deleted_by_user')
        with self.assertRaisesRegex(ValueError, 'native_evidence_deleted'):
            verify_study(study, full=True)

    def test_retained_summary_is_explicitly_historical(self):
        study = dict(catalog()[0], native_evidence_state='deleted_by_user')
        result = verify_study(study)
        self.assertEqual(result['verification_level'], 'retained_analysis_and_receipts')
        self.assertFalse(result['native_evidence_available'])

if __name__ == '__main__': unittest.main()
