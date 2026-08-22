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

## Website
The official PyRPL website address is [http://pyrpl.readthedocs.io/](http://pyrpl.readthedocs.io). The information on the website is more up-to-date than in this readme.

## Installation
The easiest and fastest way to get PyRPL is to download and execute the [precompiled executable for windows](https://sourceforge.net/projects/pyrpl/files/latest/download). This option requires no extra programs to be installed on the computer.

This checkout targets Python 3.9. From the repository root, the recommended
installation is:

```bash
uv sync --locked
```

Alternatively, create the provided Conda environment; it installs this checkout
and reads the same dependency constraints from `pyproject.toml`:

```bash
conda env create -f pyrpl.yml
conda activate pyrpl-env3
```

With an existing Python 3.9 virtual environment, `python -m pip install -e .`
is also supported.

## Quick start
First, hook up your Red Pitaya / STEMlab to a LAN accessible from your computer (follow the instructions for this on redpitya.com and make sure you can access your Red Pitaya with a web browser by typing its ip-address /  hostname into the address bar).
In a command line terminal, type
```
python -m pyrpl your_configuration_name
```
A GUI should open, let you configure the redpitaya device you would like to use, and you can start playing around with pyrpl. Different strings for 'your_configuration_name' create different configurations that will be automatically remembered by PyRPL, for example if you have several different redpitayas. Different RedPitayas with different configuration names can be run simultaneously in separate terminals.

Red Pitaya OS 2 and 3 are detected automatically. With `reloadfpga=True`,
PyRPL uses the configured bitstream and the OS overlay manager. This fork
preserves its custom `pyrpl/fpga/red_pitaya.bin` but intentionally does not
bundle a device-tree overlay. On OS 2 or 3, pass an explicitly verified,
matching `dtbo_filename` for that FPGA build and board; loading fails before
upload if it is absent. Clear or replace any saved
`fpga/red_pitaya.dtbo` setting left by the superseded upstream-artifact
experiment. Older OS images use `/dev/xdevcfg` only when it is a real
character device. Never substitute an official upstream bitstream for the
fork image merely to make a connection succeed.

## Issues
We collect a list of common problems on the [documenation website](http://pyrpl.readthedocs.io/en/latest/user_guide/installation/common_problems.html). If you do not find your problem listed there, please report all problems or wishes as new issues on [this page](https://github.com/lneuhaus/pyrpl/issues), so we can fix it and improve the future user experience.

## Unit test
If you want to check whether PyRPL works correctly on your machine, navigate with a command line terminal into the pyrpl root directory and type the  following commands (by substituting the ip-address / hostname of your Red Pitaya, of course)
```
set REDPITAYA_HOSTNAME=your_redpitaya_ip_address
nosetests
```
All tests should take about 3 minutes and finish without failures or errors. If there are errors, please report the console output as an issue (see the section "Issues" below for detailed explanations).

## Next steps / documentation
The full html documentation is hosted at [http://pyrpl.readthedocs.io](http://pyrpl.readthedocs.io). Alternatively, you can download a .pdf version at [https://media.readthedocs.org/pdf/pyrpl/latest/pyrpl.pdf](https://media.readthedocs.org/pdf/pyrpl/latest/pyrpl.pdf). We are still in the process of creating an fully up-to-date version of the documentation of the current code. If the current documentation is wrong or insufficient, please post an [issue](https://github.com/lneuhaus/pyrpl/issues/new) and we will prioritize documenting the part of code you need.

## Updates
Since PyRPL is continuously improved, you should install upgrades if you expect bugfixes. If you installed PyRPL by using pip, just type
```
pip install --upgrade pyrpl
```

If instead you have clonded the github repository (recommended for bleeding-edge updates), navigate into the pyrpl root directory on your local harddisk computer and type
```
git pull
```

## FPGA bitfile generation (only for developers)
In case you would like to modify the logic running on the FPGA, you should make sure that you are able to [generate a working bitfile on your machine](http://pyrpl.readthedocs.io/en/latest/developer_guide/fpga_compilation.html). In short, to do so, you must install Vivado 2015.4 [(64-bit windows](windows web-installer](https://www.xilinx.com/member/forms/download/xef.html?filename=Xilinx_Vivado_SDK_2015.4_1118_2_Win64.exe&akdm=1) or [Linux)](https://www.xilinx.com/member/forms/download/xef.html?filename=Xilinx_Vivado_SDK_2015.4_1118_2_Lin64.bin&akdm=1) [together with a working license](http://pyrpl.readthedocs.io/en/latest/developer_guide/fpga_compilation.html#fpga-license). Next, with a terminal in the pyrpl root directory, type
```
cd pyrpl/fpga
make
```
Compilation should take between 10 and 30 minutes, depending on your machine. If there are no errors during compilation, the new bitfile (pyrpl/fpga/red_pitaya.bin) will be automatically used at the next restart of PyRPL. The best way to getting started is to skim through the very short Makefile in the fpga directory and to continue by reading the files mentioned in the makefile and the refences therein. All verilog source code is located in the subdirectory pyrpl/fpga/rtl/. 

## License
Please read our license file [LICENSE](https://github.com/lneuhaus/pyrpl/blob/master/LICENSE) for more information. 
