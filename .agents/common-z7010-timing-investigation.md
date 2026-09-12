# Original Gen 1 / Z7010 / OS 1 timing investigation

## Scope and checkpoint — 2026-09-12

The user requested committing the common implementation fixes, then
investigating timing. Commit `43a9764` contains the filter shift-port repair,
explicit PID pause nets and their offline regressions. No device/OS root or
`develop` was merged or advanced. The user then explicitly confirmed that
the original Gen 1 / Z7010 / OS 1 configuration is the repair baseline;
subsequent device/OS adaptation belongs to the corresponding upgrade.

This investigation has not changed RTL, XDC, clocks, build settings or images
after that commit. No physical device was contacted. The local notebook is
not part of the commit and remains byte-identical to the user's saved file.

## Evidence hierarchy

1. Original repository reports under `pyrpl/fpga/out/` describe a full routed
   `red_pitaya_top`, `7z010-clg400`, speed grade -1, from Vivado **2015.4**,
   timestamp **2025-08-21 19:51:11**. They establish that an original Z7010
   build already had timing findings, before this upgrade work.
2. They are **not proven to describe the preserved shipped BIN**. Commit
   `61295d9` (2025-09-03) updates only `pyrpl/fpga/red_pitaya.bin`, not those
   reports. The historical report cannot establish that BIN's timing or
   explain/contradict its observed field performance.
3. The previous common PID-only Z7010 synthesis used Vivado 2023.2 and an
   8 ns ideal input clock. It excludes surrounding routing, PS/register bus,
   ADC I/O timing, placement and full-board clock insertion. Its positive
   estimate is not in conflict with negative full-design timing and is not
   a full-system baseline.
4. The earlier Z7020 routed checkpoint remains a separate port finding. A
   read-only query started before the user's clarification completed without
   changing it. Its measurements must not be used as the Z7010 repair target.

## What the original Z7010 reports actually show

Source: `pyrpl/fpga/out/post_route_timing_summary.rpt` and the 100-path
`post_route_timing.rpt`. These numbers belong to the historical build above.

| Finding | Evidence | Interpretation / next check |
| --- | --- | --- |
| 125 MHz DSP setup | 8,089 failing endpoints, worst slack -4.094 ns | Existing full-design datapath/integration finding, not merely an OS/Pro port symptom. |
| Worst setup path | IQ two-output LPF `delta_reg[22]` to modulator `secondproduct1/D[8]` | Trace/filter the exact IQ path before considering PID arithmetic changes. |
| ADC input hold | All 28 input paths fail; worst -2.163 ns | Audit external converter/clock/PCB timing and the inherited input constraint. Not a PID computation delay. |
| PWM setup | Four endpoints, worst -0.203 ns at 250 MHz | Separate PWM compare/output path, not the main PI loop. |
| Incomplete constraints | One no-clock finding, two unconstrained internal endpoints, 16 inputs and 46 outputs without delays | Scope/derive missing constraints; do not suppress findings. |

### Dominant IQ path is not only a setting-update path

The detailed worst path starts at the first LPF stage's **data state**:

`iqfilter[1]/genblk2[0].lpf/delta_reg[22]`

It passes through four LPF output-select LUTs, a combinational DSP multiply,
and saturation LUTs before reaching the next DSP input register. The report
gives **10.423 ns** of datapath delay: **5.041 ns logic + 5.382 ns routing**,
seven logic levels. The required clock period is 8 ns; clock paths and the
destination setup requirement also enter the reported -4.094 ns slack.

This matches the source structure: `red_pitaya_filter_block.v` chains stage
outputs combinationally; each LPF selects bypass/LPF/HPF output without an
extra output register; `red_pitaya_iq_modulator_block.v` then feeds
`red_pitaya_product_sat` before its first buffering stage. The source has
existing register boundaries; the report is not evidence of two completely
unregistered multiplication stages.

