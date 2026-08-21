# PyRPL fork agent handoff

Read this file before changing the repository. Update it when the user makes a
new dependency, packaging, hardware, testing, or documentation decision and
before a commit or handoff. Keep durable decisions here, not a chronological
work log.

## Working rules

- Preserve unrelated and uncommitted work. Inspect `git status` before editing
  and never discard user changes to notebooks, configuration, RTL, or binary
  assets.
- Do not contact, restart, or program a physical Red Pitaya unless live-device
  work is explicitly in scope. `reloadfpga=True`, `reloadserver=True`, and
  executing `test.ipynb` all mutate the target device.
- Never log, document, or commit device passwords, private configuration, or
  tokens.
- Keep the README files task-oriented. Put enduring contributor constraints
  here and FPGA build/asset provenance in `pyrpl/fpga/README.md`.
- Detailed, historical upgrade and reproduction records live under
  [`.agents/`](.agents/README.md). Keep this file as the concise statement of
  current constraints; keep one-time chronology, per-file inventories, and
  historical validation evidence in the applicable upgrade changelog.

## Supported environment and dependencies

- This checkout targets CPython `3.14.*` on x86_64 Windows.
  `.python-version`, `pyproject.toml`, `uv.lock`, and `pyrpl.yml` must remain
  aligned.
- Use `uv sync --locked` to create/synchronize the environment and `uv run`
  for repository commands. `pyproject.toml` and `uv.lock` are the dependency
  sources of truth; `pyrpl.yml` is only a Conda bootstrap around this checkout.
- Preserve the tested major-version bounds in `pyproject.toml`. In particular,
  NumPy `>=2.3.2,<3` and SciPy `>=1.16.1,<2` are the first supported lines
  with Windows CPython 3.14 wheels; lmfit is `>=1.3.4,<2`.
- Keep `netifaces2`, which supplies the `netifaces` import through a Windows
  stable-ABI wheel validated on CPython 3.14. The original `netifaces` package
  is a Windows build blocker here.
- Keep PyQt5 `>=5.15.11,<6`. Its stable-ABI bindings and the resolved native
  PyQt5-sip wheel are validated on CPython 3.14; a PyQt6 migration is not part
  of this upgrade.
- Keep `qasync>=0.28,<0.29`, which replaces abandoned Quamash. Exercise the
  Qt event-loop/Future regression test when changing it. Plain scripts and the
  CLI use the PyRPL-owned qasync loop; modern kernels reuse their running host
  loop and a process-lifetime Qt pump task; terminal IPython keeps its
  externally driven Qt loop. Never replace an active ipykernel loop during
  `import pyrpl`.
- Keep Paramiko at `>=4,<6`; older releases contain syntax that is invalid on
  Python 3.14. Direct runtime imports must not rely on transitive dependencies.
- The legacy suite uses the `nosetests` executable from
  `nose-ng>=1.4.3,<2`; the original Nose imports removed stdlib APIs on modern
  Python. Keep the test dependency out of runtime requirements.
- After dependency changes, regenerate `uv.lock`, then run `uv lock --check`,
  `uv sync --locked --dry-run`, and `uv pip check`.

## Code and packaging layout

- The real application is the root `pyrpl/` package. `src/pyrpl_change/` is a
  leftover scaffold and is not the runtime package or console entry point.
- The console entry point must remain `pyrpl.__main__:main`, and uv's build
  backend must package `pyrpl/` from the repository root.
- Built wheels must contain both `pyrpl/fpga/red_pitaya.bin` and
  `pyrpl/fpga/red_pitaya.dtbo`.
- `pyrpl/fpga/red_pitaya.dtbo` and
  `pyrpl/test/test_redpitaya_fpga_loader.py` are required parts of modern-OS
  support; do not mistake them for disposable local files when preparing a
  change.
- `README.md` is the current installation and quick-start guide.
  `pyrpl/fpga/README.md` owns FPGA provenance and build details.
  `Documentation.md` and inherited Sphinx pages contain historical
  instructions; their old dependency, `setup.py`, and release advice is not
  authoritative. Keep the archive warning in `docs/source/index.rst`.

## Safe offline validation

