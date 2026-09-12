# Red Pitaya OS 2 upgrade implementation

Branch: `gen1-os2/feature/os-upgrade` (originally developed on
`develop/red-pitaya-upgrade`); field fixes are developed below it on
`gen1-os2/fix/preflight-markers`.

Baseline: `c535358` (`Upgrade the fork to Python 3.14`)

Target: the author's original-generation STEMlab 125-14 with Zynq-7010,
running Red Pitaya OS 2.07 or newer within major version 2. This does not claim
Gen 2, Z7020, early OS 2, or OS 3 compatibility.

## Preserved FPGA image and new overlay

The fork bitstream was not rebuilt or changed:

- `pyrpl/fpga/red_pitaya.bin`
- SHA-256:
  `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`

OS 2.07+ needs FPGA Manager/device-tree integration. Two observed OS 2
`overlay.sh` generations stage custom firmware under different basenames, so
the fork packages two source-controlled variants for the preserved Z7010 image:

- `red_pitaya_os2_z10.dts` / `red_pitaya_os2_z10.dtbo` requests
  `fpga.bit.bin`; DTBO SHA-256:
  `41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9`
- `red_pitaya_os2_z10_fpga_bin.dts` /
  `red_pitaya_os2_z10_fpga_bin.dtbo` requests `fpga.bin`; DTBO SHA-256:
  `99f0fd0c3ce394fb0c86e4dec95895b8a5855cc80ebbfd5fedc961fb9ed4a35c`

The sources differ only in `firmware-name`. They were derived by comparing the
maintained PyRPL overlay with this fork's implemented RTL and Vivado block
design. They supply the four fabric clocks (125, 250, 50, and 200 MHz) and the
two AXI fabric-interface nodes. They intentionally omit the maintained
overlay's AXI XADC node: this fork directly
instantiates `XADC` in `pyrpl/fpga/rtl/red_pitaya_ams.v` and exposes those
measurements through its own register map.

The tracked DTBOs were compiled with Device Tree Compiler 1.7.2:

```text
dtc -@ -I dts -O dtb -o red_pitaya_os2_z10.dtbo red_pitaya_os2_z10.dts
dtc -@ -I dts -O dtb -o red_pitaya_os2_z10_fpga_bin.dtbo red_pitaya_os2_z10_fpga_bin.dts
```

`dtc` reports overlay address-cell warnings for the AFI nodes. The source
deliberately follows the overlay form used by the supported OS 2 base device
tree; both compiled trees were decompiled and inspected. Recompilation must
produce the exact hashes above or the binary change must receive hardware
review.

## Loader contract

`pyrpl/redpitaya.py` now detects the ecosystem version from
`/opt/redpitaya/version.txt` before falling back to `/root/.version`, and then
probes actual loader capabilities.

- Legacy OS selects `/dev/xdevcfg` only when it is a character device and no
  overlay loader is present. It checks the device again immediately before
  writing and verifies the shell result.
- OS 2.07+ selects `/opt/redpitaya/sbin/overlay.sh` only when that executable
  exists and its source declares a recognized fixed custom FPGA basename.
- Version and capability probes require terminal markers. Truncated SSH output
  is refused before any mutation.
- Overlay-source, hardware-profile, and current-state probes use separate
  non-interactive SSH command channels and verify their exit status. They do
  not depend on an interactive terminal's command echo, prompt, or timing.
- The overlay contract probe reads only `CUSTOMFPGA` assignments instead of
  copying the complete installed `overlay.sh` through the interactive SSH
  channel.
- Early OS 2 and OS 3 stop with an actionable unsupported-loader error.
- Historical `fpga.bit.bin` and newer `fpga.bin` OS 2 contracts are supported.
  The loader inspects the installed script rather than inferring the contract
  from the release number. An unknown future contract is refused.
- Before an OS 2 upload or other mutation, the loader requires Red Pitaya
  ecosystem profile 1 or 2, FPGA path `z10_125`, and Zynq type `Z7010`.
  Gen 2 and Z7020 profiles are refused.
