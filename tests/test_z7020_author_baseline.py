"""Retain provenance for the original image alongside the repaired sources."""

import hashlib
import json
from pathlib import Path
import unittest


FPGA = Path(__file__).resolve().parents[1] / 'pyrpl' / 'fpga'


class TestAuthorBaseline(unittest.TestCase):
    def test_original_manifest_and_image_remain_author_baseline(self):
        manifest = json.loads((FPGA / 'targets/z20_gen2/author_rtl.json').read_text())
        self.assertEqual('387faf3012c21925c9905d81a95cb681ac7d1b22',
                         manifest['source_commit'])
        record = json.loads((FPGA / 'red_pitaya_z20_gen2_author.json').read_text())
        self.assertEqual(manifest['source_commit'], record['rtl_commit'])
        self.assertFalse(record['common_pid_filter_fixes_included'])
        self.assertEqual('f6728daaf863f6c48a1d8b27a7262d7fb7653c489f37db36acd6cbb9cc4a7307',
                         hashlib.sha256((FPGA / record['bitstream']).read_bytes()).hexdigest())

    def test_experimental_export_does_not_weaken_drc_or_contact_hardware(self):
        source = (FPGA / 'targets/z20_gen2/export_author_test.tcl').read_text()
        active = '\n'.join(line for line in source.splitlines()
                           if not line.lstrip().startswith('#'))
        self.assertIn('xc7z020clg400-1', active)
        self.assertIn('if {[file exists $output]} { error', active)
        self.assertIn('report_drc -ruledeck bitstream_checks', active)
        self.assertIn('write_bitstream red_pitaya_z20_gen2_author.bit', active)
        self.assertNotRegex(active, r'\b(SEVERITY|set_false_path|set_multicycle_path|'
                                   r'program_hw_devices|open_hw_manager|exec)\b')
        self.assertNotIn('-force', active)


if __name__ == '__main__':
    unittest.main()
