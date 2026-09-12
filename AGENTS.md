# PyRPL fork agent guidance

## Scope

- Commit `407a9d1b8c70f74e6d59a67365d1eaa1d34a0553` is the field-tested
  CPython 3.9 checkpoint from which the CPython 3.14 upgrade proceeds.
- `.agents/python-3.9-upgrade-changelog.md` is the historical record of the
  validated 3.9 baseline. Keep the 3.14 implementation and its validation
  evidence in a separate, non-rewriting commit and in
  `.agents/python-3.14-upgrade-changelog.md`.
- Preserve the author's behavior. The Python 3.14 upgrade is complete;
  `gen1-os2/feature/os-upgrade` adds Red Pitaya OS 2.07+ loader/device-tree
  integration for the author's original Z7010 board. The
  `gen2-os2/feature/device-upgrade` and
  `gen2-pro-os2/feature/device-upgrade` candidates add repo-side support for
  the exact Z7010 Gen 2 profile families.
- Do not import implementation changes or FPGA assets from current official
  PyRPL merely because they are newer.
- Standard Z7010 Gen 2 offline readiness is committed at `3fc4307`; the user
  deferred its physical tests. Active development now targets Z7020 Gen 2 Pro
  on OS 2 under `gen2-pro-os2/feature/device-upgrade`.
- The user authorized proceeding beyond the Z7020 feasibility assessment.
  Keep its port/build/simulation evidence in a separate implementation log.
  Preserve the original BIN and approved Z7010 DTBOs; any new Z7020 image must
  have a separate target, filename and provenance. Do not enable its loader
  profile merely because RTL simulation or synthesis succeeds.

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

## FPGA and device safety

- The fork author's known hardware environment was Red Pitaya OS `1.04-18`
  on an original-generation STEMlab 125-14 with a Zynq-7010. Treat that as
  provenance for the legacy `/dev/xdevcfg` loader, not as permission to
  downgrade or program a board. The legacy loader remains original-board only;
  before any legacy live load, positively exclude Gen 2, Z7020, 4-input, and
  slave variants and require `/dev/xdevcfg` to be a character device.
- On the confirmed `1.04-18` image, `/root/.version` reports the underlying
  Linux image as `1.07`. Validate the ecosystem release with
  `/opt/redpitaya/version.txt`, which reports version `1.04`, build `18`.
