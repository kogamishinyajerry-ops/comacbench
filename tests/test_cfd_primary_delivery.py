import hashlib
from pathlib import Path
import tempfile
import unittest
from studies.verify_cfd_primary_delivery import verify_files


class PrimaryDeliveryTests(unittest.TestCase):
    def test_changed_missing_and_symlink_inputs_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'U';p.write_bytes(b'native')
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(verify_files(root,{'U':digest}),1)
            for files in ({'missing':digest},{'U':'0'*64},{'../U':digest}):
                with self.assertRaises(ValueError):verify_files(root,files)
            (root/'link').symlink_to(p)
            with self.assertRaises(ValueError):verify_files(root,{'link':digest})


if __name__=='__main__':unittest.main()
