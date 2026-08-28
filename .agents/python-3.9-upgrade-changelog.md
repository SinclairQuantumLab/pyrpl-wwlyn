# Python 3.9 upgrade changelog

This document records the clean CPython 3.9 upgrade of the
`wwlyn/pyrpl_change` fork. It describes the final upgrade commit, not the
earlier experimental Python, FPGA-loader, or device-tree work that remains
visible in Git history.

## Commit boundary

The authoritative author-fork baseline is:

| Role | Commit | Subject |
| --- | --- | --- |
| Author-fork baseline | `387faf3012c21925c9905d81a95cb681ac7d1b22` | `Add README.` |
| Explicit aggregate revert | `e7d62205e1032ce2d0a19d70a14396d050a67f7f` | `Revert Python upgrade development` |

The aggregate revert's tree is byte-for-byte identical to the baseline tree.
The Python 3.9 upgrade commit is its direct child. Consequently,
`git show HEAD` on `develop/python-upgrade` displays the effective upgrade
from the original fork rather than mixing it with the reverted experiments.

## Goals

The upgrade has a deliberately narrow scope:

1. Install and import this fork on CPython 3.9 for Windows.
2. Resolve the demonstrated numerical, Qt, and network-interface dependency
   conflicts without monkeypatching third-party modules.
3. Retain the root `pyrpl/` package and legacy setuptools packaging layout.
4. Preserve the author's FPGA image and leave the Red Pitaya, RTL, register,
   server, and `pyrpl/software_modules/` source trees byte-identical.
5. Add hardware-free regression coverage for each source compatibility fix
   and for the FPGA preservation boundary.

It does not port the project to newer Python versions, modernize every
deprecated API, add modern Red Pitaya OS loading, add a DTBO, or rebuild the
FPGA. Live-device validation is limited to the author's matching legacy
hardware and OS environment described below.

## Changed files

The amended upgrade commit changes these files relative to the author-fork
baseline:

| File | Purpose |
| --- | --- |
| `.agents/python-3.9-upgrade-changelog.md` | Records the final upgrade and validation evidence. |
| `.gitignore` | Ignores the local virtual environment and generated Nose coverage XML. |
| `.python-version` | Selects Python 3.9. |
| `AGENTS.md` | Records the preservation boundary and safe validation rules. |
| `Documentation.md` | Points users to declared compatibility bounds while retaining the author's manual workaround as historical text. |
| `README.md` | Adds the supported Python 3.9 pip/Conda installation paths and warns against overwriting the fork with PyPI PyRPL. |
| `pyproject.toml` | Adds the standard setuptools PEP 517 build-system declaration. |
| `pyrpl.yml` | Replaces a Python 3.8 machine export and absolute prefix with a portable Python 3.9 Conda bootstrap. |
| `pyrpl/acquisition_module.py` | Uses value comparison for the acquisition state. |
| `pyrpl/modules.py` | Uses QtPy's exported bound-signal type. |
| `pyrpl/widgets/module_widgets/iir_widget.py` | Passes the graph title by keyword. |
| `pyrpl/widgets/module_widgets/na_widget.py` | Passes the graph title by keyword. |
| `setup.cfg` | Uses the current metadata spelling and disables the old universal Python 2/3 wheel setting. |
| `setup.py` | Declares Python 3.9 and the compatibility dependency ranges. |
| `tests/test_python39_compatibility.py` | Adds isolated, offline regression tests. |

No other path is part of this upgrade.

## Dependency resolution

### Required compatibility bounds

The following bounds are intentional:

