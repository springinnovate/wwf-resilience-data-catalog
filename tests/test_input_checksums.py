"""Keep the frozen-input check independent of the local scientific collection."""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_inputs", ROOT / "scripts" / "check_inputs.py")
CHECK_INPUTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK_INPUTS)


class InputChecksumTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'snapshot.json').write_bytes(b'{"frozen":true}')
        (self.root / 'checksums.sha256').write_text('existing checksum list')

    def test_local_data_is_pruned_before_traversal_or_hashing(self):
        baseline = CHECK_INPUTS.manifest(self.root)
        local = self.root / 'evidence_data'
        (local / 'nested').mkdir(parents=True)
        (local / 'nested' / 'large.bin').write_bytes(b'local scientific bytes')
        native_scandir = os.scandir

        def reject_local_traversal(path):
            if Path(path) == local or local in Path(path).parents:
                raise AssertionError('Local scientific data must not be traversed.')
            return native_scandir(path)

        with patch.object(CHECK_INPUTS.os, 'scandir', side_effect=reject_local_traversal):
            self.assertEqual(CHECK_INPUTS.manifest(self.root), baseline)
        self.assertEqual(baseline, {'snapshot.json': hashlib.sha256(b'{"frozen":true}').hexdigest()})

    def test_other_unexpected_files_and_nested_same_name_remain_checked(self):
        baseline = CHECK_INPUTS.manifest(self.root)
        nested = self.root / 'source' / 'evidence_data'
        nested.mkdir(parents=True)
        (nested / 'unexpected.json').write_bytes(b'nested input')
        (self.root / 'unexpected.json').write_bytes(b'root input')
        actual = CHECK_INPUTS.manifest(self.root)
        self.assertEqual(set(actual) - set(baseline),
                         {'unexpected.json', 'source/evidence_data/unexpected.json'})
        (nested / 'unexpected.json').write_bytes(b'changed nested input')
        self.assertNotEqual(actual['source/evidence_data/unexpected.json'],
                            CHECK_INPUTS.manifest(self.root)['source/evidence_data/unexpected.json'])


if __name__ == '__main__':
    unittest.main()
