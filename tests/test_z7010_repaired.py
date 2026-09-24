"""Offline guards for the separate repaired Gen1 hardware-test candidate."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import pyrpl
from pyrpl import z10_repaired as candidate
from pyrpl.errors import ExpectedPyrplError

PACKAGE = Path(pyrpl.__file__).resolve().parent
ROOT = PACKAGE.parent
TARGET = PACKAGE / 'fpga/targets/z10_gen1'
AUTHOR_HASH = 'dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed'


class TestGen1Repaired(unittest.TestCase):
    def test_images_are_separate_hash_pinned_z7010_streams(self):
        original = (PACKAGE / 'fpga/red_pitaya.bin').read_bytes()
        repaired = candidate.repaired_file().read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), AUTHOR_HASH)
        self.assertNotEqual(original, repaired)
        self.assertEqual(len(original), len(repaired))
        self.assertTrue(candidate.is_repaired_selection(candidate.Z10_REPAIRED_BITSTREAM_FILENAME))
        self.assertFalse(candidate.is_repaired_selection(PACKAGE / 'fpga/red_pitaya.bin'))
        # Same Xilinx sync-word byte order as the field-tested dual-OS BIN.
        self.assertEqual(original.find(b'\x66\x55\x99\xaa'),
                         repaired.find(b'\x66\x55\x99\xaa'))
        self.assertGreaterEqual(repaired.find(b'\x66\x55\x99\xaa'), 0)

    def test_missing_or_wrong_explicit_image_never_falls_back(self):
        with self.assertRaises(OSError):
            candidate.repaired_file(PACKAGE / 'fpga/red_pitaya.bin')
        with self.assertRaises(OSError):
            candidate.repaired_file('does-not-exist.bin')

    @unittest.skipUnless(TARGET.is_dir(), 'source-tree build guard')
    def test_rtl_is_exact_common_repair(self):
        manifest = json.loads((TARGET / 'repaired_rtl.json').read_text())
        self.assertEqual(manifest['source_commit'], candidate.REPAIRED_RTL_COMMIT)
        for name, digest in manifest['files'].items():
            data = (PACKAGE / 'fpga/rtl' / name).read_bytes().replace(b'\r\n', b'\n')
            blob = b'blob ' + str(len(data)).encode() + b'\0' + data
            self.assertEqual(hashlib.sha1(blob).hexdigest(), digest, name)
        for name, digest in {
            'ip/system_bd.tcl': 'f0ef5df86d2f6ed3af34dc0a8611ede6a9e6cf0e',
            'sdc/red_pitaya.xdc': 'c2ff95bf72e0753bc00c98f0dc258fafc774e8d2',
            'red_pitaya_vivado.tcl': 'cc3b8a0f6c1e0edfa0985186c269d944ee40f1d9',
        }.items():
            data = (PACKAGE / 'fpga' / name).read_bytes().replace(b'\r\n', b'\n')
            blob = b'blob ' + str(len(data)).encode() + b'\0' + data
            self.assertEqual(hashlib.sha1(blob).hexdigest(), digest, name)

    @unittest.skipUnless(TARGET.is_dir(), 'source-tree build guard')
    def test_constraints_preserve_original_active_pins_and_delays(self):
        def active(path):
            return [line.split(' #')[0].strip() for line in path.read_text().splitlines()
                    if line.strip() and not line.lstrip().startswith('#')
                    and not line.startswith('set_false_path')]
        self.assertEqual(active(PACKAGE / 'fpga/sdc/red_pitaya.xdc'),
                         active(TARGET / 'board.xdc'))
        self.assertIn('set_false_path -from [get_clocks clk_fpga_0]  -to [get_clocks adc_clk]',
                      (TARGET / 'board.xdc').read_text())
        build = (TARGET / 'build.tcl').read_text()
        self.assertIn('xc7z010clg400-1', build)
        self.assertIn('-flatten_hierarchy none -bufg 16 -keep_equivalent_registers', build)
        self.assertIn('power_opt_design', build)
        self.assertNotIn('z20_gen2', build)

    @unittest.skipUnless((ROOT / 'test.ipynb.template').is_file(), 'source template')
    def test_notebook_is_clean_and_explicitly_repaired(self):
        nb = json.loads((ROOT / 'test.ipynb.template').read_text(encoding='utf-8'))
        code = []
        for c in nb['cells']:
            if c['cell_type'] == 'code':
                self.assertEqual(c['outputs'], [])
                self.assertIsNone(c['execution_count'])
                source = ''.join(c['source'])
                compile(source, '<notebook>', 'exec')
                code.append(source)
        joined = '\n'.join(code)
        self.assertIn('bitstream = repaired_file()', joined)
        self.assertIn('preflight_fpga_update', joined)
        self.assertIn('device.update_fpga', joined)
        self.assertIn('pid.i = -150000', joined)
        self.assertNotIn('Z20_', joined)
        self.assertNotIn('CONFIRM_FPGA', joined)
        self.assertNotRegex(joined, r'192\.168\.')


class TestLegacyGuard(unittest.TestCase):
    def device(self, hw='STEM_125-14_v1.1', os='Red Pitaya GNU/Linux ecosystem version 1.04-18', char=True):
        reply = 'PYRPL_OS:%s\nPYRPL_HW:%s\nPYRPL_CHAR:%s\n' % (os, hw, 'yes' if char else '')
        ssh = Mock()
        ssh.execute.return_value = (0, reply, '')
        return SimpleNamespace(ssh=ssh, end=Mock())

    def test_read_only_identity_probe(self):
        for hw in ('STEM_125-14_v1.0', 'STEM_125-14_v1.1', 'STEM_14_B_v1.0'):
            d = self.device(hw)
            report = candidate.legacy_preflight(d)
            self.assertTrue(report['read_only'])
            self.assertEqual(report['hardware_revision'], hw)
            d.ssh.scp.put.assert_not_called()
            d.end.assert_not_called()
            self.assertEqual(d.ssh.execute.call_count, 1)
            cmd = d.ssh.execute.call_args.args[0]
            self.assertIn('fw_printenv -n hw_rev', cmd)
            self.assertNotIn('fw_setenv', cmd)
            self.assertNotIn('> /dev', cmd)

    def test_unknown_or_wrong_hardware_rejected_before_mutation(self):
        for hw in ('', 'unknown', 'STEM_125-14_Z7020_v1.0', 'STEM_125-14_v2.0',
                   'STEM_125-14_Z7020_4IN_v1.0', 'STEM_125-14_v1.1_slave',
                   'STEM_125-10_v1.0', 'STEM_125-14_LN_v1.1'):
            d = self.device(hw)
            with self.assertRaises(ExpectedPyrplError):
                candidate.legacy_program(d)
            d.end.assert_not_called()
            d.ssh.scp.put.assert_not_called()

    def test_os_and_character_device_required(self):
        for opts in ({'os': '2.07-3'}, {'os': 'unknown'}, {'char': False}):
            d = self.device(**opts)
            with self.assertRaises(ExpectedPyrplError):
                candidate.legacy_program(d)
            d.end.assert_not_called()
            d.ssh.scp.put.assert_not_called()

    def test_eeprom_warning_or_probe_failure_is_not_default_identity(self):
        for status, stderr in ((1, ''), (0, 'Warning: Bad CRC, using default environment')):
            d = self.device()
            d.ssh.execute.return_value = (status, d.ssh.execute.return_value[1], stderr)
            with self.assertRaises(ExpectedPyrplError):
                candidate.legacy_program(d)
            d.ssh.scp.put.assert_not_called()
            d.end.assert_not_called()

    def test_legacy_program_checks_transfer_then_char_and_status(self):
        d = self.device()
        reply = d.ssh.execute.return_value
        d.ssh.execute.side_effect = [reply] + [(0, '', '')] * 6
        report = candidate.legacy_program(d)
        self.assertTrue(report['programmed'])
        commands = [c.args[0] for c in d.ssh.execute.call_args_list]
        self.assertIn('sha256sum', commands[2])
        self.assertTrue(commands[4].startswith('test -c /dev/xdevcfg && cat '))
        self.assertEqual(commands[-1], 'ro')
        d.ssh.scp.put.assert_called_once()

    def test_program_failure_is_not_success_and_restores_ro(self):
        d = self.device()
        reply = d.ssh.execute.return_value
        d.ssh.execute.side_effect = [reply, (0, '', ''), (0, '', ''),
                                    (0, '', ''), (1, '', 'load failed'), (0, '', '')]
        with self.assertRaisesRegex(ExpectedPyrplError, 'load failed'):
            candidate.legacy_program(d)
        self.assertEqual(d.ssh.execute.call_args.args[0], 'ro')


if __name__ == '__main__':
    unittest.main()
