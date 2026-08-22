"""Offline regression tests for the Python 3.9 compatibility work."""

import hashlib
import os
from pathlib import Path
import tempfile


os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["REDPITAYA_HOSTNAME"] = "_FAKE_"
_TEST_USER_DIR = tempfile.TemporaryDirectory(prefix="pyrpl-python39-test-")
os.environ["PYRPL_USER_DIR"] = _TEST_USER_DIR.name

from qtpy import QtWidgets

from pyrpl.acquisition_module import AcquisitionModule
from pyrpl.modules import SignalLauncher
from pyrpl.widgets.module_widgets.iir_widget import (
    MyGraphicsWindow as IirGraphicsWindow,
)
from pyrpl.widgets.module_widgets.na_widget import (
    MyGraphicsWindow as NetworkAnalyzerGraphicsWindow,
)


class TestPython39Compatibility(object):
    def test_preserves_author_fpga_asset(self):
        fpga_directory = Path(__file__).resolve().parents[1] / "pyrpl" / "fpga"
        bitstream = fpga_directory / "red_pitaya.bin"

        digest = hashlib.sha256(bitstream.read_bytes()).hexdigest()
        assert digest == (
            "dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed"
        )
        assert not list(fpga_directory.rglob("*.dtbo"))

    def test_curve_async_compares_running_state_by_value(self):
        class RunningState(str):
            pass

        class DummyAcquisition(object):
            running_state = RunningState("stopped")
            stop_called = False

            def stop(self):
                self.stop_called = True

            def _curve_async(self, delay):
                return delay

        acquisition = DummyAcquisition()
        stopped_literal = "stopped"
        assert acquisition.running_state == stopped_literal
        assert acquisition.running_state is not stopped_literal
        assert AcquisitionModule.curve_async(acquisition) == 0
        assert not acquisition.stop_called

    def test_graphics_windows_accept_parent_and_title(self):
        parent = QtWidgets.QWidget()
        windows = (
            IirGraphicsWindow("IIR title", parent),
            NetworkAnalyzerGraphicsWindow("Network analyzer title", parent),
        )

        assert windows[0].windowTitle() == "IIR title"
        assert windows[0].parent is parent
        assert windows[1].windowTitle() == "Network analyzer title"
        assert windows[1].parent_widget is parent
        for window in windows:
            window.close()

    def test_signal_launcher_uses_qtpy_signal_type(self):
        class Receiver(object):
            def update_attribute_by_name(self, name, value):
                self.received = (name, value)

        receiver = Receiver()
        launcher = SignalLauncher(module=None)
        launcher.connect_widget(receiver)
        launcher.update_attribute_by_name.emit("gain", [1.0])

        assert receiver.received == ("gain", [1.0])
        launcher._clear()
