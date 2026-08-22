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
- Do not create `.agents/` until a separate substantial runbook or release
  procedure is needed. If one is added, link it from this file and keep one
  authoritative location for each fact.

## Supported environment and dependencies

- This checkout targets CPython `3.9.*`. `.python-version`, `pyproject.toml`,
  `uv.lock`, and `pyrpl.yml` must remain aligned.
- Use `uv sync --locked` to create/synchronize the environment and `uv run`
  for repository commands. `pyproject.toml` and `uv.lock` are the dependency
  sources of truth; `pyrpl.yml` is only a Conda bootstrap around this checkout.
- Preserve these intentional compatibility bounds unless the corresponding
  legacy APIs are modernized and tested:
  - NumPy `>=1.23,<1.24` for `np.float`, `np.int`, and `np.complex` usage.
  - SciPy `>=1.9,<1.12` for `scipy.misc.derivative`.
  - lmfit `>=1.0.1,<1.3.3`, compatible with the NumPy bound.
- Keep `netifaces2`, which supplies the `netifaces` import and a Windows
  CPython 3.9 wheel. The original `netifaces` package is a Windows build
  blocker here.
- After dependency changes, regenerate `uv.lock`, then run `uv lock --check`,
  `uv sync --locked --dry-run`, and `uv pip check`.

## Code and packaging layout

- The real application is the root `pyrpl/` package. `src/pyrpl_change/` is a
  leftover scaffold and is not the runtime package or console entry point.
- The console entry point must remain `pyrpl.__main__:main`, and uv's build
  backend must package `pyrpl/` from the repository root.
- Built wheels must contain the fork-specific
  `pyrpl/fpga/red_pitaya.bin`. This repository intentionally does not bundle
  a DTBO; adding one requires explicit user authorization and proof that it
  matches the fork image and target board.
- `pyrpl/test/test_redpitaya_fpga_loader.py` is a required part of modern-OS
  loader support; do not mistake it for a disposable local file.
- `README.md` is the current installation and quick-start guide.
  `pyrpl/fpga/README.md` owns FPGA provenance and build details.
  `Documentation.md` contains historical instructions; its manual dependency
  monkeypatching and site-packages replacement advice is not authoritative.

## Safe offline validation

Set Qt to offscreen for tests that import the GUI stack:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
uv lock --check
uv run --python 3.9 python -m unittest pyrpl.test.test_redpitaya_fpga_loader
uv run --python 3.9 python -m compileall -q -f pyrpl
```

- Use Nose for the legacy suite. Pytest does not honor all of its Nose-style
  `setUpAll`/`tearDownAll` conventions and can report false setup failures.
- Before tests that use `MemoryTree`, set `PYRPL_USER_DIR` to a newly created
  temporary directory so they cannot create or delete normal user configs.
  Set `REDPITAYA_HOSTNAME=_FAKE_` for broader offline runs that might otherwise
  discover or contact hardware.
- Do not run the entire legacy test suite by default. Many tests inherit live
  hardware setup, can change outputs, or can hang while waiting for a device.
- Build a wheel after packaging or FPGA-asset changes and inspect it for the
  package, configuration, fork bitstream, absence of an unauthorized DTBO,
  and CLI entry point.

## Red Pitaya and FPGA safety

- Never replace the fork-specific `red_pitaya.bin`, add a DTBO, or substitute
  an upstream FPGA artifact as part of dependency, Python, packaging, or
  connection work without explicit user authorization. FPGA semantics are a
  defining feature of this fork.
- Treat `pyrpl/fpga/README.md` and the bitstream-hash regression test as
  authoritative. The packaged image is the exact binary introduced by commit
  `61295d9`; its reproducible-build provenance is incomplete, so a rebuild is
  a new hardware artifact and must not silently replace it.
- Before a live load, confirm the board family/profile and use an explicitly
  validated matching bitstream/DTBO pair. No matching DTBO is bundled. A
  modern-OS load must fail safely before upload when `dtbo_filename` is empty
  or missing.
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
  the loaded fork build's signature checks must pass. Results obtained with a
  substituted upstream image do not validate this fork.
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
