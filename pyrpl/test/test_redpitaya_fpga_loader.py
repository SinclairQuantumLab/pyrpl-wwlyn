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
from pyrpl.sshshell import SshShell


class FakeScp(object):
    def __init__(self):
        self.uploads = []

    def put(self, source, destination):
        self.uploads.append((source, destination))


class FakeSsh(object):
    def __init__(self, ecosystem_text='Red Pitaya OS 2.07-48',
                 root_text='Ubuntu image 1.07', overlay_available=True,
                 xdevcfg_available=False, profile_id='1',
                 profile_fpga='z10_125', profile_zynq='Z7010',
                 overlay_fpga_filename='fpga.bit.bin',
                 overlay_succeeds=True, manager_state='operating',
                 loaded_info=None,
                 legacy_load_succeeds=True, omitted_markers=()):
        self.ecosystem_text = ecosystem_text
        self.root_text = root_text
        self.overlay_available = overlay_available
        self.xdevcfg_available = xdevcfg_available
        self.profile_id = profile_id
        self.profile_fpga = profile_fpga
        self.profile_zynq = profile_zynq
        self.overlay_fpga_filename = overlay_fpga_filename
        self.overlay_succeeds = overlay_succeeds
        self.manager_state = manager_state
        self.loaded_info = (
            loaded_info if loaded_info is not None else
            'pyrpl_/opt/pyrpl/%s_/opt/pyrpl/fpga.dtbo' %
            overlay_fpga_filename)
        self.legacy_load_succeeds = legacy_load_succeeds
        self.omitted_markers = set(omitted_markers)
        self.commands = []
        self.executed_commands = []
        self.pending_output = ''
        self.scp = FakeScp()
        self.hostname = 'redpitaya.test'

    def ask(self, command=''):
        self.commands.append(command)
        if command == '' and self.pending_output:
            output = self.pending_output
            self.pending_output = ''
            return output
        if command.startswith('cat /opt/redpitaya/version.txt 2>/dev/null;'):
            output = command + '\n' + self.ecosystem_text
            if 'ecosystem_version' not in self.omitted_markers:
                output += '\nPYRPL_ECOSYSTEM_VERSION_END'
            return output
        if command.startswith('cat /root/.version 2>/dev/null;'):
            output = command + '\n' + self.root_text
            if 'root_version' not in self.omitted_markers:
                output += '\nPYRPL_ROOT_VERSION_END'
            return output
        if 'PYRPL_OVERLAY_AVAILABLE' in command and 'PYRPL_XDEVCFG_AVAILABLE' in command:
            overlay = ('PYRPL_OVERLAY_AVAILABLE' if self.overlay_available
                       else 'PYRPL_OVERLAY_MISSING')
            xdevcfg = ('PYRPL_XDEVCFG_AVAILABLE' if self.xdevcfg_available
                       else 'PYRPL_XDEVCFG_MISSING')
            output = command + '\n' + overlay + '\n' + xdevcfg
            if 'capabilities' not in self.omitted_markers:
                output += '\nPYRPL_CAPABILITIES_END'
            return output
        if 'PYRPL_OVERLAY_' in command:
            marker = ('PYRPL_OVERLAY_OK' if self.overlay_succeeds else
                      'PYRPL_OVERLAY_FAILED')
            return command + '\n' + marker
        if command == 'cat /tmp/update_fpga.txt 2>&1':
            return ('overlay loaded' if self.overlay_succeeds else
                    'FPGA loading failed')
        if command == 'cat /tmp/loaded_fpga.inf 2>&1':
            return self.loaded_info
        if command == 'cat /sys/class/fpga_manager/fpga0/state 2>&1':
            return self.manager_state
        if 'PYRPL_XDEVCFG_LOAD_' in command:
            marker = ('PYRPL_XDEVCFG_LOAD_OK'
                      if self.legacy_load_succeeds else
                      'PYRPL_XDEVCFG_LOAD_FAILED')
            return command + '\n' + marker
        if 'PYRPL_XDEVCFG_' in command:
            marker = ('PYRPL_XDEVCFG_OK' if self.xdevcfg_available else
                      'PYRPL_XDEVCFG_MISSING')
            return command + '\n' + marker
        return ''

    def execute(self, command):
        self.commands.append(command)
        self.executed_commands.append(command)
        if command.startswith(
                "grep '^[[:space:]]*CUSTOMFPGA[[:space:]]*=' "):
            if 'overlay_script' in self.omitted_markers:
                raise TimeoutError('simulated non-interactive SSH timeout')
            if self.overlay_fpga_filename is None:
                return 1, '', ''
            return (0,
                    'CUSTOMFPGA=/opt/$1/' + self.overlay_fpga_filename + '\n',
                    '')
        if 'PYRPL_PROFILE_ID:' in command:
            if 'profile' in self.omitted_markers:
                raise TimeoutError('simulated non-interactive SSH timeout')
            output = ('PYRPL_PROFILE_ID:' + self.profile_id +
                      '\nPYRPL_PROFILE_FPGA:' + self.profile_fpga +
                      '\nPYRPL_PROFILE_ZYNQ:' + self.profile_zynq + '\n')
            return 0, output, ''
        if 'PYRPL_PREFLIGHT_UPTIME:' in command:
            if 'preflight' in self.omitted_markers:
                raise TimeoutError('simulated non-interactive SSH timeout')
            output = ('PYRPL_PREFLIGHT_UPTIME:1234.5'
                      '\nPYRPL_PREFLIGHT_MANAGER:' + self.manager_state +
                      '\nPYRPL_PREFLIGHT_LOADED:' + self.loaded_info + '\n')
            return 0, output, ''
        return 127, '', 'unsupported fake command'


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