Set Qt to offscreen for tests that import the GUI stack:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:NOSE_IGNORE_CONFIG_FILES = "1"
$env:REDPITAYA_HOSTNAME = "_FAKE_"
$pyrplTestDir = Join-Path ([IO.Path]::GetTempPath()) `
    ("pyrpl-314-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $pyrplTestDir | Out-Null
$env:PYRPL_USER_DIR = $pyrplTestDir
uv lock --check
uv run --python 3.14 python -m unittest pyrpl.test.test_redpitaya_fpga_loader pyrpl.test.test_python314_compatibility pyrpl.test.test_ipykernel_compatibility
uv run --python 3.14 nosetests pyrpl/test/test_memory.py pyrpl/test/test_proxyproperty.py pyrpl/test/test_attribute.py
uv run --python 3.14 python -m compileall -q -f pyrpl
```

- Use Nose NG's `nosetests` command for the legacy suite. Pytest does not honor
  all of its Nose-style `setUpAll`/`tearDownAll` conventions and can report
  false setup failures.
- Before tests that use `MemoryTree`, set `PYRPL_USER_DIR` to a newly created
  temporary directory so they cannot create or delete normal user configs.
  Set `REDPITAYA_HOSTNAME=_FAKE_` for broader offline runs that might otherwise
  discover or contact hardware.
- Do not run the entire legacy test suite by default. Many tests inherit live
  hardware setup, can change outputs, or can hang while waiting for a device.
- Build a wheel after packaging or FPGA-asset changes and inspect it for the
  package, configuration, bitstream, DTBO, and CLI entry point.
- `.github/workflows/python314.yml` is the authoritative automated check. The
  older Travis, AppVeyor, Azure, Jenkins, Docker, and Makefile automation is
  historical upstream infrastructure; do not treat its legacy Python matrices
  or live-board jobs as validation for this fork.

## Red Pitaya and FPGA safety

- Before a live load, confirm the board family/profile and use a matching
  bitstream/DTBO pair. The packaged pair targets a Z10 STEMlab 125-14 and must
  never be used on a Z20 board.
- Treat `pyrpl/fpga/README.md` and the asset-hash regression test as
  authoritative. Replacing either FPGA asset requires provenance, new SHA-256
  values, an updated hash test, wheel inspection, and an explicitly authorized
  live validation.
- The fork-specific RTL currently does not reproduce the packaged, verified
  upstream image. A rebuild is a new hardware artifact and must not silently
  replace the working binary.
- Red Pitaya OS 2 requires `/opt/pyrpl/fpga.bit.bin`; OS 3 requires
  `/opt/pyrpl/fpga.bin`. Both use `/opt/pyrpl/fpga.dtbo` with
  `/opt/redpitaya/sbin/overlay.sh`. Do not weaken the fixed-path migration in
  `RedPitaya._configure_os_compatibility()`.
- Use `/dev/xdevcfg` only on a legacy OS and only after verifying it is a
  character device (`test -c`). Redirecting to a missing path as root creates
  an ordinary file without programming the FPGA.
- Never clamp or invent FPGA metadata such as `MINBW`. A zero/nonpositive
  value means the expected FPGA memory map is not active and must raise an
  actionable compatibility error.
- Success requires more than SSH reachability: the overlay must complete, the
  FPGA manager must report `operating`, the monitor client must connect, and
  the signature checks must pass. The verified values are IQ stages `2`, IQ
  shift bits `5`, IQ minimum bandwidth `10`, and PID minimum bandwidth `10`.
- If SSH disappears after the overlay starts, stop retrying. Wait for the board
  to return, inspect uptime, `/tmp/update_fpga.txt`, `/tmp/loaded_fpga.inf`, and
  the FPGA-manager state, and determine whether the board rebooted.

## Configuration and notebooks

- PyRPL user configurations live outside this repository under
  `PYRPL_USER_DIR` or `$HOME\pyrpl_user_dir\config`. Do not commit them.
- `MemoryTree` batches writes with a Qt timer. A short one-shot maintenance
  process must call `_write_to_file()` before exit when persistence matters.
- Restart a Jupyter kernel after changing imported PyRPL code. Do not assume a
  rerun uses new source while an old kernel is alive.
- `test.ipynb` is a local live-device smoke notebook. Preserve its cell content
  and do not execute or rewrite outputs unless the user explicitly requests
  notebook/device validation. It contains device- and machine-specific state;
  sanitize that state and clear saved outputs before adding it to a commit.
