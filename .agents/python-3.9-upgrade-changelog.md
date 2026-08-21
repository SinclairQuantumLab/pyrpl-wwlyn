# CPython 3.9 upgrade and modern Red Pitaya OS migration

This is the standalone, reproducible record of the repository change whose
original commit subject was `Upgraded to python 3.9`. It describes the state
that should be represented by the amended 3.9 commit, before any Python 3.14
work is added.

## Historical boundary

At the time this record was written, the relevant Git objects were:

| Role | Commit | Subject |
| --- | --- | --- |
| Starting point | `fcd94a092f447e1796f92f49a18fdb5798915e02` | `Start managing project with uv` |
| Original 3.9 result | `adbca0a7dd7d023638f1d16133b38ad26094845f` | `Upgraded to python 3.9` |

The original range was therefore:

```text
fcd94a092f447e1796f92f49a18fdb5798915e02..adbca0a7dd7d023638f1d16133b38ad26094845f
```

That range changed 18 files, with 1,588 insertions and 564 deletions. The user
intends to amend the result commit with this changelog only. `git commit
--amend` changes the result commit ID, so the amended commit and its tree—not
the historical ID above—become the permanent source of truth.

This upgrade was broader than a dependency resolver exercise. It also repaired
the package layout and CLI, replaced a machine-specific Conda export, added a
modern Red Pitaya OS 2/3 FPGA loading path and compatible FPGA artifacts,
hardened hardware signature validation, modernized several Qt calls, and added
offline regression coverage.

## Goals and non-goals

The completed work had these goals:

1. Make the checkout consistently target CPython 3.9.
2. Make `pyproject.toml` and `uv.lock` the dependency sources of truth.
3. Package the real root-level `pyrpl/` application instead of the leftover
   `src/pyrpl_change/` scaffold.
4. Make the console entry point call an actual `main()` function.
5. Retain compatibility with the legacy NumPy/SciPy APIs still used by the
   source at that point.
6. Make FPGA programming safe and diagnosable on Red Pitaya OS 2 and OS 3,
   while retaining a guarded legacy `/dev/xdevcfg` path.
7. Package a verified Z10 bitstream/DTBO pair and test its identity.

The work did not modernize all deprecated numerical APIs, migrate to NumPy 2,
replace Quamash, port the legacy Nose suite, or support CPython 3.14. Those are
separate concerns handled by the later 3.14 upgrade.

## Complete file inventory

The original commit changed exactly these files:

| Status | File | Purpose |
| --- | --- | --- |
| Modified | `.python-version` | Selected Python 3.9 instead of 3.8. |
| Added | `AGENTS.md` | Added durable dependency, packaging, test, notebook, and Red Pitaya safety rules. |
| Modified | `README.md` | Replaced stale setup guidance with fork-specific uv/Conda usage and modern-OS warnings. |
| Modified | `pyproject.toml` | Corrected project identity, Python requirement, package mapping, dependency bounds, and CLI. |
| Modified | `pyrpl.yml` | Replaced a machine-specific exported environment with a minimal editable-install bootstrap. |
| Modified | `pyrpl/__main__.py` | Introduced a callable `main()` and robust help handling. |
| Modified | `pyrpl/acquisition_module.py` | Corrected string comparison from identity to equality. |
| Modified | `pyrpl/attributes.py` | Made invalid FPGA `MINBW` metadata fail explicitly. |
| Modified | `pyrpl/fpga/README.md` | Recorded FPGA artifact provenance, hashes, compatibility, and build caveats. |
| Modified | `pyrpl/fpga/red_pitaya.bin` | Replaced the incompatible packaged bitstream with the verified Z10 image. |
| Added | `pyrpl/fpga/red_pitaya.dtbo` | Added the device-tree overlay required by modern Red Pitaya OS releases. |
| Modified | `pyrpl/modules.py` | Updated the bound Qt signal type for the current PyQt5 API. |
| Modified | `pyrpl/redpitaya.py` | Added OS detection, safe upload/programming, cleanup, and hardware signature validation. |
| Added | `pyrpl/test/test_redpitaya_fpga_loader.py` | Added 12 offline regression tests for the loader and packaged assets. |
| Modified | `pyrpl/widgets/module_widgets/iir_widget.py` | Corrected `GraphicsLayoutWidget` construction for modern pyqtgraph. |
| Modified | `pyrpl/widgets/module_widgets/na_widget.py` | Corrected `GraphicsLayoutWidget` construction for modern pyqtgraph. |
| Added | `test.ipynb` | Added a local, live-device smoke notebook with saved machine/device state. |
| Modified | `uv.lock` | Locked the Python 3.9 dependency graph. |