- Do not modify or rebuild `pyrpl/fpga/red_pitaya.bin`. Its expected SHA-256
  is `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
- The author fork originally contained no DTBO. The user has authorized two
  source-derived variants for the separate OS 2.07+ upgrade. They differ only
  in the firmware basename required by the installed `overlay.sh`:
  - `red_pitaya_os2_z10.dtbo` (`fpga.bit.bin`), SHA-256
    `41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9`;
  - `red_pitaya_os2_z10_fpga_bin.dtbo` (`fpga.bin`), SHA-256
    `99f0fd0c3ce394fb0c86e4dec95895b8a5855cc80ebbfd5fedc961fb9ed4a35c`.
  Neither is the maintained/upstream PyRPL overlay, and neither may acquire an
  AXI XADC node. Do not alter FPGA RTL or rebuild the bitstream as part of this
  Z7010 loader work. The separately authorized Z7020 port may adapt RTL and
  platform sources with explicit simulation evidence; it must not overwrite
  or regenerate the preserved Z7010 artifact.
- Do not contact, restart, or program a physical Red Pitaya unless live-device
  testing is explicitly requested. Running `test.ipynb`, `reloadfpga=True`,
  or `reloadserver=True` mutates the device.
- `python -m pyrpl.redpitaya_preflight HOSTNAME` is the packaged read-only
  field-preflight command. It still contacts the named board and therefore
  requires explicit live-device authorization, but it must never upload,
  remount, stop services, start a server, or program the FPGA.

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
- OS-loader changes must also pass
  `python -m unittest pyrpl.test.test_redpitaya_fpga_loader`. The wheel must
  contain the exact fork BIN plus both source-identical firmware-name DTS/DTBO
  variants, `pyrpl/redpitaya_preflight.py`, and no other DTBO.
- Standard Gen 2 readiness also runs `tests/test_fork_pid_compatibility.py`
  and `tests/test_gen2_manual_workflow.py` with unittest. These characterize
  Python register writes and validate the clean template without executing
  its device cells. They do not prove FPGA or analog behavior.
- Pro RTL changes must run the real XSim contract in
  `pyrpl/fpga/sim/run_pid_contract.py`; see its README. Keep simulation and
  synthesis outputs in new, separate directories, never in the preserved
  legacy output tree. Z7020 implementation evidence is recorded in
  `.agents/red-pitaya-z7020-upgrade-changelog.md`.

## Configuration and notebooks

- `test.ipynb.template` is the tracked user-facing manual/live-device starter.
  Put user-run steps there with brief Markdown explanations. Keep it free of
  saved outputs, device-specific addresses, and passwords.
- `test.ipynb` is the ignored local working copy, created from the template.
  Preserve its settings and saved outputs. Never stage it or overwrite it
  during template updates. Do not run it or change its contents unless the
  user explicitly requests notebook/device work.
- Keep agent-only investigation scripts and notes under `.agents/`, outside
  the package and user-facing test areas. Automated product regressions still
  belong in `pyrpl/test` or `tests`; do not confuse them with disposable agent
  diagnostics. Do not add standalone live-device scripts under `tests/`.

## Red Pitaya OS 2 and Gen 2 investigation

- The assessment and implementation state are recorded in
  `.agents/red-pitaya-os2-gen2-upgrade-assessment.md` and
  `.agents/red-pitaya-os2-upgrade-changelog.md`; the Z7010 Gen 2 implementation
  and remaining bench gate are in
  `.agents/red-pitaya-gen2-upgrade-changelog.md`. The ordered device matrix,
  candidate commits, stop conditions, and evidence-commit policy are in
  `.agents/red-pitaya-live-test-plan.md`. Keep OS compatibility and board
  compatibility as separate concerns: an original STEMlab 125-14 can run OS
  2, while "Gen 2" includes materially different Z7010, Z7020, and TI-based
  profiles.
- The OS 2.07+ loader accepts only exact STEMlab 125-14 Z7010 profile/path
  pairs: original profiles 1 and 2 with `z10_125`, standard Gen 2 profiles 20
  and 31 with `z10_125_v2`, and Pro Gen 2 profiles 21 and 32 with
  `z10_125_pro_v2`. Preserve the exact fork bitstream. Refuse mismatched
  profile/path pairs, early OS 2, OS 3, Z7020, and other converter families
  before uploading or changing device state.
- OS 2.07+ loading must inspect the installed `overlay.sh` and recognize only
  its known fixed custom basenames, `/opt/pyrpl/fpga.bit.bin` or
  `/opt/pyrpl/fpga.bin`. It must select the hash-pinned DTBO whose
  `firmware-name` matches that basename, stage `/opt/pyrpl/fpga.dtbo`, invoke
  `/opt/redpitaya/sbin/overlay.sh`, and require both approved local hashes
  before upload, a successful overlay result, FPGA Manager state `operating`,
  expected `/tmp/loaded_fpga.inf` identity, monitor-client connection, and
  positive fork register metadata. Preserve diagnostics and staged files after
  failure.
- Do not copy the maintained/upstream PyRPL DTBO into this fork. It describes
  an AXI XADC at `0x83c00000`, whereas this fork instantiates and controls XADC
  in `pyrpl/fpga/rtl/red_pitaya_ams.v`. A fork DTBO must be derived from the
  actual implemented design and validated as a pair with the fork bitstream.
- `main` contains earlier modern-loader work and regression tests. Treat it as
  a reference for selective review, not as authority to merge unrelated code
  or FPGA artifacts into this branch.
- Offline tests do not establish hardware compatibility. No OS 2 or Gen 2
  live-device claim may be made until a controlled test is explicitly
  authorized and the implementation log's field gates pass.
- Static Z7010 Gen 2 support is based on Red Pitaya's official build matrix,
  which uses the same `MODEL=Z10` platform for original, standard Gen 2, and
  Pro Gen 2 paths, plus the published package-pin evidence. The FPGA image and
  DTBO remain unchanged. Gen 2 DAC full scale is +/-2 V into high impedance
  and +/-1 V into 50 ohms; do not silently alter PyRPL's register normalization
  because software cannot infer the load. The authorized Z7020 Gen 2 port is
  under development, not load-ready. TI-based Gen 2 boards require a
  different converter/platform design and remain outside the preservation-
  first path.
