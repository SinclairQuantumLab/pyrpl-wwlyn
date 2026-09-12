# Z7020 Gen 2 Pro development target

Target part: `xc7z020clg400-1`; board family: STEMlab 125-14 Z7020 Gen 2 Pro;
OS integration target: major 2, release 2.07+. This is not the Z7010 Pro family.

This is an offline development target, not a load-ready image generator.
It builds a new PS/AXI shell around the fork's existing top-level RTL. Outputs
are checkpoints and reports in a new directory; it never calls the legacy
Makefile and never writes a BIN or DTBO. The runtime loader still rejects Z7020.

## Full-design build

Use a short, **new** absolute output path (Vivado on Windows has path-length
limits). These commands run on the development computer, not the Red Pitaya.

```powershell
& C:/Xilinx/Vivado/2023.2/bin/vivado.bat -mode batch -notrace -nojournal `
  -log C:/fpga-builds/z20-run1.log `
  -source pyrpl/fpga/targets/z20_gen2/build.tcl `
  -tclargs C:/fpga-builds/z20-run1 implement
```

Create the parent directory first. The last argument selects `bd` (generate
and validate the PS shell), `synth` (default; synthesize the whole fork), or
`implement` (also optimize/place/route). An existing output directory is
refused, never cleaned or overwritten. Save the build commit/source hashes
alongside the reports; the generated wrapper lives under `project/`.

**Successful tool completion is not timing sign-off.** Inspect the
`post_route_timing.rpt`, DRC, CDC, clock-interaction, methodology and I/O reports.
The routing completion token deliberately says `REVIEW_REPORTS`, not `PASS`.
Neither a checkpoint nor a zero tool exit status authorizes board loading.

## Preserved platform contract

- PS7 5.5, regenerated locally with pinned Vivado 2023.2; no imported 2025.1 BD.
- AXI3 GP0: 32-bit data / 12-bit ID, register aperture at `0x40000000`.
- AXI3 HP0 and HP1: 64-bit data / 6-bit ID, lower 512 MiB DDR aperture.
- Existing `red_pitaya_ps.v` port names, AXI clocks, resets and FCLK BUFGs.
  Disable the PS IP's extra FCLK buffers to avoid buffering the clocks twice.
- FCLK configuration 125/250/50/200 MHz; the fork's ADC-driven PLL is unchanged.
- One direct RTL XADC in `red_pitaya_ams.v`; no AXI XADC, GP1, HP2/HP3 or EMIO
  additions. The unused legacy GP1/converter/reset network is not reproduced.
- Original active package-pin/electrical settings and XADC logical ordering.
  Four trailing XDC comments are removed because Vivado treated them as extra
  Tcl arguments. The original constraints file is not edited.
- Legacy MIO and 16-bit DDR settings, not a new boot/FSBL configuration. Do not
  use generated PS initialization files to replace the board's boot files.

The official pinned
[Z20_G2 target](https://github.com/RedPitaya/RedPitaya-FPGA/blob/728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674/red_pitaya_vivado_Z20_G2.tcl)
also specifies a 16-bit DDR interface. RAM capacity and PL address aperture
are different questions: the retained 512 MiB aperture is not a claim to use
all of a Pro board's advertised RAM. Verify the actual board/boot configuration
before generating a deployable image or expanding memory access.

`board.xdc` retains the legacy 8 ns ADC clock and 3.4 ns input-delay assumption.
It omits legacy false paths referring to nonexistent clock names. It does not
invent DAC output delays, suppress DRC severity, or mask clock crossings.
External I/O timing and DNA-derived clock constraints still need analysis.

## Focused PID checkpoint and regressions

```powershell
& C:/Xilinx/Vivado/2023.2/bin/vivado.bat -mode batch -nojournal `
  -source pyrpl/fpga/targets/z20_gen2/synth_pid.tcl `
  -tclargs C:/path/to/a/new/pid-synthesis-directory
```

The standalone PID checkpoint remains useful for isolating control-path
changes. Run the real XSim contract in `../../sim/` as well. Source-preservation
guards (not hardware verification) run without Vivado:

```powershell
uv run --extra test python -m unittest tests.test_z7020_build_contract
```

Still required before a full image:

1. Validate exact board constraints, clocks/resets and DDR boot assumptions.
2. Simulate bus transactions, the complete fork datapath and top-level triggers.
3. Resolve full-design CDC/DRC and setup/hold timing findings without silently
   changing feedback latency. Tool completion alone is not that gate.
4. Produce separately named BIN/DTBO artifacts with source/toolchain/hash
   provenance, then implement their paired loader selection and regressions.

The runtime loader continues to reject Z7020. Keep the original Z7010 artifacts
unchanged. Hardware tests and any compatibility-main promotion remain deferred.
