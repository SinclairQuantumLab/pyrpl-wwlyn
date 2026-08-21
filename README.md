# Sinclair PyRPL fork

PyRPL (Python Red Pitaya Lockbox) turns a Red Pitaya into a DSP, measurement,
and feedback-control platform. This Sinclair Lab fork targets CPython `3.14.*`
on 64-bit Windows and packages the `pyrpl` application as
`sinclair-pyrpl-wwlyn`.

This repository is the source of truth for the fork. Upstream SourceForge
executables and the separate PyPI distribution named `pyrpl` do not contain
these changes.

## Installation

Install [uv](https://docs.astral.sh/uv/), then run this from the repository
root:

```powershell
uv sync --locked
```

That creates `.venv` with CPython 3.14 and the exact versions in `uv.lock`.
For an existing Python 3.14 environment, editable installs are also supported:

```powershell
python -m pip install -e ".[test]"
```

The optional Conda bootstrap installs this checkout using the same project
metadata:

```powershell
conda env create -f pyrpl.yml
conda activate pyrpl-env3
```

Restart any Jupyter kernel that imported PyRPL before upgrading so it uses the
new interpreter and source. PyRPL reuses a modern kernel's asyncio loop instead
of replacing it and pumps Qt events on that loop, so top-level `await` and
Qt-timer-backed PyRPL futures remain responsive.

## Quick start

Connect the Red Pitaya or STEMlab to a reachable LAN, then launch a named PyRPL
configuration:

```powershell
uv run sinclair-pyrpl-wwlyn your_configuration_name
```

The equivalent module command is
`uv run python -m pyrpl your_configuration_name`. Configuration names keep
device settings separate, including when multiple boards are used.

Red Pitaya OS 2 and 3 are detected automatically. With `reloadfpga=True`,
PyRPL loads the bundled matching bitstream and device-tree overlay; a legacy OS
uses `/dev/xdevcfg` only when it is a real character device. The bundled assets
target the Z10 STEMlab 125-14 and must not be loaded on a Z20 board. See
[`pyrpl/fpga/README.md`](pyrpl/fpga/README.md) before changing or loading FPGA
assets.

## Safe offline verification

The maintained `nose-ng` package supplies the `nosetests` command used by the
legacy tests. In PowerShell, isolate configuration writes and disable hardware
discovery before running the maintained offline checks:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:NOSE_IGNORE_CONFIG_FILES = "1"
$env:REDPITAYA_HOSTNAME = "_FAKE_"
$pyrplTestDir = Join-Path ([IO.Path]::GetTempPath()) `
    ("pyrpl-314-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $pyrplTestDir | Out-Null
$env:PYRPL_USER_DIR = $pyrplTestDir

uv lock --check
uv sync --locked --dry-run
uv pip check
uv run --no-sync python -m compileall -q -f pyrpl
uv run --no-sync python -m unittest `
    pyrpl.test.test_redpitaya_fpga_loader `
    pyrpl.test.test_python314_compatibility `
    pyrpl.test.test_ipykernel_compatibility
uv run --no-sync nosetests `
    pyrpl/test/test_memory.py `
    pyrpl/test/test_proxyproperty.py `
    pyrpl/test/test_attribute.py
```

Do not run the entire inherited suite as a routine check. Several legacy tests
expect live hardware, can change outputs, or can hang while waiting for a
device.

## Documentation and updates

This README defines the supported installation and validation workflow.
[`AGENTS.md`](AGENTS.md) records contributor constraints, and
[`pyrpl/fpga/README.md`](pyrpl/fpga/README.md) records FPGA asset provenance.
`Documentation.md` and the Sphinx tree contain useful upstream background but
also historical installation and release instructions.

The [upstream PyRPL documentation](https://pyrpl.readthedocs.io/) is useful as
an API reference, but it does not define this fork's Python or packaging
support. Report fork-specific problems in the
[Sinclair PyRPL issue tracker](https://github.com/SinclairQuantumLab/pyrpl-wwlyn/issues).

To update an existing checkout safely:

```powershell
git pull --ff-only
uv lock --check
uv sync --locked
```

## License

This repository is licensed under the GNU General Public License v3.0 or
later. See [`LICENSE`](LICENSE).