| Dependency | Constraint | Reason |
| --- | --- | --- |
| Python | `>=3.9,<3.10` | This branch targets CPython 3.9 only. |
| NumPy | `>=1.23,<1.24` | The legacy source still uses aliases such as `np.float`, `np.int`, and `np.complex`. |
| SciPy | `>=1.9,<1.12` | Lockbox code still imports `scipy.misc.derivative`. |
| lmfit | `>=1.0.1,<1.3.3` | Keeps lmfit compatible with NumPy 1.23. |
| Paramiko | `>=2.0,<4` | Avoids an untested Paramiko 4 major upgrade. Validation resolved 3.5.1 and exercised live SSH against the author's legacy target environment. |
| netifaces2 | `>=0.0.22` | Provides the `netifaces` import and a Windows CPython 3.9 wheel. The original `netifaces` distribution failed to build on the target machine. |
| pyqtgraph | `>=0.11` | Supports the author's `GraphicsLayoutWidget` migration. |
| PyQt5 | `>=5.15` | Supplies the supported Qt binding. |
| QtPy | `>=2` | Exposes `QtCore.SignalInstance` consistently for PyQt5. |

The inherited Nose, nbconvert, jupyter-client, and Quamash requirements remain
in `setup.py` to avoid broad packaging changes. `ipykernel` is included in
the Conda environment for notebook use but is not forced into every pip
installation.

### Tested resolution

A fresh CPython 3.9.25 installation resolved the compatibility-critical
packages to:

| Package | Version |
| --- | ---: |
| NumPy | `1.23.5` |
| SciPy | `1.11.4` |
| lmfit | `1.3.2` |
| Paramiko | `3.5.1` |
| netifaces2 | `0.0.22` |
| PyQt5 | `5.15.11` |
| QtPy | `2.4.3` |
| pyqtgraph | `0.13.7` |
| Quamash | `0.6.1` |

These are validation results, not a claim of an exact transitive lock. This
upgrade uses compatible ranges in `setup.py`; it does not add a `uv.lock`.

## Packaging and environment changes

- `.python-version`, `setup.py`, and `pyrpl.yml` all select CPython 3.9.
- `pyproject.toml` declares setuptools as the build backend while
  `setup.py` remains the package metadata and dependency declaration.
- The duplicate `distutils.core.setup` import was removed so it cannot shadow
  `setuptools.setup`.
- The existing root-level `pyrpl/` package discovery is retained.
- `requirements.txt` remains the one-line local install target (`.`).
- The 158-line `pyrpl.yml` machine export was replaced because it selected
  Python 3.8, contained Python-3.8-specific builds, installed a separate PyPI
  PyRPL distribution, and embedded the author's absolute Conda prefix.
- The legacy `python setup.py test` hook remains present for preservation;
  the supported selected offline checks are invoked with Nose directly.

### Generated and reverted artifacts

- The author-fork baseline contains no `uv.lock`. A tracked lockfile existed
  only in the reverted development commits; the aggregate revert removes it,
  and it is not part of the effective Python 3.9 upgrade.
- `unit_test_coverage.xml` is generated by Nose and was never tracked in Git.
  It contained 10,620 XML lines during validation, but moving or regenerating
  that report did not remove source code. The filename is now ignored.

## Source compatibility fixes

### Acquisition state comparison

`AcquisitionModule.curve_async()` now compares `running_state` by value:

```python
if self.running_state != "stopped":
```

The previous identity comparison could stop an already-stopped acquisition
when an equal string was represented by a different object.

### Qt signal detection

`SignalLauncher` now checks signals against `QtCore.SignalInstance`, the
type exported by QtPy 2 with PyQt5. Both widget connection and signal cleanup
are covered offline.

### pyqtgraph graph titles

The IIR and network-analyzer graph helpers now call
`GraphicsLayoutWidget(title=title)`. Passing the title positionally was
interpreted as the QWidget parent by current pyqtgraph. The callback parent
objects continue to be stored exactly as before; no new Qt ownership semantics
were introduced.

## FPGA and Red Pitaya preservation

The upgrade does not change:

- `pyrpl/fpga/` or its RTL and build files;
- `pyrpl/redpitaya.py`;
- `pyrpl/pyrpl_server/`;
- `pyrpl/hardware_modules/`;
- `pyrpl/attributes.py`;
- `pyrpl/software_modules/`; or
- `pyrpl/pyrpl.py`.

