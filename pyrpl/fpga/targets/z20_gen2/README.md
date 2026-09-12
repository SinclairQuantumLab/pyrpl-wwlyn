# Z7020 Gen 2 Pro development target

Target part: `xc7z020clg400-1`; board family: STEMlab 125-14 Z7020 Gen 2 Pro;
OS integration target: major 2, release 2.07+. This is not the Z7010 Pro family.

This directory currently contains a module-level synthesis checkpoint, not a
complete board build. It reads the fork's PID/filter RTL and produces only a
checkpoint and reports in a new output directory. It never calls the legacy
Makefile and never writes `red_pitaya.bin` or any DTBO.

```powershell
& C:/Xilinx/Vivado/2023.2/bin/vivado.bat -mode batch -nojournal `
  -source pyrpl/fpga/targets/z20_gen2/synth_pid.tcl `
  -tclargs C:/path/to/a/new/pid-synthesis-directory
```

Vivado 2023.2 is pinned for this module checkpoint; its device files and
synthesis license were tested locally. The official platform reference at
RedPitaya-FPGA commit `728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674` instead uses
2025.1. This module test does not demonstrate that its full block design can
be imported into 2023.2.

Still required before a full image:

1. Adapt a reproducible Z7020 PS/AXI block design and wrapper, preserving the
   fork register bus and HP0/HP1 paths without importing the official AXI XADC.
2. Validate exact board constraints, clocks/resets and DDR boot assumptions.
3. Elaborate and simulate the complete fork datapath and top-level triggers.
4. Synthesize, place, route, and inspect CDC/DRC and setup/hold timing for the
   complete target. A module post-synthesis timing estimate is not that gate.
5. Produce separately named BIN/DTBO artifacts with source/toolchain/hash
   provenance, then implement their paired loader selection and regressions.

The runtime loader continues to reject Z7020. Keep the original Z7010 artifacts
unchanged. Hardware tests and any compatibility-main promotion remain deferred.
