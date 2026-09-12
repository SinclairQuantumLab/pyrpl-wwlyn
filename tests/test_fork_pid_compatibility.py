"""Characterize the author's Python/FPGA PID contract without a board.

These tests record bus writes; they do not simulate analog behavior or prove
that a physical FPGA implements the RTL. No PID implementation is replaced.
"""

import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['REDPITAYA_HOSTNAME'] = '_FAKE_'
_TEST_USER_DIR = tempfile.TemporaryDirectory(prefix='pyrpl-pid-contract-')
os.environ['PYRPL_USER_DIR'] = _TEST_USER_DIR.name

from pyrpl.hardware_modules.pid import Pid


class RecordingPid:
    def __init__(self, number=0):
        self._number = number
        self.writes = []

    def _write(self, address, value):
        self.writes.append((address, value))


class TestForkPidCompatibility(unittest.TestCase):
    def write_sequence(self, values):
        recorder = RecordingPid()
        with patch('time.sleep'), contextlib.redirect_stdout(io.StringIO()):
            Pid.set_setpoint_array(recorder, values)
        return recorder.writes

    def test_signed_sequence_packing_and_saturation(self):
        # Index in bits 17:14, signed 14-bit two's-complement value in 13:0.
        values = [-2, -1, -0.5, 0, 0.5, 1, 2]
        words = [0x2000, 0x2000, 0x3000, 0, 0x1000, 0x1fff, 0x1fff]
        self.assertEqual(
            [(0x134, (index << 14) | word)
             for index, word in enumerate(words)],
            self.write_sequence(values))

    def test_sequence_has_sixteen_slots_and_does_not_wrap_writes(self):
        writes = self.write_sequence([0.25] * 19)
        self.assertEqual(16, len(writes))
        self.assertEqual((0x134, (15 << 14) | 0x800), writes[-1])
        self.assertEqual(list(range(16)), [value >> 14 for _, value in writes])

    def test_empty_sequence_does_not_write(self):
        self.assertEqual([], self.write_sequence([]))

    def test_sequence_preserves_authors_zero_rounding(self):
        # The sequence writer rounds tiny values to zero, unlike the scalar
        # FloatRegister's minimum-nonzero behavior. Do not normalize them alike.
        self.assertEqual([(0x134, 0), (0x134, 1 << 14)],
                         self.write_sequence([1e-9, -1e-9]))

    def test_manual_step_and_reset_use_fork_addresses(self):
        for number in range(3):
            recorder = RecordingPid(number)
            Pid.reset_sequence_index(recorder)
            Pid.manually_change_setpoint(recorder)
            self.assertEqual([(0x140, 1), (0x160 + 4 * number, 1)],
                             recorder.writes)

    def test_sequence_readback_is_signed_and_uses_fork_scale(self):
        register = Pid.setpoint_in_sequence
        self.assertEqual(0x24c, register.address)
        for raw, expected in ((0x2000, -1.0), (0x3000, -0.5),
                              (0, 0.0), (0x1000, 0.5),
                              (0x1fff, 8191 / 8192)):
            with self.subTest(raw=raw):
                self.assertEqual(expected, register.to_python(None, raw))

    def test_gain_and_integrator_contract_is_unchanged(self):
        self.assertEqual((12, 32, 30), (Pid._PSR, Pid._ISR, Pid._GAINBITS))
        self.assertEqual(30, Pid.p.bits)
        self.assertEqual(30, Pid.i.bits)
        self.assertEqual((-1, 1), (Pid.ival.min, Pid.ival.max))
        self.assertEqual(0x130, Pid.use_setpoint_sequence.address)
        self.assertEqual(0x240, Pid.setpoint_index.address)
        self.assertEqual(0x244, Pid.sequence_wrap_flag.address)


if __name__ == '__main__':
    unittest.main()
