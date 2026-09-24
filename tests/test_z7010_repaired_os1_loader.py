"""Offline OS1 method wiring and non-interactive SSH regression checks."""
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import pyrpl
from pyrpl.redpitaya import RedPitaya, defaultparameters
from pyrpl.sshshell import SshShell
from pyrpl.z10_repaired import Z10_REPAIRED_BITSTREAM_FILENAME


class TestRepairedOS1(unittest.TestCase):
    def device(self):
        d = RedPitaya.__new__(RedPitaya)
        d.parameters = dict(defaultparameters, filename=Z10_REPAIRED_BITSTREAM_FILENAME)
        d.ssh = Mock()
        d.logger = Mock()
        d.end = Mock()
        return d

    def test_preflight_method_has_no_mutation(self):
        d = self.device()
        d.ssh.execute.return_value = (
            0, 'PYRPL_OS:version=1.04\nbuild=18\nPYRPL_HW:STEM_125-14_v1.1\nPYRPL_CHAR:yes\n', '')
        report = d.preflight_fpga_update()
        self.assertTrue(report['read_only'])
        d.ssh.ask.assert_not_called()
        d.end.assert_not_called()
        d.ssh.scp.put.assert_not_called()

    def test_explicit_and_configured_repaired_selection(self):
        for explicit in (True, False):
            d = self.device()
            with patch('pyrpl.redpitaya.legacy_program', return_value={'programmed': True}) as program:
                if explicit:
                    result = d.update_fpga(filename=Z10_REPAIRED_BITSTREAM_FILENAME)
                else:
                    result = d.update_fpga()
                self.assertTrue(result['programmed'])
                program.assert_called_once_with(d, Z10_REPAIRED_BITSTREAM_FILENAME)
            d.ssh.ask.assert_not_called()

    def test_original_explicit_filename_retains_original_loader_path(self):
        d = self.device()
        d.parameters['delay'] = 0
        path = str(Path(pyrpl.__file__).parent / 'fpga/red_pitaya.bin')
        with patch('pyrpl.redpitaya.sleep'), patch('pyrpl.redpitaya.legacy_program') as repaired:
            d.update_fpga(filename=path)
        repaired.assert_not_called()
        self.assertEqual(d.ssh.scp.put.call_args.args[0], path)

    def test_execute_uses_channel_exit_status_and_utf8(self):
        shell = SshShell.__new__(SshShell)
        shell._logger = Mock()
        shell.timeout = 10
        shell.ssh = Mock()
        shell.channel = Mock()
        stdin, stdout, stderr = Mock(), Mock(), Mock()
        stdout.read.return_value = b'output\n'
        stderr.read.return_value = b'error\n'
        stdout.channel.recv_exit_status.return_value = 7
        shell.ssh.exec_command.return_value = (stdin, stdout, stderr)
        self.assertEqual(shell.execute('read-only-probe'), (7, 'output\n', 'error\n'))
        shell.ssh.exec_command.assert_called_once_with('read-only-probe', timeout=10)
        stdin.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
