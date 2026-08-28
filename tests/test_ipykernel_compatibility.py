"""End-to-end regression for PyRPL inside a modern asyncio ipykernel."""

import os
from pathlib import Path
from queue import Empty
import sys
import tempfile
from time import monotonic
import unittest

from jupyter_client import KernelManager


class TestIPythonKernelCompatibility(unittest.TestCase):
    @staticmethod
    def _execute(client, code, timeout=10):
        msg_id = client.execute(code)
        output = []
        deadline = monotonic() + timeout

        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise AssertionError(f"Kernel cell timed out: {code}")
            try:
                message = client.get_iopub_msg(timeout=remaining)
            except Empty as error:
                raise AssertionError(
                    f"Kernel cell timed out: {code}"
                ) from error

            if message.get("parent_header", {}).get("msg_id") != msg_id:
                continue
            kind = message["msg_type"]
            content = message["content"]
            if kind == "stream":
                output.append(content["text"])
            elif kind == "error":
                traceback = "\n".join(content.get("traceback", []))
                raise AssertionError(f"Kernel error in {code}:\n{traceback}")
            elif kind == "status" and content["execution_state"] == "idle":
                return "".join(output)

    def test_import_preserves_kernel_asyncio_and_qt_futures(self):
        with tempfile.TemporaryDirectory(
                prefix="pyrpl-kernel-regression-") as user_dir:
            env = os.environ.copy()
            env.update(
                PYRPL_USER_DIR=user_dir,
                QT_QPA_PLATFORM="offscreen",
                REDPITAYA_HOSTNAME="_FAKE_",
            )
            manager = KernelManager(kernel_name="python3")
            manager.kernel_spec.argv[0] = sys.executable
            manager.start_kernel(env=env)
            client = manager.blocking_client()
            client.start_channels()
            try:
                client.wait_for_ready(timeout=15)
                imported = self._execute(
                    client,
                    "import pathlib, sys, pyrpl; "
                    "print(pathlib.Path(sys.executable).resolve()); "
                    "print('imported')",
                )
                assert str(Path(sys.executable).resolve()) in imported
                assert "imported" in imported

                alive = self._execute(
                    client,
                    "import asyncio; await asyncio.sleep(0); print('alive')",
                )
                assert "alive" in alive

                future_probe = (
                    "from pyrpl.async_utils import PyrplFuture, MainThreadTimer; "
                    "future=PyrplFuture(); timer=MainThreadTimer(10); "
                    "timer.timeout.connect(lambda: future.set_result(42)); "
                    "timer.start(); "
                    "print('future', future.await_result(timeout=1.0))"
                )
                assert "future 42" in self._execute(client, future_probe)

                await_probe = (
                    "awaited=PyrplFuture(); await_timer=MainThreadTimer(10); "
                    "await_timer.timeout.connect(lambda: awaited.set_result(43)); "
                    "await_timer.start(); print('awaited', await awaited)"
                )
                assert "awaited 43" in self._execute(client, await_probe)
                assert "still-alive" in self._execute(
                    client,
                    "await asyncio.sleep(0); print('still-alive')",
                )
            finally:
                client.stop_channels()
                manager.shutdown_kernel(now=True)
