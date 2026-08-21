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
    def _execute(self, client, code, timeout=10):
        msg_id = client.execute(code)
        output = []
        deadline = monotonic() + timeout

        while True:
            remaining = deadline - monotonic()
            if remaining <= 0:
                self.fail(f"Kernel cell timed out: {code}")
            try:
                message = client.get_iopub_msg(timeout=remaining)
            except Empty:
                self.fail(f"Kernel cell timed out: {code}")

            if message.get("parent_header", {}).get("msg_id") != msg_id:
                continue
            kind = message["msg_type"]
            content = message["content"]
            if kind == "stream":
                output.append(content["text"])
            elif kind == "error":
                traceback = "\n".join(content.get("traceback", []))
                self.fail(f"Kernel error in {code}:\n{traceback}")
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
            # The generic bundled kernelspec says "python". Pin it to the
            # interpreter running this test so CI cannot select another env.
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
                self.assertIn(str(Path(sys.executable).resolve()), imported)
                self.assertIn("imported", imported)

                alive = self._execute(
                    client,
                    "import asyncio; await asyncio.sleep(0); print('alive')",
                )
                self.assertIn("alive", alive)

                future_probe = (
                    "from pyrpl.async_utils import PyrplFuture, MainThreadTimer; "
                    "future=PyrplFuture(); timer=MainThreadTimer(10); "
                    "timer.timeout.connect(lambda: future.set_result(42)); "
                    "timer.start(); "
                    "print('future', future.await_result(timeout=1.0))"
                )
                self.assertIn("future 42", self._execute(client, future_probe))

                await_probe = (
                    "awaited=PyrplFuture(); await_timer=MainThreadTimer(10); "
                    "await_timer.timeout.connect(lambda: awaited.set_result(43)); "
                    "await_timer.start(); print('awaited', await awaited)"
                )
                self.assertIn("awaited 43", self._execute(client, await_probe))
                self.assertIn(
                    "still-alive",
                    self._execute(
                        client,
                        "await asyncio.sleep(0); print('still-alive')",
                    ),
                )
            finally:
                client.stop_channels()
                manager.shutdown_kernel(now=True)


if __name__ == "__main__":
    unittest.main()
