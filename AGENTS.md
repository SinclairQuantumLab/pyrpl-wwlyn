# PyRPL fork agent guidance

## Scope

- Commit `387faf3012c21925c9905d81a95cb681ac7d1b22` is the pristine
  `wwlyn/pyrpl_change` baseline for this Python 3.9 upgrade.
- `.agents/python-3.9-upgrade-changelog.md` is the authoritative record of
  the upgrade's scope, dependency rationale, preservation boundary, and
  completed offline validation.
- Preserve the author's behavior. Limit changes to Python 3.9 dependency,
  packaging, and directly demonstrated Python/Qt compatibility fixes.
- Do not import implementation changes or FPGA assets from current official
  PyRPL merely because they are newer.

## FPGA and device safety

- Do not modify or rebuild `pyrpl/fpga/red_pitaya.bin`. Its expected SHA-256
  is `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
- The author fork contains no DTBO. Do not add one or change FPGA loading,
  server loading, registers, RTL, or hardware behavior without explicit user
  authorization for a separate task.
- Do not contact, restart, or program a physical Red Pitaya unless live-device
  testing is explicitly requested. Running `test.ipynb`, `reloadfpga=True`,
  or `reloadserver=True` mutates the device.

## Validation

- Target CPython `3.9.*`; keep `.python-version`, `setup.py`, and `pyrpl.yml`
  aligned.
- Use `QT_QPA_PLATFORM=offscreen`, a temporary `PYRPL_USER_DIR`, and
  `REDPITAYA_HOSTNAME=_FAKE_` for offline tests.
- Use Nose for the legacy tests. The safe offline subset is
  `pyrpl.test.test_memory`, `pyrpl.test.test_proxyproperty`, and
  `tests/test_python39_compatibility.py`; do not run the full
  hardware-oriented suite by default.
- Before handoff, compile all Python files, install from a fresh Python 3.9
  environment, inspect the wheel, and verify the fork bitstream hash.