- Built-in assets resolve relative to the installed `pyrpl` package, not the
  process working directory. Explicit custom relative paths remain relative to
  the working directory.
- The bitstream hash and selected matching DTBO hash must pass before any upload
  or device mutation. A renamed upstream, cross-paired, or modified artifact is
  refused.
- OS 2 uses `/opt/pyrpl/fpga.bit.bin` or `/opt/pyrpl/fpga.bin`, as declared by
  the installed script, plus fixed `/opt/pyrpl/fpga.dtbo`.
- Success requires the overlay command to succeed, FPGA Manager to report
  `operating`, and `/tmp/loaded_fpga.inf` to identify the exact staged BIN and
  DTBO paths in a `pyrpl_` load.
- Failed loads retain the staged files and collect the overlay log, manager
  state, and kernel tail for diagnosis. The code does not retry programming
  after the overlay begins.
- After the monitor client connects, four positive filter-metadata registers
  are required. A zero `MINBW` now raises a compatibility error instead of a
  `ZeroDivisionError`.
- `RedPitaya.preflight_fpga_update()` applies the same loader, asset, and
  hardware-profile gates without mutation and reports uptime, current FPGA
  Manager state, and the current loaded-image identifier. The packaged
  `python -m pyrpl.redpitaya_preflight HOSTNAME` command constructs the device
  with FPGA reload, server reload, and autostart all disabled.

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

- DTC 1.7.2 recompilation produces both tracked DTBO hashes exactly.
- `compileall` succeeds for `pyrpl`.
- The loader, Python 3.14, and real-ipykernel unittest set passes 33 tests.
- The safe Nose NG compatibility set passes 17 tests.
- A wheel built from the working tree contains the exact BIN and exactly two
  matching DTS/DTBO variants plus the preflight module; all three packaged
  binary hashes match.
- That wheel installs into a new Python 3.14 environment outside the source
  tree, where all 23 loader tests pass and the preflight command is available.

## Live validation status

On 2026-09-11, the user ran the read-only preflight against a board at
`192.168.50.155`. It successfully established SSH, read Red Pitaya OS
`2.07-3` from `/opt/redpitaya/version.txt`, and established that the installed
`overlay.sh` is executable. The overlay-contract read then timed out without
reaching the profile gate. Investigation found that the three `printf`-based
terminal probes emitted a literal `""` where the Python side expected no
quotes. The fake SSH tests had hidden that defect by returning the expected
marker independently of the command. The fix makes the fake require the exact
correct marker construction. No file was uploaded, no service was stopped,
and the FPGA was not programmed during this attempt.

Corrective commit `f3078a3` fixed the malformed marker text and limited the
overlay read to its `CUSTOMFPGA` assignment, but the user reported the same
timeout on a repeat field run. The follow-up correction therefore removes
interactive-shell markers from the three OS 2-specific probes entirely and
uses Paramiko's non-interactive command channel. This second correction has
passed offline regression tests but still awaits a repeat field run.

Red Pitaya's current official reprogramming documentation labels the complete
custom `overlay.sh` workflow as OS `2.07-43` or newer. The test board reports
`2.07-3`, so a successful non-interactive read may legitimately establish that
the installed script predates the recognized custom-FPGA contract. In that
case the expected result is an immediate, explicit unsupported-contract
diagnostic rather than a timeout; supporting that older image would be a
separate loader path.

A repeat read-only preflight with the fix is still required. Controlled live
loading also remains separately gated and requires explicit authorization and
the board booted from recoverable OS media. To cover OS 2.07+ rather than one
release, validate at least one `fpga.bit.bin` OS 2 image and one newer
`fpga.bin` OS 2 image. Before loading, collect the reported OS, detected
overlay contract, profile ID, FPGA path, Zynq type, and uptime. Then require
all of the following:

```powershell
python -m pyrpl.redpitaya_preflight rp-xxxxxx.local
```

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
