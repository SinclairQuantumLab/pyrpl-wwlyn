# PyRPL fork agent guidance

## Scope

- Commit `407a9d1b8c70f74e6d59a67365d1eaa1d34a0553` is the field-tested
  CPython 3.9 checkpoint from which the CPython 3.14 upgrade proceeds.
- `.agents/python-3.9-upgrade-changelog.md` is the historical record of the
  validated 3.9 baseline. Keep the 3.14 implementation and its validation
  evidence in a separate, non-rewriting commit and in
  `.agents/python-3.14-upgrade-changelog.md`.
- Preserve the author's behavior. Limit changes to Python 3.14 dependency,
  packaging, and directly demonstrated Python/NumPy/Qt/async compatibility
  fixes.
- Do not import implementation changes or FPGA assets from current official
  PyRPL merely because they are newer.

## FPGA and device safety

- The fork author's known hardware environment was Red Pitaya OS `1.04-18`
  on an original-generation STEMlab 125-14 with a Zynq-7010. Treat that as
  provenance for the legacy `/dev/xdevcfg` loader, not as permission to
  downgrade or program a board. Before any live load, positively exclude
  Gen 2, Z7020, 4-input, and slave variants and require `/dev/xdevcfg` to be
  a character device.
- On the confirmed `1.04-18` image, `/root/.version` reports the underlying
  Linux image as `1.07`. Validate the ecosystem release with
  `/opt/redpitaya/version.txt`, which reports version `1.04`, build `18`.
- Do not modify or rebuild `pyrpl/fpga/red_pitaya.bin`. Its expected SHA-256
  is `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
- The author fork contains no DTBO. Do not add one or change FPGA loading,
  server loading, registers, RTL, or hardware behavior without explicit user
  authorization for a separate task.
- Do not contact, restart, or program a physical Red Pitaya unless live-device
  testing is explicitly requested. Running `test.ipynb`, `reloadfpga=True`,
  or `reloadserver=True` mutates the device.

## Validation

- Target CPython `3.14.*`; keep `.python-version`, `setup.py`, and `pyrpl.yml`
  aligned.
- `setup.py` remains the dependency and package-metadata source of truth;
  `pyproject.toml` selects the setuptools build backend. This branch does not
  use a generated dependency lockfile.
- Preserve the tested major-version bounds in `setup.py`: NumPy
  `>=2.3.2,<3`, SciPy `>=1.16.1,<2`, lmfit `>=1.3.4,<2`, Paramiko `>=4,<6`,
  PyQt5 `>=5.15.11,<6`, and pyqtgraph `>=0.14,<1`.
- Quamash is replaced by `qasync>=0.28,<0.29`. qasync 0.28 does not claim
  upstream Python 3.14 support, so the script and real-ipykernel event-loop
  regressions are mandatory before handoff.
- Use the `nosetests` command supplied by `nose-ng>=1.4.3,<2`; the original
  Nose package uses standard-library APIs removed by modern Python.
- Use `QT_QPA_PLATFORM=offscreen`, a temporary `PYRPL_USER_DIR`, and
  `REDPITAYA_HOSTNAME=_FAKE_` for offline tests.
- Use Nose NG for the legacy tests. The safe offline subset is
  `pyrpl.test.test_memory`, `pyrpl.test.test_proxyproperty`, and
  the root `tests/test_*compatibility.py` regressions; do not run the full
  hardware-oriented suite by default.
- Create or replace the local environment with
  `uv venv --clear --python 3.14 --seed .venv` and
  install with `uv pip install --python .venv/Scripts/python.exe -e ".[test]"`.
- Before handoff, compile all Python files, install from a fresh Python 3.14
  environment, inspect the wheel, and verify the fork bitstream hash.

## Configuration and notebooks

- `test.ipynb` is a tracked record of live-device experiments. It contains
  machine- and device-specific state and hardware-mutating cells. Do not run
  it, sanitize it, or rewrite its saved outputs unless the user explicitly
  requests notebook/device work.
- `tests/simple_connection_test.py` is local and ignored. Never commit its
  device-specific configuration; keep the tracked template sanitized.

## Red Pitaya OS 2 and Gen 2 investigation

- The evidence and proposed validation gates are recorded in
  `.agents/red-pitaya-os2-gen2-upgrade-assessment.md`. Keep OS compatibility
  and board compatibility as separate concerns: an original STEMlab 125-14
  can run OS 2, while "Gen 2" includes materially different Z7010, Z7020, and
  TI-based profiles.
- The first implementation target, if authorized, is the original Z7010
  STEMlab 125-14 on a pinned OS 2.07 image while preserving the exact fork
  bitstream. This is primarily a loader/device-tree integration task, not a
  reason to alter the fork's DSP RTL.
- Do not copy the maintained/upstream PyRPL DTBO into this fork. It describes
  an AXI XADC at `0x83c00000`, whereas this fork instantiates and controls XADC
  in `pyrpl/fpga/rtl/red_pitaya_ams.v`. A fork DTBO must be derived from the
  actual implemented design and validated as a pair with the fork bitstream.
- `main` contains earlier modern-loader work and regression tests. Treat it as
  a reference for selective review, not as authority to merge unrelated code
  or FPGA artifacts into this branch.
- A Z7010 Gen 2 board may be compatible with the existing bitstream after
  exact model, pin, clock, and analog validation. A Z7020 Gen 2 target requires
  a separately authorized FPGA rebuild/port. TI-based Gen 2 boards require a
  different converter/platform design and are outside the preservation-first
  path.
