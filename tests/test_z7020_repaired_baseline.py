"""Source, provenance and manual selection guards for the repaired candidate."""

import hashlib
import json
from pathlib import Path
import unittest

FPGA = Path(__file__).resolve().parents[1] / 'pyrpl' / 'fpga'
TARGET = FPGA / 'targets/z20_gen2'


class TestRepairedBaseline(unittest.TestCase):
    def test_entire_rtl_tree_matches_shared_fix_checkpoint(self):
        manifest = json.loads((TARGET / 'repaired_rtl.json').read_text())
        self.assertEqual('e7479166c03c15bdd244e2153e974b4596815041', manifest['source_commit'])
        rtl = FPGA / 'rtl'
        self.assertEqual(set(manifest['files']), {p.name for p in rtl.iterdir() if p.is_file()})
        for name, expected in manifest['files'].items():
            with self.subTest(file=name):
                content = (rtl / name).read_bytes().replace(b'\r\n', b'\n')
                self.assertEqual(expected, hashlib.sha1(
                    ('blob %d\0' % len(content)).encode() + content).hexdigest())

    def test_only_approved_pid_and_filter_sources_differ_from_author(self):
        original = json.loads((TARGET / 'author_rtl.json').read_text())['files']
        repaired = json.loads((TARGET / 'repaired_rtl.json').read_text())['files']
        self.assertEqual(set(original), set(repaired))
        self.assertEqual({'red_pitaya_pid_block.v', 'red_pitaya_filter_block.v'},
                         {name for name in original if original[name] != repaired[name]})

    def test_notebook_explicitly_selects_repaired_image(self):
        notebook = json.loads((FPGA.parents[1] / 'test.ipynb.template').read_text(encoding='utf-8'))
        cells = {cell['id']: ''.join(cell['source']) for cell in notebook['cells']}
        self.assertIn('Common PID/filter fixes are included', cells['template-intro'])
        self.assertIn('Z20_REPAIRED_BITSTREAM_FILENAME', cells['template-local'])
        self.assertNotIn('Z20_AUTHOR_BITSTREAM_FILENAME', cells['template-local'])
        self.assertIn('red_pitaya_z20_gen2_repaired.json', cells['template-local'])
        self.assertIn('gen2pro-os2-repaired', cells['template-connect'])

    def test_export_does_not_change_timing_or_drc(self):
        source = (TARGET / 'export_repaired_test.tcl').read_text()
        active = '\n'.join(line for line in source.splitlines()
                           if not line.lstrip().startswith('#'))
        self.assertIn('xc7z020clg400-1', active)
        self.assertIn('if {[file exists $output]} { error', active)
        self.assertIn('report_drc -ruledeck bitstream_checks', active)
        self.assertIn('write_bitstream red_pitaya_z20_gen2_repaired.bit', active)
        self.assertNotRegex(active, r'\b(SEVERITY|set_false_path|set_multicycle_path|'
                                   r'program_hw_devices|open_hw_manager|exec)\b')
        self.assertNotIn('-force', active)

    def test_packaged_record_matches_artifact_and_repair_scope(self):
        record = json.loads((FPGA / 'red_pitaya_z20_gen2_repaired.json').read_text())
        self.assertTrue(record['common_pid_filter_fixes_included'])
        self.assertEqual('not performed', record['hardware_test'])
        self.assertEqual(record['bitstream_sha256'], hashlib.sha256(
            (FPGA / record['bitstream']).read_bytes()).hexdigest())
        self.assertEqual(record['rtl_commit'], 'e7479166c03c15bdd244e2153e974b4596815041')


if __name__ == '__main__':
    unittest.main()
