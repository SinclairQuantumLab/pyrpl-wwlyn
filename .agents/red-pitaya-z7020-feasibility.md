# Z7020 Gen 2 feasibility — 2026-09-12

The user requested a parallel, read-only engineering assessment while standard
Z7010 Gen 2 readiness work continues. No FPGA build, RTL modification, branch
promotion, or device access was performed for this assessment.

## Conclusion

A preservation-first port is realistic: a moderate platform adaptation with
substantial simulation, timing, and bench validation, not a complete DSP
rewrite. It requires a separately built Z7020 image. Allowing the existing
Z7010 image through the loader's profile check is not a port.

AI can trace and modify the Verilog, construct self-checking testbenches,
automate Vivado, and interpret implementation reports. Physical correctness
and equivalent control behavior must be established by those tools and actual
measurements, not by the agent's confidence.

## What the fork implements

- `pyrpl/fpga/rtl/red_pitaya_pid_block.v`: PSR 12, ISR 32, gain width 30;
  held P contribution and frozen I accumulator; 16 signed 14-bit setpoints;
  synchronized rising-edge advance, reset, index and wrap logic.
- `red_pitaya_dsp.v`: PID0/1/2 hold uses DIO_P0/1/2; advance uses DIO_P3/4/5
  or the software-generated pulse.
- `pyrpl/hardware_modules/pid.py`: sequence enable/write/reset at 0x130,
  0x134, 0x140; index/wrap/value readback at 0x240, 0x244, 0x24C.

These are concrete contracts to preserve rather than replace with maintained
PyRPL's implementation. Python register-write tests are useful but are not an
RTL simulation of these behaviors.

## Why a platform port is plausible

The pinned official FPGA source has a
[Z20_G2 build target](https://github.com/RedPitaya/RedPitaya-FPGA/blob/728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674/red_pitaya_vivado_Z20_G2.tcl)
for `xc7z020clg400-1`, including PyRPL constraints and 125/250/50/200 MHz
fabric clocks. The
[ecosystem build matrix](https://github.com/RedPitaya/RedPitaya/blob/0e46d64396a57752bf97315789d6cc6c9fbddad8/Makefile.x86#L273)
also selects PyRPL for `Z20_125_V2`, using `Z20_G2` / `z20_125_v2`.
This establishes a platform reference, not validation of this fork.

The [specific Z7020 Gen 2 Pro hardware](https://redpitaya.readthedocs.io/en/latest/developerGuide/hardware/GEN2/125-14_Gen2_Z7020_Pro/top.html)
uses LTC2145-14 ADC / AD9767 DAC, unlike the TI-based converter families.
The comparison of common ADC/DAC/DIO/PWM/serial-link package pins against
[official Gen 2 PyRPL constraints](https://github.com/RedPitaya/RedPitaya-FPGA/blob/728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674/prj/pyrpl/sdc/red_pitaya_G2.xdc)
found matching assignments. XADC logical-port ordering differs, however, so
copying the entire official XDC would not preserve the fork's channel map.

## Necessary work and non-interchangeable pieces

1. Create a separate part/build target and artifact path, with an explicit RTL
   source list. Never overwrite `pyrpl/fpga/red_pitaya.bin`.
2. Regenerate/adapt the PS/AXI wrapper and review clocks, resets, GPIO and
   constraints. Preserve the register bus and HP0/HP1 interfaces.
3. Keep the fork DSP and direct XADC. The
   [official block design](https://github.com/RedPitaya/RedPitaya-FPGA/blob/728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674/prj/pyrpl/ip/system.tcl#L423)
   instantiates an AXI XADC at 0x83C00000 and cannot be imported wholesale.
4. Validate the exact board/boot DDR configuration. Product documentation
   advertises 1 GB, whereas the pinned
   [PS configuration](https://github.com/RedPitaya/RedPitaya-FPGA/blob/728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674/prj/barebones/ip/ps7_config.tcl)
   describes a 512 MB aperture. This does not by itself require a DDR
   controller rewrite; exploiting additional RAM is a separate feature.
5. Derive/validate a companion DTBO from the actual implemented platform, then
   bind the loader to the new part/profile/artifact hashes.

## Main uncertainties: reproducibility and timing

Local source inspection found:

- the original BIN lacks complete reproducible-build provenance, as recorded
  in `pyrpl/fpga/README.md`;
- `ip/system_bd.tcl` is a Vivado 2015.4 export with an XADC connection remaining
  after XADC creation was commented out;
- `rtl/tb_red_pitaya_pid_block.v` is empty;
- the saved `out/post_route_timing_summary.rpt` reports WNS -4.094 ns,
  8,093 setup-failing endpoints and worst hold slack -2.163 ns. Most setup
  failures are in the 125 MHz ADC/DSP domain.

The saved report is not proven to be the report for the currently shipped
BIN. Do not infer that the field-tested BIN necessarily has those exact
violations. Conversely, do not dismiss them as false paths without analysis.
Adding pipeline stages can change feedback latency/phase and needs an explicit
behavior-preservation decision.

Vivado, xvlog, xelab and xsim launchers are installed under
`C:\Xilinx\Vivado\2023.2\bin`, but are not on PATH. Their license/device
support and actual execution were not checked. The pinned official
[toolchain requirement](https://github.com/RedPitaya/RedPitaya-FPGA/blob/728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674/README.md#L7)
is Vivado 2025.1. Either use a matching environment or explicitly regenerate
and validate the platform for 2023.2; do not assume cross-version success.

## Smallest useful follow-on, if implementation is authorized

First lock down PID/hold/sequence and bus behavior with self-checking RTL
simulation. Then build the separate platform, run simulation, synthesis,
implementation, CDC/DRC and timing checks, and retain a source/toolchain/hash/
report manifest. Finally compare I/O, hold, triggers and control behavior on
the original and target boards. Extra RAM, E3 GPIO/LVDS and external-clock
features are not necessary for this first functional port.
