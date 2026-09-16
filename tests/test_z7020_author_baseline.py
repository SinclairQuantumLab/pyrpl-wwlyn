"""The first Pro device test must not acquire shared RTL repairs."""

import hashlib
import json
from pathlib import Path
import unittest


FPGA = Path(__file__).resolve().parents[1] / 'pyrpl' / 'fpga'


class TestAuthorBaseline(unittest.TestCase):
    def test_notebook_selects_author_image_and_is_not_a_fixed_logic_test(self):
        notebook = json.loads((FPGA.parents[1] / 'test.ipynb.template').read_text(encoding='utf-8'))
        cells = {cell['id']: ''.join(cell['source']) for cell in notebook['cells']}
        self.assertIn('Common PID/filter fixes are intentionally absent', cells['template-intro'])
        self.assertIn('Z20_AUTHOR_BITSTREAM_FILENAME', cells['template-local'])
        self.assertNotIn('"red_pitaya.bin"', cells['template-local'])
        self.assertIn('gen2-pro-os2-author-baseline', cells['template-connect'])

    def test_entire_rtl_tree_matches_author_commit(self):
        manifest = json.loads((FPGA / 'targets/z20_gen2/author_rtl.json').read_text())
        self.assertEqual('387faf3012c21925c9905d81a95cb681ac7d1b22',
                         manifest['source_commit'])
        rtl = FPGA / 'rtl'
        self.assertEqual(set(manifest['files']),
                         {p.name for p in rtl.iterdir() if p.is_file()})
        for name, expected in manifest['files'].items():
            with self.subTest(file=name):
                content = (rtl / name).read_bytes().replace(b'\r\n', b'\n')
                header = ('blob %d\0' % len(content)).encode('ascii')
                self.assertEqual(expected, hashlib.sha1(header + content).hexdigest())

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