The packaged `pyrpl/fpga/red_pitaya.bin` remains the author's exact Git blob
`b306438ea69753197570da0b5a403b1b380301ed`:

| Property | Value |
| --- | --- |
| Size | `2,083,740` bytes |
| SHA-256 | `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed` |

No `.dtbo`, `.dtb`, `.dts`, or `.dtsi` file is added. No upstream FPGA
artifact is substituted. The upgrade also does not clamp or invent FPGA
metadata to hide an incompatible memory map.

## Offline regression coverage

`tests/test_python39_compatibility.py` lives outside the `pyrpl` package so
it can set these safeguards before importing PyRPL:

- `QT_QPA_PLATFORM=offscreen`;
- `REDPITAYA_HOSTNAME=_FAKE_`; and
- a temporary `PYRPL_USER_DIR`.

Its four tests verify:

1. the author's bitstream SHA-256 and absence of a DTBO;
2. value—not identity—comparison of `running_state`;
3. IIR and network-analyzer graph title construction while retaining callback
   parent references; and
4. Qt signal connection, emission, and cleanup through QtPy.

## Validation completed

The package-bearing implementation tree first passed hardware-free validation:

- CPython `3.9.25` created and installed the checkout successfully.
- The fresh installation contained 68 installed distributions and
  `uv pip check --python ...` reported no broken requirements.
- All 71 non-test modules discovered with `pkgutil.walk_packages` imported
  successfully with offscreen Qt, a fake Red Pitaya hostname, and an isolated
  user directory.
- `compileall` completed for `pyrpl/` and `tests/`.
- The selected Nose suite ran nine tests:
  `pyrpl.test.test_memory`, `pyrpl.test.test_proxyproperty`, and
  `tests/test_python39_compatibility.py`. All nine passed.
- `pyrpl.yml` parsed with Python 3.9, ipykernel, pip, and a local checkout
  install. Conda itself was not available, so environment creation was not
  executed.
- A recorded clean-tree wheel build used standard Python 3.9 `venv` and pip
  with a Git archive of the package-bearing tree.
- Inspection recorded 129 wheel entries, the 2,083,740-byte fork bitstream
  with the expected SHA-256, and no device-tree file.
- Installing that wheel into a fresh Python 3.9 environment succeeded;
  `pip check` passed and PyRPL imported from `site-packages`.

### Authorized live-device smoke validation

Live validation was subsequently authorized on a confirmed original-generation
STEMlab 125-14 running the author's Red Pitaya ecosystem `1.04-18`:

- `/opt/redpitaya/version.txt` reported ecosystem version `1.04`, build `18`.
  `/root/.version` reported `1.07`, which is the underlying Linux image rather
  than the ecosystem release; the kernel reported `4.9.0-xilinx`.
- `/dev/xdevcfg` was verified to be a character device before programming.
- The preserved fork bitstream with SHA-256
  `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`
  was loaded through the author's legacy path, with no DTBO substitution.
- CPython `3.9.25` completed `Pyrpl(...)` initialization with FPGA and server
  reload enabled. The process exited successfully, and the earlier lockbox
  `ZeroDivisionError` did not recur.
- Read-only postflight confirmed ecosystem `1.04-18`, the character device,
  an installed executable PyRPL server, and cleanup of the staged bitstream.

This validates only the author's matching original-generation Zynq-7010
hardware and legacy OS environment. It does not establish compatibility with
Gen 2, Z7020, 4-input, slave, or OS 2.x/3.x targets.

## Not validated

- `test.ipynb` was not executed, modified, or included.
- No FPGA-manager or overlay behavior was exercised; those mechanisms belong
  to newer Red Pitaya OS releases and remain outside this upgrade.
- The complete legacy test suite was not run because parts of it require or
  mutate hardware.
- No claim is made that this branch supports a hardware, OS, or bitstream
  combination that the author did not provide.

Live-device validation is a separate, explicitly authorized task and must use
the author's matching hardware artifacts rather than substituting an upstream
bitstream or DTBO.
