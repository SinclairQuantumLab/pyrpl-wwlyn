"""Offline regression tests for the CPython 3.14 migration."""

import asyncio
from importlib.metadata import version
import logging
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import numpy as np
from qtpy import QtWidgets

from pyrpl import __version__
from pyrpl.async_utils import LOOP, MainThreadTimer, PyrplFuture, sleep
from pyrpl import __main__ as pyrpl_main
from pyrpl.curvedb import CurveDB
from pyrpl.software_modules.lockbox.input import InputDirect
from pyrpl.widgets.pyrpl_widget import EL, LogHandler, PyrplWidget


class QuadraticInput(InputDirect):
    def expected_signal(self, variable):
        return variable ** 2


class TestPython314Compatibility(unittest.TestCase):
    def test_supported_runtime(self):
        self.assertEqual((3, 14), sys.version_info[:2])

    def test_distribution_and_runtime_versions_match(self):
        self.assertEqual(__version__, version("sinclair-pyrpl-wwlyn"))

    def test_numpy_2_dtype_path(self):
        curve = CurveDB()
        self.assertTrue(all(values.dtype == np.dtype(float)
                            for values in curve.data))

    def test_lockbox_finite_difference_slope(self):
        input_signal = QuadraticInput.__new__(QuadraticInput)
        self.assertAlmostEqual(6.0, input_signal.expected_slope(3.0), places=8)

    def test_qt_async_future(self):
        future = PyrplFuture()
        self.assertIs(LOOP, future.get_loop())

        timer = MainThreadTimer(1.5)
        self.assertEqual(2, timer.interval())
        timer.timeout.connect(lambda: future.set_result(42))
        timer.start()

        self.assertEqual(42, future.await_result(timeout=1.0))

    def test_qasync_drives_native_coroutines(self):
        async def current_loop():
            await asyncio.sleep(0)
            return asyncio.get_running_loop()

        task = asyncio.ensure_future(current_loop())
        sleep(0.02)

        self.assertTrue(task.done())
        self.assertIs(LOOP, task.result())
        self.assertFalse(LOOP.is_running())

    def test_blocking_future_drives_native_coroutines(self):
        async def current_loop():
            await asyncio.sleep(0)
            return asyncio.get_running_loop()

        task = asyncio.ensure_future(current_loop())
        future = PyrplFuture()
        timer = MainThreadTimer(2)
        timer.timeout.connect(lambda: future.set_result(42))
        timer.start()

        self.assertEqual(42, future.await_result(timeout=1.0))
        self.assertTrue(task.done())
        self.assertIs(LOOP, task.result())
        self.assertFalse(LOOP.is_running())

    def test_blocking_sleep_rejected_inside_owned_task(self):
        async def blocking_sleep():
            sleep(0)

        with self.assertRaisesRegex(RuntimeError, "await asyncio.sleep"):
            LOOP.run_until_complete(blocking_sleep())
        self.assertFalse(LOOP.is_running())

    def test_import_reuses_running_host_loop(self):
        code = """
import asyncio

async def main():
    import pyrpl.async_utils as async_utils
    assert async_utils.LOOP is asyncio.get_running_loop()
    await asyncio.sleep(0)

asyncio.run(main())
"""
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"
        completed = subprocess.run(
            [sys.executable, "-c", code],
            check=False,
            capture_output=True,
            env=env,
            text=True,
            timeout=15,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_cli_drives_qasync_loop(self):
        tasks = []

        async def current_loop():
            await asyncio.sleep(0)
            return asyncio.get_running_loop()

        def create_pyrpl(**kwargs):
            task = asyncio.ensure_future(current_loop())
            task.add_done_callback(lambda _task: LOOP.stop())
            tasks.append(task)
            return object()

        with patch.object(sys, "argv", ["pyrpl", "test-config"]), \
                patch.object(pyrpl_main, "Pyrpl", side_effect=create_pyrpl), \
                patch("builtins.print"):
            pyrpl_main.main()

        self.assertEqual(1, len(tasks))
        self.assertIs(LOOP, tasks[0].result())
        self.assertFalse(LOOP.is_running())

    def test_qt_log_handler_cleanup(self):
        widget = PyrplWidget.__new__(PyrplWidget)
        QtWidgets.QMainWindow.__init__(widget)
        widget.timers = []
        widget.logger = logging.getLogger(__name__ + '.widget')
        widget.handler = LogHandler()
        widget.logger.addHandler(widget.handler)
        EL.show_exception.connect(widget.show_exception)
        widget.handler.show_log.connect(widget.show_log)

        widget._clear()

        self.assertIsNone(widget.handler)
        self.assertEqual([], widget.logger.handlers)


if __name__ == '__main__':
    unittest.main()
