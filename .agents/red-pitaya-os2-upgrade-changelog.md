# Red Pitaya OS 2 upgrade implementation

Branch: `develop/red-pitaya-upgrade`

Baseline: `c535358` (`Upgrade the fork to Python 3.14`)

Target: the author's original-generation STEMlab 125-14 with Zynq-7010,
running a pinned Red Pitaya OS 2.07 release. This does not claim Gen 2, Z7020,
early OS 2, or OS 3 compatibility.

## Preserved FPGA image and new overlay

The fork bitstream was not rebuilt or changed:

- `pyrpl/fpga/red_pitaya.bin`
- SHA-256:
  `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`

OS 2.07 needs FPGA Manager/device-tree integration. The fork now packages a
source-controlled overlay specifically for the preserved Z7010 image:

- source: `pyrpl/fpga/red_pitaya_os2_z10.dts`
- compiled overlay: `pyrpl/fpga/red_pitaya_os2_z10.dtbo`
- DTBO SHA-256:
  `41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9`

The source was derived by comparing the maintained PyRPL overlay with this
fork's implemented RTL and Vivado block design. It supplies the four fabric
clocks (125, 250, 50, and 200 MHz) and the two AXI fabric-interface nodes. It
intentionally omits the maintained overlay's AXI XADC node: this fork directly
instantiates `XADC` in `pyrpl/fpga/rtl/red_pitaya_ams.v` and exposes those
measurements through its own register map.

The tracked DTBO was compiled with Device Tree Compiler 1.7.2:

```text
dtc -@ -I dts -O dtb -o red_pitaya_os2_z10.dtbo red_pitaya_os2_z10.dts
```

`dtc` reports overlay address-cell warnings for the AFI nodes. The source
deliberately follows the overlay form used by the supported OS 2 base device
tree; the compiled tree was decompiled and inspected. Recompilation must
produce the exact hash above or the binary change must receive hardware review.

## Loader contract

`pyrpl/redpitaya.py` now detects the ecosystem version from
`/opt/redpitaya/version.txt` before falling back to `/root/.version`, and then
probes actual loader capabilities.

- Legacy OS selects `/dev/xdevcfg` only when it is a character device and no
  overlay loader is present. It checks the device again immediately before
  writing and verifies the shell result.
- OS 2.07 selects `/opt/redpitaya/sbin/overlay.sh` only when that executable
  exists.
- Early OS 2 and OS 3 stop with an actionable unsupported-loader error.
- Later OS 2 minor releases are also refused. Newer ecosystem source changed
  the custom filename from `fpga.bit.bin` to `fpga.bin`; that contract and its
  matching overlay firmware name need a separate implementation and test.
- Before an OS 2 upload or other mutation, the loader requires Red Pitaya
  ecosystem profile 1 or 2, FPGA path `z10_125`, and Zynq type `Z7010`.
  Gen 2 and Z7020 profiles are refused.
- Built-in assets resolve relative to the installed `pyrpl` package, not the
  process working directory. Explicit custom relative paths remain relative to
  the working directory.
- Both OS 2 asset hashes must match the approved fork pair before any upload or
  device mutation. A renamed upstream or modified artifact is refused.
- OS 2 uses the fixed paths `/opt/pyrpl/fpga.bit.bin` and
  `/opt/pyrpl/fpga.dtbo`, as required by the Red Pitaya `pyrpl` overlay entry.
- Success requires the overlay command to succeed, FPGA Manager to report
  `operating`, and `/tmp/loaded_fpga.inf` to identify a `pyrpl_` load.
- Failed loads retain the staged files and collect the overlay log, manager
  state, and kernel tail for diagnosis. The code does not retry programming
  after the overlay begins.
- After the monitor client connects, four positive filter-metadata registers
  are required. A zero `MINBW` now raises a compatibility error instead of a
  `ZeroDivisionError`.

## Offline validation

The dedicated regression suite uses fake SSH/SCP objects and cannot contact a
board. It covers hashes, overlay contents, version precedence, loader
selection, profile refusal before mutation, fixed remote paths, failed overlay
and manager states, legacy character-device/write checks, and incompatible
FPGA metadata:

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:REDPITAYA_HOSTNAME = "_FAKE_"
$env:PYRPL_USER_DIR = Join-Path $env:TEMP ("pyrpl-os2-test-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $env:PYRPL_USER_DIR | Out-Null
.\.venv\Scripts\python.exe -m unittest -v pyrpl.test.test_redpitaya_fpga_loader
```

Offline code, legacy compatibility, clean-wheel installation, and wheel-content
checks are required before handoff. Record their exact final results in the
commit or handoff summary rather than treating this file as an append-only log.

Current offline state on CPython 3.14.4:

- DTC 1.7.2 recompilation produces the tracked DTBO hash exactly.
- `compileall` succeeds for `pyrpl`.
- The loader, Python 3.14, and real-ipykernel unittest set passes 27 tests.
- The safe Nose NG compatibility set passes 17 tests.
- A wheel built from the working tree contains the exact BIN, DTS, and sole
  DTBO; both packaged binary hashes match.
- That wheel installs into a new Python 3.14 environment outside the source
  tree, where all 18 loader tests pass.

## Live validation still required

No physical Red Pitaya has been contacted or programmed by this implementation
work. A controlled live test needs separate explicit authorization and a board
booted from recoverable OS 2.07 media. Before loading, collect the reported OS,
profile ID, FPGA path, Zynq type, and uptime. Then require all of the following:

1. the profile gate identifies the original Z7010 STEMlab 125-14;
2. `overlay.sh` completes without loss of SSH or a board reboot;
3. `/tmp/update_fpga.txt` is successful and `/tmp/loaded_fpga.inf` identifies
   the fork load;
4. `/sys/class/fpga_manager/fpga0/state` reports `operating`;
5. the PyRPL monitor server and client connect and the fork metadata checks
   pass;
6. controlled ASG, scope, PID/filter, setpoint, and slow-analog checks match
   the known OS 1.04-18 behavior.

If SSH disappears once loading starts, do not retry. Wait for the board to
return and inspect uptime, the two `/tmp` diagnostics, FPGA Manager state, and
the kernel log to determine whether it rebooted.
