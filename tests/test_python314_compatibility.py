"""Offline regression tests for the CPython 3.14 migration."""

import asyncio
from importlib.metadata import version
import os
import subprocess
import sys
import tempfile
import unittest


os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["REDPITAYA_HOSTNAME"] = "_FAKE_"
_TEST_USER_DIR = tempfile.TemporaryDirectory(prefix="pyrpl-python314-test-")
os.environ["PYRPL_USER_DIR"] = _TEST_USER_DIR.name

import numpy as np

from pyrpl import __version__
from pyrpl.async_utils import LOOP, MainThreadTimer, PyrplFuture, sleep
from pyrpl.curvedb import CurveDB
from pyrpl.software_modules.lockbox.input import InputDirect


class QuadraticInput(InputDirect):
    def expected_signal(self, variable):
        return variable ** 2


class TestPython314Compatibility(unittest.TestCase):
    def test_supported_runtime(self):
        assert sys.version_info[:2] == (3, 14)

    def test_distribution_and_runtime_versions_match(self):
        assert __version__ == version("pyrpl")

    def test_numpy_2_dtype_path(self):
        curve = CurveDB()
        assert all(values.dtype == np.dtype(float) for values in curve.data)

    def test_lockbox_five_point_slope(self):
        input_signal = QuadraticInput.__new__(QuadraticInput)
        assert abs(input_signal.expected_slope(3.0) - 6.0) < 1e-8

    def test_qt_async_future_and_integer_timer(self):
        future = PyrplFuture()
        assert future.get_loop() is LOOP

        timer = MainThreadTimer(1.5)
        assert timer.interval() == 2
        timer.timeout.connect(lambda: future.set_result(42))
        timer.start()

        assert future.await_result(timeout=1.0) == 42

    def test_qasync_drives_native_coroutines(self):
        async def current_loop():
            await asyncio.sleep(0)
            return asyncio.get_running_loop()

        task = asyncio.ensure_future(current_loop())
        sleep(0.02)

        assert task.done()
        assert task.result() is LOOP
        assert not LOOP.is_running()

    def test_blocking_sleep_rejected_inside_owned_task(self):
        async def blocking_sleep():
            sleep(0)

        try:
            LOOP.run_until_complete(blocking_sleep())
        except RuntimeError as error:
            assert "await asyncio.sleep" in str(error)
        else:
            raise AssertionError("blocking sleep unexpectedly re-entered a task")
        assert not LOOP.is_running()

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
        completed = subprocess.run(
            [sys.executable, "-c", code],
            check=False,
            capture_output=True,
            env=env,
            text=True,
            timeout=15,
        )
        assert completed.returncode == 0, completed.stderr
