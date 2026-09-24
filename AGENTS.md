# PyRPL fork agent guidance

## Shared PID source integration (2026-09-24)

- This develop branch directly integrates `fix/pid-rtl-shadowing` at
  `e747916`, including declaration visibility, the disabled-D connection,
  explicit filter shift padding/pause nets, and the equivalent literal-zero
  cleanup. This explicitly authorizes these common source repairs on this
  development line; it does not authorize further RTL redesign.
- The target's FPGA images, DTBOs, loader, clocks and notebook are retained.
  Existing packaged images do not acquire these source repairs merely by
  merging. No replacement image, hardware validation or main promotion is
  claimed. Keep original-logic feature candidates separate.
- Timing remains an open finding, not a proven deployed-hardware flaw or a
  predetermined repair task. Changes are deferred pending understanding of
  the relevant build, constraints and device behavior. Shorter actual delays
  or a low-latency trade-off with empirical validation are possible explanations,
  not measured conclusions or established author intent. No clock/latency
  changes or timing repair without a new request.
- Prior simulation evidence is in `.agents/common-pid-rtl-fix-changelog.md`
  and `.agents/root-pid-repair-rollout.md`; the latter describes the historical
  topic rollout, not the current branch layout. The historical timing study
  is `.agents/common-z7010-timing-investigation.md`. This integration uses
  source/tree preservation checks, not a fresh simulation or field test.

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
- Current implementation work targets the standard Z7010 Gen 2 on OS 2 only.
  Preserve the existing Pro candidate without advancing it. A separate agent
  may assess Z7020 feasibility read-only at the user's request; that is not
  authorization to change FPGA assets or implement the Z7020 port.

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
  loader work.
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

- Shared PID RTL implementation changes require the real XSim contract in
  `pyrpl/fpga/sim/run_pid_contract.py`; see its README. Prior passing evidence
  is not hardware validation or timing closure. For an unchanged-source merge,
  verify source identity and target preservation; do not repeat full suites
  merely to integrate an already validated update.

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
  because software cannot infer the load. A Z7020 Gen 2 target still requires
  a separately authorized FPGA rebuild/port. TI-based Gen 2 boards require a
  different converter/platform design and remain outside the preservation-
  first path.
