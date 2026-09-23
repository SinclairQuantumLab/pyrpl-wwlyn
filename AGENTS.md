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
- Built wheels must contain both `pyrpl/fpga/red_pitaya.bin` and
  `pyrpl/fpga/red_pitaya.dtbo`.
- `pyrpl/fpga/red_pitaya.dtbo` and
  `pyrpl/test/test_redpitaya_fpga_loader.py` are required parts of modern-OS
  support; do not mistake them for disposable local files when preparing a
  change.
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
  package, configuration, bitstream, DTBO, and CLI entry point.

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

## Common-policy comparison

- At the start of each new agent/thread working on this repository, and
  after a clone, fetch or pull, compare the common AGENTS.md policies across
  all available local branches and remote-tracking branches before making
  changes. Repeat after branch/worktree switches or common-policy edits.
- Enumerate refs with `git for-each-ref refs/heads refs/remotes` and read
  instruction files with `git show <ref>:AGENTS.md`, without checking out
  other branches. Deduplicate identical file blobs; inspect referenced
  common-policy files too if the guidance has been split. Include the
  current checkout's uncommitted instructions without discarding them.
- This check covers locally available refs, not unseen remote branches.
  Do not fetch/pull merely to perform it. Note missing instructions or
  limited/shallow history when relevant; absence is not permission to
  ignore known user policies. Keep the check lightweight: no test suites
  and no repeated full scan each turn unless refs or policies changed.
- Before an agent switches branches, record the source branch/commit and any
  uncommitted instruction changes. After switching, reread the destination's
  AGENTS.md and compare its common policies with the source; use read-only
  Git diffs rather than switching other worktrees to inspect them.
- When starting work in another existing worktree, compare common policies
  with the previously used checkout when known. After editing common policy,
  identify which active compatibility branches still need that update.
- Compare shared workflow rules only (permissions, worktree management,
  branching, notebook preservation and validation proportionality). Preserve
  device/OS-specific instructions, FPGA constraints and validation evidence.
  A later timestamp or commit alone does not establish which policy is right.
- Report missing or conflicting common rules and reconcile them in the
  current task's authorized scope. Do not overwrite entire AGENTS.md files,
  modify another worker's files, or automatically commit/update all branches.
  Cross-branch propagation and hook installation require explicit approval.
  This is an agent workflow rule, not an installed Git hook.