No other file belongs in the 3.9 commit. In particular, `.agents/README.md`,
the Python 3.14 changelog, the Python 3.14 workflow/tests, and the current
Python 3.14 source edits belong to the following commit.

## Python and dependency changes

### Interpreter alignment

The following declarations were aligned on CPython `3.9.*`:

- `.python-version` changed from `3.8` to `3.9`.
- `pyproject.toml` changed `requires-python` from the 3.8 line to `==3.9.*`.
- `pyrpl.yml` selected `python=3.9`.
- `uv.lock` was regenerated for the resulting constraint set.

The intended commands after changing the declarations were:

```powershell
uv lock
uv lock --check
uv sync --locked --dry-run
uv pip check
```

### Compatibility bounds

The 3.9 state intentionally constrained libraries around APIs that the legacy
source still called:

| Dependency | 3.9 constraint | Reason |
| --- | --- | --- |
| NumPy | `>=1.23,<1.24` | The source still used `np.float`, `np.int`, and `np.complex`, which disappear in later NumPy. |
| SciPy | `>=1.9,<1.12` | The lockbox code still imported `scipy.misc.derivative`, removed in later SciPy. |
| lmfit | `>=1.0.1,<1.3.3` | Kept lmfit compatible with the NumPy 1.23 line. |
| netifaces2 | `>=0.0.22` | Supplies the `netifaces` import and a Windows CPython 3.9 wheel; original `netifaces` was a Windows build blocker. |
| ipykernel | `>=6.31` | Established the supported kernel floor used for notebooks. |

The rest of the older direct requirements remained substantially as inherited,
including Quamash and original Nose. This was deliberate scope control, not a
claim that those projects were current.

### Resolved direct dependency versions

For reconstruction and resolver-drift diagnosis, the original 3.9 lock
resolved the direct/runtime-relevant packages as follows:

| Package | Resolved version |
| --- | ---: |
| Project distribution | `0.1.0` |
| scp | `0.16.1` |
| matplotlib | `3.9.4` |
| scipy | `1.11.4` |
| PyYAML | `6.0.3` |
| pandas | `2.3.3` |
| pyqtgraph | `0.13.7` |
| NumPy | `1.23.5` |
| Paramiko | `5.0.0` |
| Nose | `1.3.7` |
| PyQt5 | `5.15.11` |
| PyQt5-Qt5 | `5.15.19` |
| PyQt5-sip | `12.17.1` |
| QtPy | `2.4.3` |
| nbconvert | `7.17.1` |
| jupyter-client | `8.6.3` |
| netifaces2 | `0.0.22` |
| lmfit | `1.3.2` |
| Quamash | `0.6.1` |
| ipykernel | `6.31.0` |
| IPython | `8.18.1` |

Do not substitute current “latest” versions when reproducing this state. Use
the amended 3.9 commit's `uv.lock` with `uv sync --locked`.

## Packaging and environment repair

### Real package mapping

The runtime application is the root-level `pyrpl/` directory. The
`src/pyrpl_change/` directory is a project scaffold and is not the PyRPL
runtime. The upgrade changed the project name from `pyrpl-change` to
`sinclair-pyrpl-wwlyn`, configured uv's build backend to package `pyrpl/` from
the repository root, and set the console script to:

