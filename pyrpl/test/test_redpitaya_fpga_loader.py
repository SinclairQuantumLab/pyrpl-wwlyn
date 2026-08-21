"""Offline regression tests for Red Pitaya FPGA loading compatibility."""

import hashlib
import logging
import os
from pathlib import Path
import tempfile
import unittest

import pyrpl.redpitaya as redpitaya_module
from pyrpl.attributes import FilterRegister
from pyrpl.errors import ExpectedPyrplError
from pyrpl.redpitaya import RedPitaya, defaultparameters


class FakeScp(object):
    def __init__(self):
        self.uploads = []

    def put(self, source, destination):
        self.uploads.append((source, destination))


class FakeSsh(object):
    def __init__(self, version_text='', xdevcfg_is_character=True,
                 overlay_succeeds=True, legacy_load_succeeds=True,
                 delay_legacy_marker=False):
        self.version_text = version_text
        self.xdevcfg_is_character = xdevcfg_is_character
        self.overlay_succeeds = overlay_succeeds
        self.legacy_load_succeeds = legacy_load_succeeds
        self.delay_legacy_marker = delay_legacy_marker
        self.pending_output = ''
        self.commands = []
        self.scp = FakeScp()
        self.hostname = 'redpitaya.test'

    def ask(self, command=''):
        self.commands.append(command)
        if command == '' and self.pending_output:
            output = self.pending_output
            self.pending_output = ''
            return output
        if command == 'cat /root/.version':
            return self.version_text
        if 'PYRPL_XDEVCFG_LOAD_' in command:
            marker = ('PYRPL_XDEVCFG_LOAD_OK' if self.legacy_load_succeeds
                      else 'PYRPL_XDEVCFG_LOAD_FAILED')
            if self.delay_legacy_marker:
                self.pending_output = marker
                return command
            return command + '\n' + marker
        if 'PYRPL_XDEVCFG_' in command:
            if self.xdevcfg_is_character:
                marker = 'PYRPL_XDEVCFG_OK'
            else:
                marker = 'PYRPL_XDEVCFG_MISSING'
            return command + '\n' + marker
        if 'PYRPL_OVERLAY_' in command:
            marker = ('PYRPL_OVERLAY_OK' if self.overlay_succeeds else
                      'PYRPL_OVERLAY_FAILED')
            return command + '\n' + marker
        if command == 'cat /tmp/update_fpga.txt':
            return 'overlay loaded'
        if command == 'cat /sys/class/fpga_manager/fpga0/state 2>&1':
            return 'operating'
        return ''


class ZeroMetadataClient(object):
    def __init__(self):
        self.read_requests = []

    def reads(self, address, length):
        self.read_requests.append((address, length))
        return [0] * length


class ZeroRegisterModule(object):
    name = 'iq1'

    def _read(self, _address):
        return 0


def make_device(version_text='', xdevcfg_is_character=True,
                overlay_succeeds=True, legacy_load_succeeds=True,
                delay_legacy_marker=False):
    """Construct a RedPitaya without opening a network connection."""
    device = RedPitaya.__new__(RedPitaya)
    device.logger = logging.getLogger(__name__)
    device.parameters = defaultparameters.copy()
    device.parameters.update({
        'delay': 0,
        'serverdirname': '/opt/pyrpl/',
    })
    device.c = {}
    device.ssh = FakeSsh(version_text, xdevcfg_is_character,
                         overlay_succeeds,
                         legacy_load_succeeds, delay_legacy_marker)
    device.client = None
    device.end = lambda: device.ssh.commands.append('__PYRPL_END__')
    device.start_ssh = lambda: None
    return device


class TestRedPitayaFpgaLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._original_sleep = redpitaya_module.sleep
        redpitaya_module.sleep = lambda _seconds: None

    @classmethod
    def tearDownClass(cls):
        redpitaya_module.sleep = cls._original_sleep

    def test_packaged_z10_assets_match_live_verified_pair(self):
        fpga_directory = Path(redpitaya_module.__file__).parent / 'fpga'
        expected = {
            'red_pitaya.bin':
                '4894f44b7611f2f0cbc18d339596f28476e452de1bac01a30206864ccd92fffe',
            'red_pitaya.dtbo':
                '9c19b99bef128d6069d44e8294ce6f118ee8513e523673ec02e1510d76877020',
        }
        for filename, expected_hash in expected.items():
            digest = hashlib.sha256(
                (fpga_directory / filename).read_bytes()).hexdigest()
            self.assertEqual(expected_hash, digest)

    def test_os_version_parsing(self):
        device = make_device('Red Pitaya OS 2.00-30\n')
        self.assertEqual('2.00', device.get_os_version())

        device.ssh.version_text = 'Release: 3.0.1-42'
        self.assertEqual('3.0.1', device.get_os_version())

        device.ssh.version_text = 'legacy image 1.04-18'
        self.assertEqual('1.04', device.get_os_version())

        device.ssh.version_text = 'unversioned development image'
        self.assertEqual('unknown', device.get_os_version())

    def test_os_compatibility_requires_firmware_loader_names(self):
        device = make_device()
        device.parameters['serverbinfilename'] = 'saved-name.bin'
        device.parameters['serverdirname'] = '/tmp/custom/'
        device.parameters['serverdtbofilename'] = 'custom.dtbo'
        device.parameters['dtbo_filename'] = ''

        device.os_version = '2.00'
        device._configure_os_compatibility()
        self.assertEqual('fpga.bit.bin',
                         device.parameters['serverbinfilename'])
        self.assertEqual('/opt/pyrpl/',
                         device.parameters['serverdirname'])
        self.assertEqual('fpga.dtbo',
                         device.parameters['serverdtbofilename'])
        self.assertEqual('fpga/red_pitaya.dtbo',
                         device.parameters['dtbo_filename'])
        self.assertEqual('fpga.bit.bin',
                         device.c['redpitaya']['serverbinfilename'])

        device.os_version = '3.0.1'
        device._configure_os_compatibility()
        self.assertEqual('fpga.bin', device.parameters['serverbinfilename'])

        device.parameters['serverbinfilename'] = 'legacy.bin'
        device.os_version = '1.04'
        device._configure_os_compatibility()
        self.assertEqual('legacy.bin',
                         device.parameters['serverbinfilename'])

    def test_os2_uses_overlay_loader_instead_of_xdevcfg(self):
        device = make_device()
        device.os_version = '2.00'
        device._configure_os_compatibility()

        with tempfile.TemporaryDirectory() as directory:
            bitstream = os.path.join(directory, 'custom.bin')
            dtbo = os.path.join(directory, 'custom.dtbo')
            with open(bitstream, 'wb') as output:
                output.write(b'bitstream')
            with open(dtbo, 'wb') as output:
                output.write(b'device tree overlay')

            device.update_fpga(filename=bitstream, dtbo_filename=dtbo)

        overlay_commands = [command for command in device.ssh.commands
                            if 'overlay.sh' in command]
        self.assertEqual(1, len(overlay_commands))
        self.assertIn('/opt/pyrpl/fpga.bit.bin', overlay_commands[0])
        self.assertIn('/opt/pyrpl/fpga.dtbo', overlay_commands[0])
        self.assertFalse(any('> /dev/xdevcfg' in command
                             for command in device.ssh.commands))
        self.assertTrue(any(destination.endswith('/fpga.bit.bin')
                            for _source, destination in
                            device.ssh.scp.uploads))

    def test_os2_uses_matching_bundled_dtbo_by_default(self):
        device = make_device()
        device.os_version = '2.07'
        device._configure_os_compatibility()

        with tempfile.TemporaryDirectory() as directory:
            bitstream = os.path.join(directory, 'custom.bin')
            with open(bitstream, 'wb') as output:
                output.write(b'bitstream')
            device.update_fpga(filename=bitstream)

        overlay_commands = [command for command in device.ssh.commands
                            if 'overlay.sh' in command]
        self.assertTrue(overlay_commands[0].startswith(
            '/opt/redpitaya/sbin/overlay.sh pyrpl '
            '/opt/pyrpl/fpga.bit.bin'))
        self.assertIn('PYRPL_OVERLAY_""OK', overlay_commands[0])
        self.assertNotIn('PYRPL_OVERLAY_OK', overlay_commands[0])
        self.assertIn('/opt/pyrpl/fpga.dtbo', overlay_commands[0])
        self.assertEqual(2, len(device.ssh.scp.uploads))
        self.assertTrue(any(source.endswith('red_pitaya.dtbo') and
                            destination.endswith('/fpga.dtbo')
                            for source, destination in device.ssh.scp.uploads))

    def test_os2_requires_a_matching_local_dtbo(self):
        device = make_device()
        device.os_version = '2.07'
        device._configure_os_compatibility()
        device.parameters['dtbo_filename'] = 'fpga/does-not-exist.dtbo'

        with tempfile.TemporaryDirectory() as directory:
            bitstream = os.path.join(directory, 'custom.bin')
            with open(bitstream, 'wb') as output:
                output.write(b'bitstream')
            with self.assertRaises(OSError) as raised:
                device.update_fpga(filename=bitstream)

        self.assertIn('device-tree overlay not found',
                      str(raised.exception))
        self.assertEqual([], device.ssh.scp.uploads)

    def test_os2_rejects_failed_overlay_even_if_manager_is_operating(self):
        device = make_device(overlay_succeeds=False)
        device.os_version = '2.07'
        device._configure_os_compatibility()

        with tempfile.TemporaryDirectory() as directory:
            bitstream = os.path.join(directory, 'custom.bin')
            with open(bitstream, 'wb') as output:
                output.write(b'bitstream')
            with self.assertRaises(OSError) as raised:
                device.update_fpga(filename=bitstream)

        self.assertIn('FPGA overlay loading failed', str(raised.exception))

    def test_legacy_loader_refuses_non_character_xdevcfg(self):
        device = make_device(xdevcfg_is_character=False)
        device.os_version = '1.04'
        device.parameters['serverbinfilename'] = 'legacy.bin'

        with tempfile.TemporaryDirectory() as directory:
            bitstream = os.path.join(directory, 'legacy.bin')
            with open(bitstream, 'wb') as output:
                output.write(b'bitstream')

            with self.assertRaises(OSError) as raised:
                device.update_fpga(filename=bitstream)

        self.assertIn('/dev/xdevcfg character device', str(raised.exception))
        self.assertTrue(any('[ -c /dev/xdevcfg ]' in command
                            for command in device.ssh.commands))
        self.assertFalse(any(command.startswith('cat ') and
                             '> /dev/xdevcfg' in command
                             for command in device.ssh.commands))

    def test_legacy_loader_rejects_nonzero_write_result(self):
        device = make_device(legacy_load_succeeds=False)
        device.os_version = '1.04'
        device.parameters['serverbinfilename'] = 'legacy.bin'

        with tempfile.TemporaryDirectory() as directory:
            bitstream = os.path.join(directory, 'legacy.bin')
            with open(bitstream, 'wb') as output:
                output.write(b'bitstream')
            with self.assertRaises(OSError) as raised:
                device.update_fpga(filename=bitstream)

        self.assertIn('Legacy FPGA loading failed', str(raised.exception))

    def test_legacy_loader_waits_for_delayed_completion_marker(self):
        device = make_device(delay_legacy_marker=True)
        device.os_version = '1.04'
        device.parameters['serverbinfilename'] = 'legacy.bin'

        with tempfile.TemporaryDirectory() as directory:
            bitstream = os.path.join(directory, 'legacy.bin')
            with open(bitstream, 'wb') as output:
                output.write(b'bitstream')
            device.update_fpga(filename=bitstream)

        self.assertTrue(any(command == '' for command in
                            device.ssh.commands))

    def test_zero_fpga_metadata_is_an_expected_error(self):
        device = make_device()
        device.os_version = '2.00'
        device.client = ZeroMetadataClient()

        with self.assertRaises(ExpectedPyrplError) as raised:
            device._validate_fpga_compatibility()

        self.assertIn('not running a compatible PyRPL FPGA image',
                      str(raised.exception))
        self.assertIn('minimum bandwidth', str(raised.exception))
        self.assertEqual(4, len(device.client.read_requests))
        self.assertTrue(all(length == 1 for _address, length in
                            device.client.read_requests))

    def test_zero_filter_minimum_bandwidth_has_actionable_error(self):
        register = FilterRegister(address=0x124, filterstages=0x230,
                                  shiftbits=0x234, minbw=0x238)
        register.name = 'bandwidth'

        with self.assertRaises(ExpectedPyrplError) as raised:
            register._MAXSHIFT(ZeroRegisterModule())

        self.assertIn('not running a compatible PyRPL FPGA image',
                      str(raised.exception))
        self.assertNotIsInstance(raised.exception, ZeroDivisionError)


if __name__ == '__main__':
    unittest.main()
