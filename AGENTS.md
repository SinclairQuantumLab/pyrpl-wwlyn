# PyRPL fork agent guidance

## Current main acceptance (2026-09-24)

- `gen1-os1/main` is the user-accepted, device-tested original-logic baseline
  selected from `3eacfe2`. See
  `.agents/pre-repair-main-acceptance-20260924.md` for the user's confirmation,
  exact source selection, previous evidence and limits. No new agent-run
  test or broader timing/profile guarantee is claimed.
- This status supersedes earlier pending-test/no-main instructions below.
  Historical first-test scopes and build logs retain their original evidence.
  Do not import the shared PID/filter repairs into this main without new
  authorization: those remain on the separate develop line. Preserve the
  original RTL, images, loader and notebook. Timing remains an open finding,
  not an established deployed defect or an authorized repair task.


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

## Branching

- Authorized local layout: the primary checkout serves
  `gen2-pro-os2/feature/device-upgrade`; `.worktrees/gen1-os2` serves
  `gen1-os2/main`, with its own environment and local notebook. The external
  `working-vs1` worktree belongs to another worker and must remain untouched.
- Recommend persistent device/OS worktrees under one contained directory,
  such as `.worktrees/<genX-osY>/`, rather than scattered project folders.
  Each worktree should have its own `.venv` and ignored local notebook.
  Document this convention here; do not add bootstrap scripts or create/move
  worktrees without an explicit request. Preserve existing worktrees and
  their local files. Git clones reproduce committed guidance and published
  branches, not local worktree layouts, environments or ignored notebooks.
- This contained device/OS worktree layout is intentional, not permission
  for agents to create arbitrary additional worktrees. Existing worktrees
  do not imply authorization to add more. Creating, moving, removing or
  reorganizing worktrees requires the user's explicit approval; use the
  appropriate existing worktree for ordinary development.
- Scale validation to the task. Commit-only requests require diff/staging
  review, not test reruns. Minor changes need only directly relevant checks.
  The full validation checklist below is for substantive implementation or
  release work, or an explicit request, not every handoff or branch operation.

- Common work uses focused topic branches such as `feature/*`, `fix/*`, and
  `refactor/*`. Global `develop` is optional shared integration when several
  changes need testing together, not a mandatory propagation step.
- Device- or OS-specific work belongs under its target compatibility root,
  for example `gen1-os2/feature/os-upgrade` or
  `gen2-os2/fix/device-profile`.
- A compatibility root's `main` branch means that combination is considered
  commissionable. Do not create or advance it based only on offline evidence
  when its field gate is still open.
- When authorized and ready, merge each specific common topic directly into
  the intended `<root>/develop` branches. Use explicit merge commits
  (`--no-ff`) naming the update and target so each root's adoption is visible
  and the shared commits retain their identity. Inspect the incoming ancestry
  first; a topic name does not guarantee it contains no unrelated changes.
- Create `<root>/fix/*` or other root-specific topics only when adaptation,
  substantial conflict resolution or separate development/validation is
  needed, not as automatic intermediate copies of every common update.
  Propagation into develop does not authorize promotion into `<root>/main`.
- Use `git cherry-pick -x` for an intentionally selective backport that must
  not import the source branch's other changes, such as common documentation
  authored on a device-specific topic. Do not merge a device-upgrade branch
  wholesale into other roots just to share its documentation.
- Do not rebase published compatibility `main` branches or rewrite validation
  history.

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

## Configuration and notebooks

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