```toml
sinclair-pyrpl-wwlyn = "pyrpl.__main__:main"
```

This prevented a successful build that contained the wrong package.

### CLI repair

`pyrpl/__main__.py` was refactored so the entry point references a real
`main()` function rather than relying only on module import side effects. It
also recognizes both `-h` and `--help`. The program's historical argument
parsing behavior was otherwise retained.

### Conda bootstrap simplification

`pyrpl.yml` had been a 158-line, machine-specific Conda export with an absolute
prefix and a separate old PyRPL installation. It was replaced by a small,
portable conda-forge environment that installs Python 3.9, pip, and this
checkout in editable mode.

The resulting responsibility split was:

- `pyproject.toml`: human-maintained dependency and packaging declarations.
- `uv.lock`: exact resolved dependency graph.
- `pyrpl.yml`: optional Conda bootstrap around the same checkout.

## Source compatibility repairs

### Equality comparison

`pyrpl/acquisition_module.py` changed a comparison equivalent to:

```python
state is not "stopped"
```

to value comparison:

```python
state != "stopped"
```

String identity is an implementation accident and generated a modern Python
warning; the code needed value semantics.

### Qt signal type

`pyrpl/modules.py` replaced the old `pyqtBoundSignal` type check with
`QtCore.SignalInstance`, matching the installed PyQt5 API.

### pyqtgraph constructor calls

The IIR and network-analyzer widgets changed `GraphicsLayoutWidget`
construction to pass `parent=` and `title=` by keyword. This avoids positional
argument interpretation changes in current pyqtgraph.

### Invalid FPGA metadata

`FilterRegister._MAXSHIFT` in `pyrpl/attributes.py` now requires a positive
FPGA `MINBW`. A zero or negative value means the expected FPGA memory map is
not active. It raises an actionable `ExpectedPyrplError` rather than dividing
by zero, clamping the value, or silently inventing compatible metadata.

## Red Pitaya OS 2/3 and FPGA changes

This was the most behaviorally substantial part of the 3.9 change.

### Connection and validation sequence

The connection sequence in `pyrpl/redpitaya.py` became:

1. Establish SSH.
2. Read `/root/.version` and parse the board OS generation.
3. Select and enforce the correct fixed remote FPGA filenames.
4. If requested, upload and program the matching bitstream/DTBO pair.
5. Start the PyRPL server and monitor client.
6. Read FPGA signature metadata and reject a mismatched or inactive memory map.

SSH reachability alone is not considered successful FPGA loading.

### OS-dependent remote paths

The supported paths are:

| OS family | Bitstream path | Overlay path | Programming mechanism |
| --- | --- | --- | --- |
| Red Pitaya OS 2 | `/opt/pyrpl/fpga.bit.bin` | `/opt/pyrpl/fpga.dtbo` | `/opt/redpitaya/sbin/overlay.sh` |
| Red Pitaya OS 3 | `/opt/pyrpl/fpga.bin` | `/opt/pyrpl/fpga.dtbo` | `/opt/redpitaya/sbin/overlay.sh` |
| Legacy OS | local configured server path | Not applicable | Guarded `/dev/xdevcfg` write |

OS 3 uses `fpga.bin`, while the supplied DTBO originally embeds the equal-size
firmware name `fpga.bit.bin`. The loader patches that embedded string in a
temporary DTBO for OS 3, uploads the temporary result, and cleans it up. It
does not mutate the packaged DTBO.

### Upload and overlay behavior

The loader now:

- Resolves bundled assets relative to the installed `pyrpl` package.
- Normalizes server destinations as POSIX paths.
- Retries SCP upload up to three times.
- Stops conflicting server/web services before programming.
- Uploads the bitstream and DTBO as a pair on modern OS versions.
- Uses marker files and delayed command-output checks safely.
- Examines overlay output and requires the FPGA manager state to be
  `operating`.
