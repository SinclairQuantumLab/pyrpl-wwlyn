"""OS2-specific candidate selection; no network or device access."""
import unittest
from unittest.mock import patch

from pyrpl.errors import ExpectedPyrplError
from pyrpl.redpitaya import RedPitaya
from pyrpl.test.test_redpitaya_fpga_loader import make_device
from pyrpl.z10_repaired import (Z10_REPAIRED_BITSTREAM_FILENAME,
                                Z10_REPAIRED_BITSTREAM_SHA256)


class TestRepairedOS2(unittest.TestCase):
    def test_both_installed_overlay_basenames(self):
        for basename in ('fpga.bit.bin', 'fpga.bin'):
            d = make_device(overlay_fpga_filename=basename)
            report = d.preflight_fpga_update(Z10_REPAIRED_BITSTREAM_FILENAME)
            self.assertEqual(report['local_bitstream_sha256'], Z10_REPAIRED_BITSTREAM_SHA256)
            self.assertEqual(report['bitstream_lineage'], 'common-pid-repaired')
            self.assertEqual(report['remote_bitstream'], '/opt/pyrpl/' + basename)
            self.assertFalse(d.ssh.scp.uploads)
            with patch('pyrpl.redpitaya.sleep'):
                d.update_fpga(Z10_REPAIRED_BITSTREAM_FILENAME)
            self.assertEqual(len(d.ssh.scp.uploads), 2)
            self.assertIn('repaired', d.ssh.scp.uploads[0][0])

    def test_repaired_image_does_not_expand_hardware_profiles(self):
        for opts in ({'profile_id': '20', 'profile_fpga': 'z10_125_v2'},
                     {'profile_id': '21', 'profile_fpga': 'z20_125_v2', 'profile_zynq': 'Z7020'},
                     {'profile_id': '2', 'profile_zynq': 'Z7020'}):
            d = make_device(**opts)
            with self.assertRaises(ExpectedPyrplError):
                d.update_fpga(Z10_REPAIRED_BITSTREAM_FILENAME)
            self.assertFalse(d.ssh.scp.uploads)
            self.assertNotIn('rw', d.ssh.commands)

    def test_default_remains_author(self):
        report = make_device().preflight_fpga_update()
        self.assertEqual(report['bitstream_lineage'], 'preserved-author')
        self.assertIsNone(report['repaired_rtl_commit'])


if __name__ == '__main__':
    unittest.main()
