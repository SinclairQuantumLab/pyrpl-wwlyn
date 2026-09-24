# Repaired Z7020 / OS 2 user-test preparation — 2026-09-24

## Scope and lineage

The user explicitly requested a device-ready **repaired develop**, not another
test of the accepted original-logic main. Merge `00df760` brings main `3023600`
into `gen2pro-os2/develop` from `08a7ea7`, retaining the shared repairs from
`e7479166c03c15bdd244e2153e974b4596815041`. No history is rewritten or main advanced.

The entire RTL tree is identical to the shared repair checkpoint. Relative to
author `387faf3`, only `red_pitaya_pid_block.v` and `red_pitaya_filter_block.v`
differ: declaration visibility, the disabled-D connection, explicit shift
padding/pause net declarations, and the equivalent literal-zero cleanup.
There is no PID/filter redesign, timing repair, clock change or added pipeline
stage. Existing Z7010 and original-logic Z7020 images, both DTBOs, PS shell,
board constraints and build.tcl are retained byte-for-byte from the main.

## Simulation and implementation

- Real XSim 2023.2 run: `TEMP/pyrpl-pid-rtl-nmlkz1w7`.
- PASS: 342 PID checks; five filter families each pass 4,096 checks.
- Fresh full build: `TEMP/z20-repair-74c65e8e`, source checkpoint `00df760`.
- The separately exported artifact is `red_pitaya_z20_gen2_repaired.bit.bin`.
  Its final hash, build reports and timing findings are recorded in the adjacent
  packaged JSON and the repaired build evidence record. Tool success is not
  timing closure. No device has been contacted for this preparation.

The loader retains the exact profile-22 / z20_125_v2 / Z7020 check for both
Pro images and both existing overlay firmware-name contracts. Selection is
by verified image hash, not basename alone. Preflight reports the selected
lineage and whether common repairs are included. Corrupt, unknown and
mismatched-board images remain rejected before upload.

## Completed build and validation

All 21,764 routable nets routed, with zero routing errors and zero bitstream
DRC errors (133 warnings, no severity overrides). Final setup WNS is -4.369 ns
(6,802 failing endpoints); hold WHS is -2.362 ns (28 failing endpoints).
The DNA clock and incomplete I/O constraints remain findings. This is not a
timing repair or evidence of repaired-image hardware behavior.
The 4,045,568-byte image SHA-256 is
`24e3d58678ec15a98e44455c945577915b38c11038c4d1638ee50808ed12d549`.

Evidence directory: `TEMP/pyrpl-z20-repaired-validation-20260924`.
All 124 Python sources compiled; 86 focused unittests passed, including the
real-ipykernel regression, original/repaired loader guards, source preservation
and notebook template checks. Five legacy memory/proxy tests passed. A fresh
Python 3.14 wheel install passed dependency checks and the same 86 tests
(one repository-only ignore-policy check skipped in the extracted source).
The 157-entry wheel contains both distinct Pro images, the original Z7010 BIN,
exactly the two existing DTBOs and provenance. Simulation/target sources stay
in the source archive, not the runtime wheel. No user notebook was executed.

## Notebook preservation

Before editing, the local notebook was backed up byte-for-byte to ignored
`.agents/local-notebooks/test-gen2pro-before-repaired-20260924-170047.ipynb`,
SHA-256 `da7a36b580ec1a897be0405676aad6d41927353d31f5d43029ef8a014991aa30`.
Only the selected image/provenance and explanatory labels change locally.
Credentials, hostname, config name, measurement code and saved outputs remain
unchanged. Outputs are explicitly labeled historical until rerun. The clean
template uses a separate `gen2pro-os2-repaired` config; the local notebook
retains the user's existing config for their repeat experiment.

Restart the kernel and run the notebook in order: local selection, read-only
preflight, FPGA programming, server connection, metadata, signal tests.
The user performs all device operations. Record the new image hash with the
result; an old notebook success or an old image is not repaired-image evidence.
