"""Offline tests of the separately pinned, unrepaired Pro test image."""

import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['REDPITAYA_HOSTNAME'] = '_FAKE_'
_USER_DIR = tempfile.TemporaryDirectory(prefix='pyrpl-author-loader-')
os.environ['PYRPL_USER_DIR'] = _USER_DIR.name

from pyrpl import redpitaya
from pyrpl.errors import ExpectedPyrplError
from pyrpl.test.test_redpitaya_fpga_loader import make_device


class TestAuthorLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (Path(redpitaya.__file__).parent /
                     redpitaya.Z20_AUTHOR_BITSTREAM_FILENAME)

    def device(self, **kwargs):
        settings = dict(profile_id='22', profile_fpga='z20_125_v2',
                        profile_zynq='Z7020')
        settings.update(kwargs)
        device = make_device(**settings)
        device.parameters['filename'] = str(self.image)
        device.detect_platform()
        return device

    def assert_no_mutation(self, device):
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)
        self.assertNotIn('__PYRPL_END__', device.ssh.commands)

    def test_separate_image_is_packaged_and_hash_pinned(self):
        digest = hashlib.sha256(self.image.read_bytes()).hexdigest()
        self.assertEqual(redpitaya.Z20_AUTHOR_BITSTREAM_SHA256, digest)
        self.assertNotEqual(redpitaya.FORK_BITSTREAM_SHA256, digest)

    def test_read_only_plan_selects_both_existing_firmware_name_contracts(self):
        for filename in ('fpga.bit.bin', 'fpga.bin'):
            with self.subTest(filename=filename):
                device = self.device(overlay_fpga_filename=filename)
                report = device.preflight_fpga_update()
                self.assertEqual('22', report['hardware_profile']['id'])
                self.assertEqual('pro-z7020', report['hardware_profile']['variant'])
                self.assertEqual(redpitaya.Z20_AUTHOR_BITSTREAM_SHA256,
                                 report['local_bitstream_sha256'])
                self.assertEqual(redpitaya.OS2_Z10_DTBO_SHA256[filename],
                                 report['local_dtbo_sha256'])
                self.assertIn('no-common-fixes', report['artifact_lineage'])
                self.assertFalse(report['timing_closed'])
                self.assert_no_mutation(device)

    def test_other_boards_and_mismatched_profile_fields_are_rejected(self):
        for pid, path, zynq in [('1', 'z10_125', 'Z7010'),
                               ('21', 'z10_125_pro_v2', 'Z7010'),
                               ('6', 'z20_125', 'Z7020'),
                               ('23', 'z20_125_v2', 'Z7020'),
                               ('22', 'z10_125', 'Z7020'),
                               ('22', 'z20_125_v2', 'Z7010')]:
            with self.subTest(profile=(pid, path, zynq)):
                device = self.device(profile_id=pid, profile_fpga=path,
                                     profile_zynq=zynq)
                with self.assertRaises(ExpectedPyrplError):
                    device.update_fpga()
                self.assert_no_mutation(device)

    def test_packaged_image_does_not_depend_on_working_directory(self):
        device = self.device()
        device.parameters['filename'] = redpitaya.Z20_AUTHOR_BITSTREAM_FILENAME
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                report = device.preflight_fpga_update()
            finally:
                os.chdir(previous)
        self.assertEqual(str(self.image), report['local_bitstream'])
        self.assert_no_mutation(device)

    def test_mock_load_uploads_the_z7020_image_and_matching_overlay(self):
        for filename in ('fpga.bit.bin', 'fpga.bin'):
            with self.subTest(filename=filename):
                device = self.device(overlay_fpga_filename=filename)
                with patch.object(redpitaya, 'sleep', lambda seconds: None):
                    report = device.update_fpga()
                self.assertEqual(2, len(device.ssh.scp.uploads))
                self.assertEqual(str(self.image), device.ssh.scp.uploads[0][0])
                self.assertIn('/opt/pyrpl/' + filename, device.ssh.scp.uploads[0][1])
                self.assertIn('operating', report['manager_state'])

    def test_original_z7010_bin_still_cannot_be_loaded_on_z7020(self):
        device = self.device()
        device.parameters['filename'] = redpitaya.defaultparameters['filename']
        with self.assertRaises(ExpectedPyrplError):
            device.update_fpga()
        self.assert_no_mutation(device)

    def test_z7020_image_cannot_use_the_legacy_loader(self):
        device = self.device(ecosystem_text='Red Pitaya OS 1.04-18',
                             overlay_available=False, xdevcfg_available=True)
        with self.assertRaises(ExpectedPyrplError):
            device.update_fpga()
        self.assert_no_mutation(device)

    def test_changed_image_is_rejected_before_upload(self):
        device = self.device()
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / self.image.name
            data = bytearray(self.image.read_bytes())
            data[-1] ^= 1
            bad.write_bytes(data)
            with self.assertRaises(OSError):
                device.update_fpga(filename=str(bad))
        self.assert_no_mutation(device)


if __name__ == '__main__':
    unittest.main()
