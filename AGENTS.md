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
- The user separately authorized common PID RTL repairs: integrator-readback
  declaration visibility and the default DERIVATIVE=0 shadowed D-input fix.
  Record their evidence in `.agents/common-pid-rtl-fix-changelog.md`.
  This is not authorization for PID/filter redesign or a replacement BIN.
- Common implementation review continues on `fix/pid-rtl-shadowing` using
  the original Z7010 RTL lineage. Characterize enabled filters and repair
  demonstrated implementation issues without changing arithmetic or latency.
  OS loader differences are not part of this work; timing evidence must name
  its FPGA target and must not be generalized from Z7020 to Z7010.

## Branching

- `develop` is the integration branch for changes that apply across device/OS
  combinations. Common work uses standard topic namespaces such as
  `feature/*`, `fix/*`, and `refactor/*` and is merged into `develop`.
- Device- or OS-specific work belongs under its target compatibility root,
  for example `gen1-os2/feature/os-upgrade` or
  `gen2-os2/fix/device-profile`.
- A compatibility root's `main` branch means that combination is considered
  commissionable. Do not create or advance it based only on offline evidence
  when its field gate is still open.
- Propagate common changes from `develop` into compatibility branches with
  merge commits. Use `git cherry-pick -x` only for an intentionally selective
  backport that must not import the source branch's other changes.
- Do not rebase published compatibility `main` branches or rewrite validation
  history.
- Classify changes by cause, not where they were discovered. Pre-existing
  shared RTL defects belong on `fix/*` based on `develop`; board/OS/interface
  port changes belong under the target compatibility root. Common toolchain
  prerequisites may be separate commits on the shared topic.
- A timing failure found during a port is a validation finding, not permission
  to redesign PID/filter logic, add latency or lower clocks. Establish its
  cause and scope first. Common source fixes do not authorize rebuilding or
  replacing the original BIN or advancing commissioned compatibility mains.
- Keep subsequent work isolated on the common fix topic. Do not merge it
  into `develop` or any device/OS root until the user explicitly requests it.
  The earlier merges through `2703645`/`ef7f1c1` remain historical checkpoints.

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

- Target CPython `3.14.*`; keep `.python-version`, `pyproject.toml`,
  `uv.lock`, and `pyrpl.yml` aligned.
- `pyproject.toml` is the dependency and package-metadata source of truth and
  uses the uv build backend. Keep the generated universal `uv.lock` tracked;
  update it with uv rather than editing it manually.
- Preserve the tested major-version bounds in `pyproject.toml`: NumPy
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
- Create or update the local environment with `uv sync --extra test`. Use
  `uv run --extra test ...` for the validated commands; normal project
  operation must not depend on `--locked`, `--frozen`, or similar flags.
- Before handoff, compile all Python files, install from a fresh Python 3.14
  environment, inspect the wheel, and verify the fork bitstream hash.
- Shared PID RTL fixes must run `pyrpl/fpga/sim/run_pid_contract.py` against
  the real sources with XSim; see its README. The source archive includes the
  simulation harness, but the runtime wheel must exclude it. Behavioral
  simulation does not establish timing closure or historical BIN equivalence.

## Configuration and notebooks

- The common branch still tracks its historical `test.ipynb`, unlike the
  newer compatibility candidates. The user's local notebook was preserved
  byte-for-byte during the branch switch and therefore appears modified.
  Never stage, restore, execute or overwrite that local file as part of this
  RTL task. Notebook tracking/template migration is a separate change.
- `test.ipynb` is the user-facing manual/live-device acceptance workflow and
  the tracked record of live-device experiments. Put steps that a user is
  expected to run there, make every mutating step explicit, and never store a
  password. It contains machine- and device-specific state and
  hardware-mutating cells. Do not run it or rewrite saved outputs unless the
  user explicitly requests notebook/device work.
- Keep agent-only investigation scripts and notes under `.agents/`, outside
  the package and user-facing test areas. Automated product regressions still
  belong in `pyrpl/test` or `tests`; do not confuse them with disposable agent
  diagnostics. Do not add standalone live-device scripts under `tests/`.
