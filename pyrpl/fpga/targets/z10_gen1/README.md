# Original Gen1 Z7010 repaired-source test candidate

This target rebuilds the common PID repair (`e747916`) for the original
STEMlab 125-14 / xc7z010clg400-1. It does not change the preserved author
`fpga/red_pitaya.bin`, RTL, clocks, latency, accepted mains or OS2 DTBOs.
The separately named candidate is for user bench tests on Gen1 OS1/OS2.
It is **not timing-closed or yet hardware-validated**.

## Build and export

Use Vivado 2023.2 and new output directories for each invocation:

```text
vivado -mode batch -source build.tcl -tclargs NEW_BUILD implement
vivado -mode batch -source export_repaired_test.tcl -tclargs NEW_BUILD/post_route.dcp NEW_EXPORT
```

Paths to the scripts must be resolved from this directory. Build only emits
reports/checkpoints. Export separately produces `red_pitaya_z10_gen1_repaired.bin`
using the author's uncompressed BIT / SMAPx32 / disablebitswap conversion.
No DRC severity changes, timing waivers or board operations are performed.
Inspect reports before packaging; merely running export does not update
the loader's approved hash or provenance evidence.

## Tool-version adaptations

The original 2015.4 `ip/system_bd.tcl` remains untouched. `system_bd.tcl`
derives its design instead of importing the Z7020 Pro PS shell:

- update the script version check and remove obsolete `PCW_IRQ_F2P_INTR`;
- match the external HP AXI ID widths to the existing six-bit RTL ports;
- remove a dangling clock reference to the already-commented AXI XADC;
- disable IP auto-BUFG insertion because `red_pitaya_ps.v` provides four BUFGs;
- annotate the external HP clock-to-bus association for BD validation.

The original DDR/MIO, GP1/converter/reset topology and address map are retained.
The unused GP1 path still raises a BD incomplete-address-path warning; it is
not a new peripheral. Synthesis has no black boxes and one direct XADC.
The original synthesis flags, `power_opt_design`, and implementation sequence
are retained. This is not a bit-equivalent recreation of the 2015.4 build.

`board.xdc` preserves all active pins, I/O properties, clock periods and input
delays. Four invalid trailing inline comments are stripped; six legacy false
paths referencing absent clock names are left as comments, not replaced with
new exceptions. The valid `clk_fpga_0` to `adc_clk` exception is retained.
The actual clocks and remaining timing/I/O findings are
recorded in `.agents/z7010-repaired-build-evidence.json`.

`repaired_rtl.json` pins every original RTL file to the approved common repair.
Run `tests.test_z7010_repaired` for preservation/notebook/artifact guards and
the real XSim contract under `fpga/sim` for behavioral regression evidence.