- Surfaces kernel diagnostics on failure.
- Restores services and the read-only state during cleanup.
- Keeps uploaded artifacts available when programming fails, aiding diagnosis.
- Propagates both primary loading failures and cleanup failures rather than
  reporting false success.

For a legacy OS, `/dev/xdevcfg` is used only after `test -c /dev/xdevcfg`
confirms it is a character device. Redirecting a bitstream as root to a missing
path can create an ordinary file without programming anything, so weakening
this guard is unsafe.

### Hardware signature checks

After connection, the loader reads the IQ/PID metadata registers. The values
must be readable and positive. The explicitly live-validated expected values
for the packaged image are:

| Signature | Expected value |
| --- | ---: |
| IQ stages | `2` |
| IQ shift bits | `5` |
| IQ minimum bandwidth | `10` |
| PID minimum bandwidth | `10` |

A nonpositive or incompatible signature raises `ExpectedPyrplError` with an
actionable compatibility message.

## FPGA artifact identity and provenance

The 3.9 commit changed a material hardware artifact. Preserve this information
when reconstructing or reviewing the commit.

| Artifact | Size | SHA-256 | MD5 |
| --- | ---: | --- | --- |
| Replaced old `red_pitaya.bin` | 2,083,740 bytes | `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed` | `445d5f25202870b084066ee0ae139967` |
| New `red_pitaya.bin` | 2,083,740 bytes | `4894f44b7611f2f0cbc18d339596f28476e452de1bac01a30206864ccd92fffe` | `9fe0c5848be583be21fd0ac82bf8bb74` |
| New `red_pitaya.dtbo` | 5,200 bytes | `9c19b99bef128d6069d44e8294ce6f118ee8513e523673ec02e1510d76877020` | `5e0df7d10ac398d8730af272abd79fbe` |

`pyrpl/fpga/README.md` records that the new pair was obtained from the
`pyrpl-fpga/pyrpl` project on 2026-08-20 and was live-tested on a Z10 STEMlab
125-14 with profile `z10_125` and Red Pitaya OS 2.07. The previously packaged
bitstream reset the board with both tested DTBOs; it was not a working modern-OS
alternative.

There is a historical provenance gap: the exact upstream commit/ref and source
URL were not recorded. Therefore, “download the latest upstream artifact” is
not a reproducible instruction. For a byte-for-byte reproduction, extract the
two files from the amended 3.9 release commit and verify the SHA-256 values
above. Any replacement is a new hardware artifact requiring new provenance,
hashes, regression updates, wheel inspection, and authorized live validation.

The fork's local RTL did not reproduce this verified packaged image. Rebuilding
the RTL and silently replacing the image is outside this upgrade.

## Tests added in the 3.9 commit

`pyrpl/test/test_redpitaya_fpga_loader.py` added 12 offline regression tests.
Together they verify:

1. The packaged bitstream and DTBO have the exact approved sizes and hashes.
2. OS-version parsing distinguishes supported modern and legacy forms.
3. OS 2 selects `fpga.bit.bin`; OS 3 selects `fpga.bin`; both select the fixed
   DTBO path.
4. OS 2 uses the overlay mechanism and never falls through to `/dev/xdevcfg`.
5. The default local DTBO resolves to the bundled package artifact.
6. A missing local DTBO fails before a partial upload.
7. An overlay command failure remains a failure even if FPGA-manager state is
   later reported as `operating`.
8. A legacy load refuses a non-character `/dev/xdevcfg`.
9. A nonzero legacy bitstream-write status is reported.
10. A delayed completion marker is handled.
11. Zero FPGA metadata is rejected after connection.
12. A zero `FilterRegister.MINBW` raises an actionable compatibility error.

These tests use fakes and do not authorize or contact physical hardware.

## Validation and safety procedure

The durable offline validation sequence for the 3.9 state was:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:REDPITAYA_HOSTNAME = "_FAKE_"
$pyrplTestDir = Join-Path ([IO.Path]::GetTempPath()) `
    ("pyrpl-39-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $pyrplTestDir | Out-Null
$env:PYRPL_USER_DIR = $pyrplTestDir

uv lock --check
uv sync --locked --dry-run
uv pip check
uv run --python 3.9 python -m unittest `
    pyrpl.test.test_redpitaya_fpga_loader