Other top-100 paths start at `quadrature_filter_reg[7]`, the filter-enable
control. Both data and control paths therefore require assessment. Declaring
all configuration paths false would neither solve the data path nor preserve
the supported behavior of live register updates.

### PID and bus integration must be separated

The historical top-100 list includes:

- PS bus `wr_wdata_reg[10]` to PID `ki_mult0/A[10]`: -3.396 ns;
- PS bus `wr_wdata_reg[10]` to PID `set_filter_reg[10]`: -3.331 ns;
- ADC data registers to PID multiplier input pins elsewhere in that list.

These show integration paths reaching PID, not proof that every violation
originates in the PI recurrence. Synthesis can absorb registers into DSP
input stages, so a DSP endpoint pin must be interpreted together with its
actual register configuration, not its name alone. Only 100 paths were saved;
this list cannot establish a complete endpoint distribution.

### ADC hold and DNA are constraint/model work first

The original XDC applies one `set_input_delay ... 3.400` to ADC inputs without
distinct early/late values. The worst hold report combines that 3.400 ns
input delay and 0.805 ns input path with approximately 6.011 ns clock skew.
This is a specific timing-model result. Changing the delay until the report
turns green would not establish real-board timing. Derive converter data-valid
min/max and relative board-clock delay before changing capture constraints.

The DNA clock comes from `dna_clk <= dna_cnt[2]` in `red_pitaya_hk.v` and feeds
`DNA_PORT.CLK`; the counter later stops. The historical report already marks
the clock-related unconstrained pins. Its divided-clock waveform/phase and
read/shift relationship need explicit validation/constraints; this is not an
excuse to add a blanket false path.

## Reproduction status and ordered next work

The installed tool inventory contains Vivado **2023.2 only**. The original
`ip/system_bd.tcl` explicitly requires **2015.4**. No old full-design DCP was
found in the local FPGA tree. The original top-level build also generates
and overwrites the preserved image/output tree, so it was **not executed**.

1. Establish a report/checkpoint-only **Z7010 full-top** build in a new output
   directory. Keep the original RTL/PS/pin/clock contracts and document any
   toolchain-only changes needed for 2023.2. Do not import the Pro PS shell
   (which has separate platform choices) as if it were the original build.
   A modern-tool recreation must be labelled as such, not an exact replay of
   the author's 2015.4 implementation or evidence about the old BIN.
2. Capture setup/hold paths grouped by data/control/bus, including actual
   DSP-register mapping. Separate the IQ mux/multiply/saturation bottleneck,
   PID input/bus paths, PWM path and external timing constraints.
3. Test cycle/bit-preserving alternatives before any implementation change:
   e.g. combinational bypass-selection restructuring and placement/fanout
   improvements. These are investigation candidates, not demonstrated fixes.
   Preserve every filter mode, register interface and feedback latency.
4. Re-run full Z7010 placement/routing and explicit functional regressions.
   Keep unresolved external timing-model/CDC findings visible. No automatic
   image generation or compatibility-main promotion follows from tool success.
5. Only after the common baseline work is validated, and only on explicit
   merge instruction, propagate common changes. Then assess OS2/Gen2/Z7020
   differences on their own upgrade branches.

## Retained secondary query (not the baseline)

`.agents/inspect_shared_timing.tcl` is read-only: it opens an existing DCP,
emits grouped setup/hold paths and PID/integration detail, and closes it.
It does not change constraints, route the design or write a checkpoint/image.
The query of the earlier Z7020 DCP completed at local
`TEMP/common-timing-43a9764` (adjacent `.log`). The input DCP SHA-256 is
`e54465fafbda6b957009ef4f05961f317a079dc406241c750b493ec76f14a864`;
its source is the prior Pro build, **not** current common commit `43a9764`.
The output directory's name identifies this investigation, not DCP provenance.
It enumerated 6,802 negative setup paths and 28 negative hold paths with one
worst path per endpoint and a 20,000 cap that was not hit. All counts and
slacks remain secondary port evidence; none is a Z7010 baseline measurement.
