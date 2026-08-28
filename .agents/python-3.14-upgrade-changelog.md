# CPython 3.14 upgrade

## Baseline and scope

This upgrade starts from commit `407a9d1`, the CPython 3.9 checkpoint that the
user reported successfully field-testing on the author's original-generation
STEMlab 125-14 and Red Pitaya OS `1.04-18` environment. The 3.14 work is a new,
non-rewriting change on `develop/python-upgrade`.

The upgrade preserves the fork's hardware identity. It does not modify the Red
Pitaya loader, server, register map, RTL, or either existing FPGA binary. It
does not add a device-tree artifact. The canonical `red_pitaya.bin` remains
2,083,740 bytes with SHA-256
`dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.

## Environment and packaging

- The exclusive runtime target is CPython `3.14.*`, declared consistently in
  `.python-version`, `setup.py`, and `pyrpl.yml`.
- `setup.py` remains the dependency and package-metadata source of truth;
  `pyproject.toml` selects a current setuptools build backend. No `uv.lock` is
  introduced.
- The tested environment resolves NumPy 2.5.2, SciPy 1.18.1, pandas 3.0.5,
  Matplotlib 3.11.1, pyqtgraph 0.14.0, QtPy 2.4.3, PyQt5 5.15.11, Paramiko
  5.0.0, lmfit 1.3.4, netifaces2 0.0.22, qasync 0.28.0, ipykernel 7.3.0,
  and nose-ng 1.4.3.
- Quamash is replaced by qasync. The unmaintained original Nose runner is
  replaced by Nose NG for the selected legacy suite.
- The repository `.venv` was recreated with CPython 3.14.4 and the editable
  `.[test]` installation. `uv pip check` reports all 82 installed packages as
  compatible.
- The notebook kernel metadata now identifies the 3.14.4 environment. Its
  hardware-mutating cells and saved outputs were not executed or rewritten.

## Compatibility changes

- Removed runtime uses of NumPy's deleted `np.float`, `np.int`, and
  `np.complex` aliases and imported warning classes from `numpy.exceptions`.
- Replaced the removed `scipy.misc.derivative` call with the equivalent
  five-point central first derivative used by lockbox inputs.
- Converted float geometry and timer values at strict Qt integer API
  boundaries, and used floating-point Qt polygon points where appropriate.
- Updated the PyRPL future/event-loop integration for Python 3.14 asyncio.
  Plain scripts use a qasync Qt loop, while a running ipykernel loop is reused
  and its Qt events are pumped without replacing or re-entering that loop.
- Made `python -m pyrpl` run through the shared Qt/asyncio loop and retain its
  module-level `PYRPL` instance.
- Removed Python 3.14 syntax warnings caused by invalid escape sequences and a
  `return` statement in `finally`.

## Offline validation completed

All validation used `QT_QPA_PLATFORM=offscreen`, an isolated temporary
`PYRPL_USER_DIR`, and `REDPITAYA_HOSTNAME=_FAKE_` where PyRPL was imported.
No physical Red Pitaya was contacted.

- CPython 3.14.4 compiled `pyrpl/` and `tests/` with every `SyntaxWarning`
  promoted to an error.
- All 71 discovered non-test PyRPL modules imported successfully.
- Nine `unittest` regressions passed, including NumPy 2 behavior, the lockbox
  derivative, Qt timers, synchronous and native-asyncio futures, host-loop
  reuse, and an end-to-end subprocess running a real ipykernel.
- Nose NG passed 17 selected offline tests: the legacy `MemoryTree` and proxy
  property cases, all four retained Python 3.9 regressions, and all eight
  Python 3.14 script regressions.
- The Conda YAML parsed with the expected Python 3.14 and editable test-extra
  installation declarations.
- The wheel built successfully with 129 entries. Inspection verified package
  name `pyrpl`, version 0.9.5.0, `Requires-Python: >=3.14,<3.15`, the exact
  fork bitstream, the qasync requirement, and the absence of `.dtb`, `.dtbo`,
  `.dts`, and `.dtsi` files.
- Installing the wheel into a separate fresh CPython 3.14.4 environment
  succeeded. `uv pip check` found no broken requirements, and PyRPL imported
  from that environment's `site-packages` rather than the checkout.

## Remaining validation boundary

The CPython 3.14 change has not been run against the physical Red Pitaya. The
successful live test belongs to the preceding CPython 3.9 checkpoint. A 3.14
live load remains a separate, explicitly authorized step and must use the same
confirmed STEMlab 125-14 / OS 1.04-18 / fork-bitstream combination.

qasync 0.28.0 does not advertise Python 3.14 support and emits a deprecation
warning for an asyncio helper scheduled for removal in Python 3.16. The new
script and real-ipykernel regressions demonstrate the required behavior on
3.14.4, but those tests must remain mandatory until qasync publishes a release
with explicit support for this runtime line.