uv run --python 3.9 python -m compileall -q -f pyrpl
```

Use original Nose—not pytest—for any selected legacy tests in this historical
state. Pytest does not honor all inherited Nose-style `setUpAll` and
`tearDownAll` conventions. Never run the whole legacy suite by default: many
tests inherit live-hardware setup and can change board outputs or hang.

After packaging or FPGA-asset changes, build a wheel and inspect it for at
least:

- The root `pyrpl` package, not `src/pyrpl_change`.
- The console entry point `pyrpl.__main__:main`.
- `pyrpl/fpga/red_pitaya.bin`.
- `pyrpl/fpga/red_pitaya.dtbo`.
- Global configuration YAML files required at runtime.

The live-device evidence for the verified values and Z10/OS 2.07 compatibility
is historical evidence from the 3.9 work. Do not repeat live loading unless it
is explicitly requested, the device is confirmed to be a matching Z10, and
the bitstream/DTBO hashes match.

## Notebook warning

`test.ipynb` was added in the original 3.9 commit as a local live-device smoke
notebook. It contains one code cell with saved outputs, a device-specific
configuration selection, a device hostname, and calls that request both FPGA
and server reload. Executing it mutates a physical target.

The notebook was not sanitized before the original commit. Before amending or
sharing the 3.9 commit, review it separately, remove private or
machine-specific state, clear saved outputs, and decide deliberately whether a
live-device notebook belongs in version control. This changelog does not
repeat any of those values. Do not execute or rewrite it merely to inspect the
Python upgrade.

## Exact reconstruction procedure

To recreate the 3.9 result independently:

1. Start from the tree at
   `fcd94a092f447e1796f92f49a18fdb5798915e02`.
2. Create a branch or worktree dedicated to the reconstruction; do not modify
   an unrelated branch.
3. Apply the interpreter, packaging, environment, source, loader, widget,
   documentation, and test changes described above.
4. Obtain `red_pitaya.bin` and `red_pitaya.dtbo` from the amended 3.9 commit,
   not an unpinned upstream download, and verify their SHA-256 hashes.
5. Regenerate `uv.lock` with Python constrained to `3.9.*` and compare the
   direct resolutions to the version table above.
6. Run the safe offline validation with an isolated `PYRPL_USER_DIR`, fake
   hostname, and offscreen Qt.
7. Build and inspect the wheel.
8. Compare the resulting file list to the 18-file inventory above.
9. Treat physical-device validation as a separately authorized operation.

For a historical diff while the original objects still exist:

```powershell
git diff --stat fcd94a092f447e1796f92f49a18fdb5798915e02 adbca0a7dd7d023638f1d16133b38ad26094845f
git diff --name-status fcd94a092f447e1796f92f49a18fdb5798915e02 adbca0a7dd7d023638f1d16133b38ad26094845f
```

After amendment, substitute the new 3.9 commit ID. The expected tree content,
artifact hashes, and validation behavior remain the same.

## Review checklist for the 3.9 amendment

Before amending the commit:

- Confirm the branch and worktree are the intended ones.
- Confirm this is the only newly staged file:
  `.agents/python-3.9-upgrade-changelog.md`.
- Review `test.ipynb` for private/machine-specific state and saved output.
- Confirm neither `.agents/README.md` nor the 3.14 changelog is staged.
- Confirm no Python 3.14 implementation, dependency, workflow, or test file is
  staged into the amendment.
- Record the new amended commit ID for the following 3.14 commit message or
  release notes.

One safe staging check is:

```powershell
git add -- .agents/python-3.9-upgrade-changelog.md
git diff --cached --name-status
```

The expected staged list has exactly one added file. This record does not
perform the amendment; the reviewer controls that history-changing action.
