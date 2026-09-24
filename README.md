[<img src="http://pyrpl.readthedocs.io/en/latest/_static/logo.png" width="250" alt="PyRPL">](http://www.pyrpl.org/)

[![travis status](https://travis-ci.org/lneuhaus/pyrpl.svg?branch=master "Travisstatus")](https://travis-ci.org/lneuhaus/pyrpl)
[![appveyor status](https://ci.appveyor.com/api/projects/status/wv2acmg869acg5yy?svg=true)](https://ci.appveyor.com/project/lneuhaus/pyrpl)
[![code coverage](https://codecov.io/github/lneuhaus/pyrpl/coverage.svg?branch=master "Code coverage")](https://codecov.io/gh/lneuhaus/pyrpl)
[![Python versions on PyPI](https://img.shields.io/pypi/pyversions/pyrpl.svg)](https://pypi.python.org/pypi/pyrpl/)
[![PyRPL version on PyPI](https://img.shields.io/pypi/v/pyrpl.svg "PyRPL on PyPI")](https://pypi.python.org/pypi/pyrpl/)
[![Download pyrpl](https://img.shields.io/sourceforge/dt/pyrpl.svg)](https://sourceforge.net/projects/pyrpl/files/)
[![Documentation Status](https://readthedocs.org/projects/pyrpl/badge/?version=latest)](http://pyrpl.readthedocs.io/en/latest/)
[![join chat on gitter](https://badges.gitter.im/JoinChat.svg "Join chat on gitter")](https://gitter.im/lneuhaus/pyrpl)
[![License](https://img.shields.io/pypi/l/pyrpl.svg)](https://github.com/lneuhaus/pyrpl/blob/master/LICENSE)

[![Download PyRPL](https://a.fsdn.com/con/app/sf-download-button)](https://sourceforge.net/projects/pyrpl/files/)
[![LGPLv3](https://www.gnu.org/graphics/gplv3-88x31.png)](https://www.gnu.org/licenses/gpl.html)

PyRPL (Python RedPitaya Lockbox) turns your RedPitaya into a powerful DSP device, especially suitable as a digital lockbox and measurement device in quantum optics experiments.

## Accepted device baseline (2026-09-24)

`gen1-os2/main` records the user's successful real-device testing and acceptance
of the original-logic baseline. The shared PID/filter repairs remain on
`gen1-os2/develop`, not this main. See the
[acceptance record](.agents/pre-repair-main-acceptance-20260924.md) for source
snapshots, previous observations and evidence limits. This is user-reported
acceptance, not a new agent-run test or proof of timing closure. Older
pending-field-test statements below describe earlier development stages.

## Website
The official PyRPL website address is [http://pyrpl.readthedocs.io/](http://pyrpl.readthedocs.io). The information on the website is more up-to-date than in this readme.

## Installation

This fork targets CPython 3.14. From the repository root on Windows:

```powershell
uv sync --extra test
uv run --extra test python --version  # Must report Python 3.14.x.
```

The committed `uv.lock` makes this environment reproducible. The `test` extra
includes the notebook kernel, coverage support, and the maintained Nose NG
runner used by the selected legacy tests.

Alternatively, create the supplied Conda environment:

```powershell
conda env create -f pyrpl.yml
conda activate pyrpl-py314
```

Both methods install this checkout, including its fork-specific FPGA image and
the two OS 2 Z7010 overlay filename variants.
The declared dependency bounds support NumPy 2 without manual monkeypatches.
Do not
install the unrelated `pyrpl` package from PyPI over this checkout.

### Historical upstream installation

The instructions below predate this fork's Python 3.14 environment and are
retained as historical PyRPL documentation.

The easiest and fastest way to get PyRPL is to download and execute the [precompiled executable for windows](https://sourceforge.net/projects/pyrpl/files/latest/download). This option requires no extra programs to be installed on the computer.

If instead you would like to use and/or modify the source code, make sure you have an
installation of Python (2.7, 3.4, 3.5, or 3.6). If you are new to Python or unexperienced with fighting installation issues, it is recommended to install the [Anaconda](https://www.continuum.io/downloads) Python distribution, which allows to install all PyRPL dependencies via
```
conda install numpy scipy paramiko pandas nose pip pyqt qtpy pyqtgraph pyyaml nbconvert
```
Check [this documentation section](http://pyrpl.readthedocs.io/en/latest/user_guide/installation/common_problems.html#anaconda-problems) for hints if you are unable to execute conda in a terminal. Alternatively, if you prefer creating a virtual environment for pyrpl, do so with the following two commands
```
conda create -y -n pyrpl-env numpy scipy paramiko pandas nose pip pyqt qtpy pyqtgraph pyyaml nbconvert
activate pyrpl-env
```
If you are not using Anaconda, you must manually install the python package [PyQt5](https://pypi.python.org/pypi/PyQt5) or [PyQt4](https://pypi.python.org/pypi/PyQt4), which requires a working C compiler installation on the system.

Next, clone (if you have a [git client](https://git-scm.com/downloads) installed - recommended option) the pyrpl repository to your computer with 
```
git clone https://github.com/lneuhaus/pyrpl.git
```
or [download and extract](https://github.com/lneuhaus/pyrpl/archive/master.zip) (if you do not want to install git on your computer) the repository. 

Install PyRPL by navigating with the command line terminal (the one where the pyrpl-env environment is active in case you are using anaconda) into the pyrpl root directory and typing
```
python -m pip install --editable .
```

## Quick start

### Red Pitaya compatibility

This branch preserves the author's exact FPGA image for an
original-generation STEMlab 125-14 with Zynq-7010. The loader supports:

- the author's Red Pitaya OS 1.04-18 environment through `/dev/xdevcfg`, after
  verifying that it is a character device; and
- Red Pitaya OS 2.07+ on ecosystem profile 1 or 2 (`z10_125`, Z7010), through
  FPGA Manager and a packaged, fork-specific overlay.

The loader reads the installed `overlay.sh` and supports both known OS 2 custom
firmware basenames, `fpga.bit.bin` and `fpga.bin`, with a matching hash-pinned
DTBO for each. An unknown loader contract, early OS 2, OS 3, Gen 2, or Z7020 is
refused before FPGA files are uploaded. OS 2.07+ support has passed
hardware-free regression tests; FPGA loading and PyRPL connection were also
field-tested on one original Z7010 board running OS 2.07-3. Analog/control
functionality and the newer `fpga.bin` contract still need field validation.
The built-in FPGA filenames resolve from the installed package, so launching
PyRPL from another working directory does not substitute another image.

After booting the intended OS 2 image, the packaged preflight command can
collect the release, overlay contract, board profile, current FPGA Manager
state, uptime, and exact local asset hashes without loading anything:

```powershell
python -m pyrpl.redpitaya_preflight rp-xxxxxx.local
```

It opens an SSH connection and prompts for the password, but sets
`reloadfpga=False`, `reloadserver=False`, and `autostart=False`. It refuses an
unsupported loader, mismatched board profile, unapproved asset, or incomplete
SSH result. Run it only when live read-only access to the named board is
intended.

For a new checkout, copy `test.ipynb.template` to `test.ipynb` and edit its
hostname. The template is versioned; `test.ipynb` is an ignored local working
copy where you can keep your settings and results.

First, hook up your Red Pitaya / STEMlab to a LAN accessible from your computer (follow the instructions for this on redpitya.com and make sure you can access your Red Pitaya with a web browser by typing its ip-address /  hostname into the address bar).
In a command line terminal, type
```
python -m pyrpl your_configuration_name
```
A GUI should open, let you configure the redpitaya device you would like to use, and you can start playing around with pyrpl. Different strings for 'your_configuration_name' create different configurations that will be automatically remembered by PyRPL, for example if you have several different redpitayas. Different RedPitayas with different configuration names can be run simultaneously in separate terminals.

## Issues
We collect a list of common problems on the [documenation website](http://pyrpl.readthedocs.io/en/latest/user_guide/installation/common_problems.html). If you do not find your problem listed there, please report all problems or wishes as new issues on [this page](https://github.com/lneuhaus/pyrpl/issues), so we can fix it and improve the future user experience.

## Unit test

Run the hardware-free compatibility suite from the repository root:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:REDPITAYA_HOSTNAME = "_FAKE_"
$env:PYRPL_USER_DIR = Join-Path $env:TEMP ("pyrpl-test-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $env:PYRPL_USER_DIR | Out-Null
uv run --extra test python -m unittest -v tests\test_python314_compatibility.py tests\test_ipykernel_compatibility.py
uv run --extra test python -m unittest -v pyrpl.test.test_redpitaya_fpga_loader
uv run --extra test nosetests -v pyrpl.test.test_memory pyrpl.test.test_proxyproperty tests\test_python39_compatibility.py tests\test_python314_compatibility.py
```

The complete legacy suite includes tests that discover, contact, and mutate a
Red Pitaya, so it is not an ordinary offline test command. Live-device
validation must be explicitly planned for the confirmed board, OS, and fork
bitstream combination.

## Next steps / documentation
The full html documentation is hosted at [http://pyrpl.readthedocs.io](http://pyrpl.readthedocs.io). Alternatively, you can download a .pdf version at [https://media.readthedocs.org/pdf/pyrpl/latest/pyrpl.pdf](https://media.readthedocs.org/pdf/pyrpl/latest/pyrpl.pdf). We are still in the process of creating an fully up-to-date version of the documentation of the current code. If the current documentation is wrong or insufficient, please post an [issue](https://github.com/lneuhaus/pyrpl/issues/new) and we will prioritize documenting the part of code you need.

## Updates
Since PyRPL is continuously improved, you should install upgrades if you expect bugfixes. If you installed PyRPL by using pip, just type

**Historical note:** the command below installs the official PyPI package, not
this fork. Do not run it for this checkout; update this checkout with Git.

```
pip install --upgrade pyrpl
```

If instead you have clonded the github repository (recommended for bleeding-edge updates), navigate into the pyrpl root directory on your local harddisk computer and type
```
git pull
```

## FPGA bitfile generation (only for developers)

The packaged `pyrpl/fpga/red_pitaya.bin` is a hash-pinned artifact that defines
this fork's behavior. Do not replace it merely by running the historical build;
see `pyrpl/fpga/README.md` for its provenance and the separately reproducible
OS 2 overlay.

In case you would like to modify the logic running on the FPGA, you should make sure that you are able to [generate a working bitfile on your machine](http://pyrpl.readthedocs.io/en/latest/developer_guide/fpga_compilation.html). In short, to do so, you must install Vivado 2015.4 [(64-bit windows](windows web-installer](https://www.xilinx.com/member/forms/download/xef.html?filename=Xilinx_Vivado_SDK_2015.4_1118_2_Win64.exe&akdm=1) or [Linux)](https://www.xilinx.com/member/forms/download/xef.html?filename=Xilinx_Vivado_SDK_2015.4_1118_2_Lin64.bin&akdm=1) [together with a working license](http://pyrpl.readthedocs.io/en/latest/developer_guide/fpga_compilation.html#fpga-license). Next, with a terminal in the pyrpl root directory, type
```
cd pyrpl/fpga
make
```
Compilation should take between 10 and 30 minutes, depending on your machine. If there are no errors during compilation, the new bitfile (pyrpl/fpga/red_pitaya.bin) will be automatically used at the next restart of PyRPL. The best way to getting started is to skim through the very short Makefile in the fpga directory and to continue by reading the files mentioned in the makefile and the refences therein. All verilog source code is located in the subdirectory pyrpl/fpga/rtl/. 

## License
Please read our license file [LICENSE](https://github.com/lneuhaus/pyrpl/blob/master/LICENSE) for more information. 