def make_device(**ssh_kwargs):
    """Construct a RedPitaya without opening a network connection."""
    device = RedPitaya.__new__(RedPitaya)
    device.logger = logging.getLogger(__name__)
    device.parameters = defaultparameters.copy()
    device.parameters['delay'] = 0
    device.c = {}
    device.ssh = FakeSsh(**ssh_kwargs)
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

    def test_noninteractive_ssh_command_returns_exact_streams_and_status(self):
        class FakeChannel(object):
            def recv_exit_status(self):
                return 7

        class FakeStream(object):
            def __init__(self, data=b''):
                self.data = data
                self.channel = FakeChannel()

            def close(self):
                pass

            def read(self):
                return self.data

        class FakeClient(object):
            def __init__(self):
                self.calls = []

            def exec_command(self, command, timeout=None):
                self.calls.append((command, timeout))
                return (FakeStream(), FakeStream(b'output\n'),
                        FakeStream(b'diagnostic\n'))

            def close(self):
                pass

        shell = SshShell.__new__(SshShell)
        shell._logger = logging.getLogger(__name__)
        shell.timeout = 3
        shell.ssh = FakeClient()

        status, output, error = shell.execute('read-only-command')

        self.assertEqual(7, status)
        self.assertEqual('output\n', output)
        self.assertEqual('diagnostic\n', error)
        self.assertEqual([('read-only-command', 3)], shell.ssh.calls)

    def test_packaged_fpga_assets_are_the_fork_pair(self):
        fpga_directory = Path(redpitaya_module.__file__).parent / 'fpga'
        bitstream = fpga_directory / 'red_pitaya.bin'
        bit_dtbo = fpga_directory / 'red_pitaya_os2_z10.dtbo'
        bin_dtbo = fpga_directory / 'red_pitaya_os2_z10_fpga_bin.dtbo'
        bit_dts = fpga_directory / 'red_pitaya_os2_z10.dts'
        bin_dts = fpga_directory / 'red_pitaya_os2_z10_fpga_bin.dts'
        self.assertEqual(
            'dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed',
            hashlib.sha256(bitstream.read_bytes()).hexdigest())
        self.assertEqual(
            '41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9',
            hashlib.sha256(bit_dtbo.read_bytes()).hexdigest())
        self.assertEqual(
            '99f0fd0c3ce394fb0c86e4dec95895b8a5855cc80ebbfd5fedc961fb9ed4a35c',
            hashlib.sha256(bin_dtbo.read_bytes()).hexdigest())
        self.assertEqual(
            bit_dts.read_text().replace('fpga.bit.bin', 'fpga.bin'),
            bin_dts.read_text())
        self.assertEqual('fpga/red_pitaya.bin', defaultparameters['filename'])
        self.assertEqual('fpga/red_pitaya_os2_z10.dtbo',
                         defaultparameters['dtbo_filename'])

    def test_dtbo_matches_direct_xadc_fork_design(self):
        fpga_directory = Path(redpitaya_module.__file__).parent / 'fpga'
        variants = (
            ('red_pitaya_os2_z10.dtbo', 'red_pitaya_os2_z10.dts',
             b'fpga.bit.bin\x00'),
            ('red_pitaya_os2_z10_fpga_bin.dtbo',
             'red_pitaya_os2_z10_fpga_bin.dts', b'fpga.bin\x00'),
        )
        for dtbo_name, dts_name, firmware_name in variants:
            with self.subTest(dtbo_name=dtbo_name):
                data = (fpga_directory / dtbo_name).read_bytes()
                source = (fpga_directory / dts_name).read_text()
                for value in (firmware_name, b'clocking0\x00',
                              b'clocking1\x00', b'clocking2\x00',
                              b'clocking3\x00', b'afi0@f8008000\x00',
                              b'afi1@f8009000\x00', b'__fixups__\x00',
                              b'fpga_full\x00', b'amba\x00', b'clkc\x00'):
                    self.assertIn(value, data)
                for value in (b'xadc_wiz', b'xlnx,axi-xadc',
                              b'xlnx,xadc-wiz'):
                    self.assertNotIn(value, data)
                self.assertIn('rtl/red_pitaya_ams.v', source)
                self.assertNotIn('xadc_wiz@83c00000', source)

    def test_built_in_assets_do_not_depend_on_working_directory(self):
        device = make_device()
        expected = (Path(redpitaya_module.__file__).parent /
                    defaultparameters['filename']).resolve()
        with tempfile.TemporaryDirectory() as temporary_directory:
            previous_directory = os.getcwd()
            try:
                os.chdir(temporary_directory)
                resolved = device._local_fpga_file(
                    defaultparameters['filename'], 'FPGA bitstream',
                    package_relative=True)
            finally:
                os.chdir(previous_directory)
        self.assertEqual(expected, Path(resolved))

    def test_custom_relative_asset_uses_working_directory(self):
        device = make_device()
        with tempfile.TemporaryDirectory() as temporary_directory:
            custom_file = Path(temporary_directory) / 'custom.bin'
            custom_file.write_bytes(b'custom')
            previous_directory = os.getcwd()
            try:
                os.chdir(temporary_directory)
                resolved = device._local_fpga_file(
                    'custom.bin', 'FPGA bitstream', package_relative=False)
            finally:
                os.chdir(previous_directory)
            self.assertEqual(custom_file, Path(resolved))

    def test_ecosystem_version_wins_over_misleading_root_version(self):
        device = make_device(
            ecosystem_text='Red Pitaya GNU/Linux ecosystem version 1.04-18',
            root_text='Red Pitaya Linux 1.07',
            overlay_available=False, xdevcfg_available=True)
        self.assertEqual('1.04-18', device.get_os_version())
        self.assertEqual('/opt/redpitaya/version.txt',
                         device.os_version_source)

    def test_complete_missing_ecosystem_version_falls_back_to_root(self):
        device = make_device(
            ecosystem_text='version file unavailable',
            root_text='Red Pitaya Linux 1.07',
            overlay_available=False, xdevcfg_available=True)
        self.assertEqual('legacy', device.detect_platform())
        self.assertEqual('1.07', device.os_version)
        self.assertEqual('/root/.version', device.os_version_source)

    def test_os207_plus_selects_recognized_overlay_contracts(self):
        for ecosystem_text, fpga_filename in (
                ('Red Pitaya OS 2.07-48', 'fpga.bit.bin'),
                ('Red Pitaya OS 2.08-1', 'fpga.bin')):
            with self.subTest(fpga_filename=fpga_filename):
                device = make_device(
                    ecosystem_text=ecosystem_text,
                    overlay_fpga_filename=fpga_filename)
                self.assertEqual('overlay', device.detect_platform())
                self.assertEqual(fpga_filename,
                                 device.os2_fpga_filename)
                overlay_probe = [
                    command for command in device.ssh.commands
                    if command.startswith(
                        "grep '^[[:space:]]*CUSTOMFPGA[[:space:]]*=' ")]
                self.assertEqual(1, len(overlay_probe))
                self.assertNotIn('cat /opt/redpitaya/sbin/overlay.sh',
                                 overlay_probe[0])
                self.assertNotIn('PYRPL_OVERLAY_SCRIPT_END',
                                 overlay_probe[0])
                self.assertIn(overlay_probe[0],
                              device.ssh.executed_commands)

        legacy = make_device(
            ecosystem_text='ecosystem version 1.04-18',
            root_text='Linux image 1.07', overlay_available=False,
            xdevcfg_available=True)
        self.assertEqual('legacy', legacy.detect_platform())

    def test_os207_plus_loads_matching_fixed_bin_and_dtbo_paths(self):
        for ecosystem_text, fpga_filename, dtbo_basename in (
                ('Red Pitaya OS 2.07-48', 'fpga.bit.bin',
                 'red_pitaya_os2_z10.dtbo'),
                ('Red Pitaya OS 2.08-1', 'fpga.bin',
                 'red_pitaya_os2_z10_fpga_bin.dtbo')):
            with self.subTest(fpga_filename=fpga_filename):
                device = make_device(
                    ecosystem_text=ecosystem_text,
                    overlay_fpga_filename=fpga_filename)
                device.detect_platform()
                result = device.update_fpga()

                overlay_commands = [
                    command for command in device.ssh.commands
                    if 'overlay.sh pyrpl' in command]
                self.assertEqual(1, len(overlay_commands))
                bin_path = '/opt/pyrpl/' + fpga_filename
                self.assertIn(bin_path, overlay_commands[0])
                self.assertIn('/opt/pyrpl/fpga.dtbo', overlay_commands[0])
                self.assertFalse(any('> /dev/xdevcfg' in command
                                     for command in device.ssh.commands))
                sources = [Path(source).name for source, _destination
                           in device.ssh.scp.uploads]
                destinations = [destination for _source, destination
                                in device.ssh.scp.uploads]
                self.assertEqual([dtbo_basename], sources[1:])
                self.assertEqual([bin_path, '/opt/pyrpl/fpga.dtbo'],
                                 destinations)
                self.assertEqual(fpga_filename,
                                 result['fpga_filename'])
                self.assertIn('operating', result['manager_state'])

    def test_os207_plus_preflight_is_read_only_and_matches_update(self):
        for ecosystem_text, fpga_filename, dtbo_basename, dtbo_digest in (
                ('Red Pitaya OS 2.07-48', 'fpga.bit.bin',
                 'red_pitaya_os2_z10.dtbo',
                 '41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9'),
                ('Red Pitaya OS 2.08-1', 'fpga.bin',
                 'red_pitaya_os2_z10_fpga_bin.dtbo',
                 '99f0fd0c3ce394fb0c86e4dec95895b8a5855cc80ebbfd5fedc961fb9ed4a35c')):
            with self.subTest(fpga_filename=fpga_filename):
                device = make_device(
                    ecosystem_text=ecosystem_text,
                    overlay_fpga_filename=fpga_filename)
                report = device.preflight_fpga_update()

                self.assertTrue(report['read_only'])
                self.assertEqual('overlay', report['loader'])
                self.assertEqual(fpga_filename, report['fpga_filename'])
                self.assertEqual(
                    {'id': '1', 'fpga': 'z10_125', 'zynq': 'Z7010'},
                    report['hardware_profile'])
                self.assertEqual(dtbo_basename,
                                 Path(report['local_dtbo']).name)
                self.assertEqual(dtbo_digest,
                                 report['local_dtbo_sha256'])
                self.assertEqual(
                    'dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed',
                    report['local_bitstream_sha256'])
                self.assertEqual('/opt/pyrpl/' + fpga_filename,
                                 report['remote_bitstream'])
                self.assertEqual('/opt/pyrpl/fpga.dtbo',
                                 report['remote_dtbo'])
                self.assertEqual('1234.5', report['uptime_seconds'])
                self.assertEqual('operating',
                                 report['fpga_manager_state'])
                self.assertEqual([], device.ssh.scp.uploads)
                self.assertNotIn('rw', device.ssh.commands)
                self.assertNotIn('__PYRPL_END__', device.ssh.commands)
                self.assertFalse(any(
                    'overlay.sh pyrpl ' in command
                    for command in device.ssh.commands))
                self.assertFalse(any(
                    'killall nginx' in command
                    for command in device.ssh.commands))
                allowed_prefixes = (
                    'cat /opt/redpitaya/version.txt 2>/dev/null;',
                    'cat /root/.version 2>/dev/null;',
                    'if [ -x /opt/redpitaya/sbin/overlay.sh ];',
                    "grep '^[[:space:]]*CUSTOMFPGA[[:space:]]*=' ",
                    "printf 'PYRPL_PROFILE_ID:';",
                    "printf 'PYRPL_PREFLIGHT_UPTIME:';",
                )
                self.assertTrue(all(
                    command == '' or command.startswith(allowed_prefixes)
                    for command in device.ssh.commands),
                    device.ssh.commands)

    def test_missing_dtbo_fails_before_device_mutation(self):
        device = make_device()
        device.parameters['dtbo_filename'] = 'fpga/does-not-exist.dtbo'
        device.detect_platform()
        with self.assertRaises(OSError) as raised:
            device.update_fpga()
        self.assertIn('device-tree overlay not found',
                      str(raised.exception))
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)
        self.assertNotIn('__PYRPL_END__', device.ssh.commands)

    def test_unapproved_os2_assets_fail_before_device_mutation(self):
        fpga_directory = Path(redpitaya_module.__file__).parent / 'fpga'
        with tempfile.TemporaryDirectory() as temporary_directory:
            wrong_bitstream = Path(temporary_directory) / 'wrong.bin'
            wrong_bitstream.write_bytes(b'not the fork image')
            wrong_dtbo = Path(temporary_directory) / 'wrong.dtbo'
            wrong_dtbo.write_bytes(
                (fpga_directory / 'red_pitaya_os2_z10.dtbo').read_bytes() +
                b'changed')

            for filename, dtbo_filename, expected_message in (
                    (str(wrong_bitstream), None,
                     'does not match this fork\'s preserved FPGA image'),
                    (None, str(wrong_dtbo),
                     'does not match this fork\'s approved Z7010')):
                with self.subTest(expected_message=expected_message):
                    device = make_device()
                    device.detect_platform()
                    with self.assertRaises(OSError) as raised:
                        device.update_fpga(
                            filename=filename, dtbo_filename=dtbo_filename)
                    self.assertIn(expected_message, str(raised.exception))
                    self.assertEqual([], device.ssh.scp.uploads)
                    self.assertNotIn('rw', device.ssh.commands)
                    self.assertNotIn('__PYRPL_END__', device.ssh.commands)

    def test_cross_paired_os2_overlay_fails_before_device_mutation(self):
        old_dtbo = (Path(redpitaya_module.__file__).parent / 'fpga' /
                    'red_pitaya_os2_z10.dtbo')
        device = make_device(
            ecosystem_text='Red Pitaya OS 2.08-1',
            overlay_fpga_filename='fpga.bin')
        device.detect_platform()
        with self.assertRaises(OSError) as raised:
            device.update_fpga(dtbo_filename=str(old_dtbo))
        self.assertIn('approved Z7010 fpga.bin overlay',
                      str(raised.exception))
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)

    def test_os207_refuses_gen2_before_device_mutation(self):
        device = make_device(profile_id='20', profile_fpga='z10_125_v2')
        device.detect_platform()
        with self.assertRaises(ExpectedPyrplError) as raised:
            device.update_fpga()
        self.assertIn('does not yet authorize Gen 2', str(raised.exception))
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)
        self.assertNotIn('__PYRPL_END__', device.ssh.commands)

    def test_os207_refuses_z7020_before_device_mutation(self):
        device = make_device(profile_id='6', profile_fpga='z20_125',
                             profile_zynq='Z7020')
        device.detect_platform()
        with self.assertRaises(ExpectedPyrplError):
            device.update_fpga()
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)

    def test_early_os2_and_os3_are_not_silently_loaded(self):
        for ecosystem_text, overlay_available, fpga_filename in (
                ('Red Pitaya OS 2.05-37', False, 'fpga.bit.bin'),
                ('Red Pitaya OS 3.00-12', True, 'fpga.bin')):
            with self.subTest(ecosystem_text=ecosystem_text):
                device = make_device(
                    ecosystem_text=ecosystem_text,
                    overlay_available=overlay_available,
                    overlay_fpga_filename=fpga_filename,
                    xdevcfg_available=False)
                self.assertEqual('unsupported', device.detect_platform())
                with self.assertRaises(ExpectedPyrplError):
                    device.update_fpga()
                self.assertEqual([], device.ssh.scp.uploads)
                self.assertNotIn('rw', device.ssh.commands)

    def test_os207_requires_overlay_capability(self):
        device = make_device(overlay_available=False)
        self.assertEqual('unsupported', device.detect_platform())
        with self.assertRaises(ExpectedPyrplError) as raised:
            device.update_fpga()
        self.assertIn('overlay.sh is unavailable', str(raised.exception))

    def test_os207_plus_refuses_unknown_overlay_contract(self):
        device = make_device(
            ecosystem_text='Red Pitaya OS 2.08-1',
            overlay_fpga_filename=None)
        self.assertEqual('unsupported', device.detect_platform())
        with self.assertRaises(ExpectedPyrplError) as raised:
            device.update_fpga()
        self.assertIn('validated fpga.bit.bin/fpga.bin contracts',
                      str(raised.exception))
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)

    def test_incomplete_preflight_output_fails_before_device_mutation(self):
        for omitted_marker in ('ecosystem_version', 'capabilities',
                               'overlay_script', 'profile'):
            with self.subTest(omitted_marker=omitted_marker):
                device = make_device(
                    xdevcfg_available=True,
                    omitted_markers=(omitted_marker,))
                if omitted_marker == 'profile':
                    self.assertEqual('overlay', device.detect_platform())
                else:
                    self.assertEqual('unsupported', device.detect_platform())
                with self.assertRaises(ExpectedPyrplError):
                    device.update_fpga()
                self.assertEqual([], device.ssh.scp.uploads)
                self.assertNotIn('rw', device.ssh.commands)
                self.assertNotIn('__PYRPL_END__', device.ssh.commands)

        device = make_device(omitted_markers=('preflight',))
        with self.assertRaises(ExpectedPyrplError) as raised:
            device.preflight_fpga_update()
        self.assertIn('read-only FPGA preflight SSH command failed',
                      str(raised.exception))
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)
        self.assertNotIn('__PYRPL_END__', device.ssh.commands)

    def test_unknown_os_does_not_fall_back_to_xdevcfg(self):
        device = make_device(
            ecosystem_text='unparseable', root_text='also unparseable',
            overlay_available=False, xdevcfg_available=True)
        self.assertEqual('unsupported', device.detect_platform())
        with self.assertRaises(ExpectedPyrplError):
            device.update_fpga()
        self.assertEqual([], device.ssh.scp.uploads)
        self.assertNotIn('rw', device.ssh.commands)

    def test_failed_overlay_and_manager_state_are_rejected(self):
        failed = make_device(overlay_succeeds=False)
        failed.detect_platform()
        with self.assertRaises(OSError) as raised:
            failed.update_fpga()
        self.assertIn('FPGA overlay loading failed', str(raised.exception))

        not_operating = make_device(manager_state='write error')
        not_operating.detect_platform()
        with self.assertRaises(OSError) as raised:
            not_operating.update_fpga()
        self.assertIn('manager is not operating', str(raised.exception))

        wrong_identity = make_device(
            ecosystem_text='Red Pitaya OS 2.08-1',
            overlay_fpga_filename='fpga.bin',
            loaded_info='pyrpl_/opt/pyrpl/fpga.bit.bin_'
                        '/opt/pyrpl/fpga.dtbo')
        wrong_identity.detect_platform()
        with self.assertRaises(OSError) as raised:
            wrong_identity.update_fpga()
        self.assertIn('does not identify the expected custom PyRPL files',
                      str(raised.exception))

    def test_legacy_loader_requires_character_device_and_write_success(self):
        device = make_device(
            ecosystem_text='ecosystem 1.04-18', root_text='image 1.07',
            overlay_available=False, xdevcfg_available=True)
        device.detect_platform()
        device.update_fpga()
        self.assertTrue(any(command.startswith('cat ') and
                            '> /dev/xdevcfg' in command
                            for command in device.ssh.commands))

        failed = make_device(
            ecosystem_text='ecosystem 1.04-18', root_text='image 1.07',
            overlay_available=False, xdevcfg_available=True,
            legacy_load_succeeds=False)
        failed.detect_platform()
        with self.assertRaises(OSError) as raised:
            failed.update_fpga()
        self.assertIn('Legacy FPGA loading failed', str(raised.exception))

    def test_zero_fpga_metadata_is_an_actionable_error(self):
        device = make_device()
        device.os_version = '2.07-48'
        device.client = ZeroMetadataClient()
        with self.assertRaises(ExpectedPyrplError) as raised:
            device._validate_fpga_compatibility()
        self.assertIn("not running this fork's FPGA memory map",
                      str(raised.exception))
        self.assertEqual(4, len(device.client.read_requests))

    def test_zero_filter_minimum_bandwidth_is_an_actionable_error(self):
        register = FilterRegister(address=0x124, filterstages=0x230,
                                  shiftbits=0x234, minbw=0x238)
        register.name = 'bandwidth'
        with self.assertRaises(ExpectedPyrplError) as raised:
            register._MAXSHIFT(ZeroRegisterModule())
        self.assertIn("not running this fork's compatible FPGA image",
                      str(raised.exception))
        self.assertNotIsInstance(raised.exception, ZeroDivisionError)


if __name__ == '__main__':
    unittest.main()
