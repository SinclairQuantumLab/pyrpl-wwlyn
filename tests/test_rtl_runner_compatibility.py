"""Offline checks of the RTL runner's evidence and failure handling."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class TestRtlRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fpga = Path(__file__).resolve().parents[1] / 'pyrpl' / 'fpga'
        spec = importlib.util.spec_from_file_location(
            'pid_contract_runner', cls.fpga / 'sim' / 'run_pid_contract.py')
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def run_mock_toolchain(self, transcript, returncode=0):
        # This intentionally never starts Vivado. The real RTL contract is a
        # separate required command; these tests exercise its Python runner.
        with tempfile.TemporaryDirectory(prefix='pyrpl-rtl-runner-test-') as temp:
            root = Path(temp)
            for name in ('xvlog', 'xelab', 'xsim'):
                (root / (name + ('.bat' if os.name == 'nt' else ''))).touch()

            def completed(command, **kwargs):
                is_sim = Path(command[0]).stem == 'xsim'
                return subprocess.CompletedProcess(
                    command, returncode if is_sim else 0,
                    transcript if is_sim else 'compile/elaborate complete', '')

            error = None
            with patch.object(self.runner.subprocess, 'run', side_effect=completed), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    self.runner.run(root, root)
                except RuntimeError as exc:
                    error = exc
            outputs = list(root.glob('pyrpl-pid-rtl-*'))
            self.assertEqual(len(outputs), 1)
            return json.loads((outputs[0] / 'result.json').read_text()), error

    def test_pass_records_both_benches_and_real_sources(self):
        report, error = self.run_mock_toolchain('PID_CONTRACT_PASS 342 checks')
        self.assertIsNone(error)
        self.assertTrue(report['passed'])
        self.assertEqual({Path(p).as_posix() for p in report['source_sha256']}, {
            'rtl/red_pitaya_lpf_block.v', 'rtl/red_pitaya_filter_block.v',
            'rtl/red_pitaya_pid_block.v', 'sim/tb_pid_contract.sv',
            'sim/tb_filter_contract.sv',
        })
        sv_command = report['commands'][1]['argv']
        self.assertIn('--sv', sv_command)
        self.assertEqual({Path(p).name for p in sv_command[2:]}, {
            'tb_pid_contract.sv', 'tb_filter_contract.sv'})

    def test_zero_exit_without_pass_is_not_success(self):
        report, error = self.run_mock_toolchain('simulation ended')
        self.assertIsNotNone(error)
        self.assertFalse(report['passed'])

    def test_fatal_with_zero_exit_is_not_success(self):
        report, error = self.run_mock_toolchain(
            'PID_CONTRACT_FAIL filter mismatch\nPID_CONTRACT_PASS 342 checks')
        self.assertIsNotNone(error)
        self.assertFalse(report['passed'])

    def test_nonzero_exit_keeps_failed_report(self):
        report, error = self.run_mock_toolchain('tool failed', 2)
        self.assertIsNotNone(error)
        self.assertFalse(report['passed'])
        self.assertEqual(report['commands'][-1]['returncode'], 2)


if __name__ == '__main__':
    unittest.main()
