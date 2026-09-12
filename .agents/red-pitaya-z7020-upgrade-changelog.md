# Z7020 Gen 2 Pro / OS 2 implementation

## Scope and starting point — 2026-09-12

The user requested committing standard Gen 2 readiness, deferring physical
tests, and proceeding to Gen 2 Pro / OS 2. In the context of the preceding
assessment this means the Z7020 Pro target, not merely the existing Z7010 Pro
profile rows.

- `3fc4307`: standard Z7010 Gen 2 offline checkpoint; field tests deferred.
- `cd4bd73`: merge that checkpoint into the existing
  `gen2-pro-os2/feature/device-upgrade` branch without rewriting either history.
- No compatibility main is promoted. The existing packaged BIN/DTBOs and
  ignored user notebook remain unchanged. The loader still rejects Z7020.

The first Pro implementation milestone establishes actual RTL simulation and
a Z7020 module-level synthesis target. It is not a completed board port.

## Source defects reproduced before correction

The new self-checking testbench compiles the real PID/filter/LPF files, not a
replacement behavioral module. XSim 2023.2 first rejected `int_shr` being
referenced by the register bus before its declaration. Moving its declaration
and the unchanged `IBW = ISR+14` constant ahead of the bus fixed compilation.

Simulation then failed 27 of the initial 282 checks: every checked PID output
was X while register/sequence checks passed. With the default DERIVATIVE=0,
the generate branch declared a local `kd_reg_s`; its zero assignment did not
drive the same-named outer signal used by `pid_sum`.

The Pro branch changes the outer signal to a net and removes the disabled
branch's shadow declaration, connecting that zero to the sum. It does not add
a pipeline stage, change fixed-point width, gain, saturation or trigger logic.
DERIVATIVE=1 was already documented as non-functional and remains outside this
milestone; this is not a claim to have implemented/validated the D path.

This proves defects in the checked-in RTL under the tested tools, not defects
in the historical field-tested BIN. Their exact build correspondence is
unknown. The Z7010 BIN was not regenerated or overwritten.

History verification: the PID RTL at original baseline `387faf3` and at the
pre-port merge `cd4bd73` has the identical Git blob
`d293ac95b80503311d04d1dcaaa19321b3ef1e02`. The shadowed signal was therefore
already present before the upgrade, not introduced by the port. Its default
PI correction is in `6e76d87`.

## Implemented development infrastructure

- `pyrpl/fpga/sim/tb_pid_contract.sv`: default PI register contract, positive/
  negative P output and clipping, held P, I accumulation/hold/release/saturation,
  signed 16-slot sequence, reset/index/wrap, differential input and cycle-level
  checks. No internal signal is forced.
- `sim/run_pid_contract.py`: standalone xvlog/xelab/xsim runner, optional tool
  path, fresh retained output directories, source SHA-256 manifest, console
  transcripts and explicit pass-token validation. XSim returned zero even for
  the failing `$fatal`; the runner correctly treated that run as failed.
- `targets/z20_gen2/synth_pid.tcl`: explicit source list and
  `xc7z020clg400-1` target, Vivado 2023.2 module-level synthesis, checkpoint and
  reports. It cannot emit a BIN/DTBO and does not use the destructive legacy
  Makefile targets or write into their output tree.
- Agent-only installed-part/IP inventory stays in `.agents/`. Simulation and
  target sources are included in the source archive and excluded from the
  runtime wheel. The retained notebook is clearly labelled a Z7010 reference,
  not an available Z7020 loading procedure.

## Offline evidence

Vivado 2023.2 build 4029153 executed locally. Inventory found the Z7020 part,
processing_system7 5.5, axi_interconnect 1.7/2.1 and proc_sys_reset 5.0. The
synthesis license for Z7020 was successfully checked out and released.

- Expanded real-RTL simulation: **341 checks passed**. This includes the
  four-clock P/bypass output latency and three-sampled-clock sequence advance,
  held-high/no-falling-edge behavior, and signed integrator endpoints.
- Z7020 PID out-of-context synthesis: **0 errors, 0 critical warnings,
  57 warnings**; 835 LUTs, 545 flip-flops, 4 DSP48E1s, no black boxes.
- Post-synthesis timing estimate with an 8 ns clock: WNS +0.452 ns,
  worst hold slack +0.186 ns. There is no placement/routing, top-level clock
  source or I/O delay constraint; these numbers are NOT timing closure or
  a full-design frequency claim.
- Warnings include legacy generate syntax, implicit pause nets, an LPF shift
  port-width mismatch, unused register bits, and missing out-of-context clock
  source information. The Windows tool also printed a nonfatal path message;
  the script completed and generated its checkpoint and both reports.
- Python 3.14 offline unittests: 53 passed, including the real ipykernel;
  Nose NG safe subset: 24 passed (overlaps some unittest cases).
- Plain `uv sync --extra test` passed; 115 Python files compiled with
  SyntaxWarning treated as an error. No dependency/lockfile change was needed.
- The source archive and its 153-entry wheel built successfully. A fresh
  Python 3.14.4 wheel installation passed `uv pip check` and all 53 unittests,
  including an actual ipykernel, from outside the checkout. Wheel inspection
  verified the original BIN, exactly two approved DTBOs, both byte-identical
  DTS sources and preflight module. Simulation/target sources were present
  only in the source archive, and the local notebook was excluded.
- `git diff --check` passed. Original BIN/DTBO and local notebook SHA-256
  values remained unchanged; no device/OS main branch advanced.

## Remaining work

1. Reproduce/adapt the full PS/AXI wrapper for a pinned Z7020 platform while
   retaining the direct XADC, register map and HP0/HP1 contract. The official
   2025.1 block design is a reference, not a validated 2023.2 import.
2. Check the exact board pin/clock/reset/DDR assumptions and simulate the
   complete datapath, enabled filters and top-level DIO/software triggers.
3. Synthesize/place/route the full design; resolve timing and CDC/DRC findings
   without silently changing feedback latency.
4. Generate separately named, provenance-recorded Z7020 BIN/DTBO artifacts,
   then add their exact loader selection and offline tests.
5. Perform the deferred hardware/analog/control acceptance when the device is
   available. No board was contacted during this milestone.

## Full PS/AXI integration milestone — 2026-09-12

Following the user's authorization to continue, a separate Vivado 2023.2
PS shell and full-fork build were implemented on top of `6e76d87`. No further
RTL, Python runtime, loader, notebook or packaged FPGA asset changes were made
in this milestone.

### Implementation and preserved behavior

- `targets/z20_gen2/ps_config.tcl` derives its explicit PS settings from the
  author's `ip/system_bd.tcl`. Legacy MIO/DDR settings remain unchanged. GP1
  and its abandoned AXI-XADC/interrupt path are disabled; GP0 and HP0/HP1 remain.
- `system_bd.tcl` regenerates PS7 5.5, external AXI3 interfaces and the existing
  wrapper port names. It validates actual generated bus metadata: GP0 data/ID
  widths 32/12 and HP0/HP1 widths 64/6. Full synthesis successfully connects
  this generated wrapper to the unmodified `red_pitaya_ps.v`.
- Register aperture starts at `0x40000000`; both HP DDR apertures retain the
  lower 512 MiB. FCLK settings are 125/250/50/200 MHz. Extra PS-IP FCLK BUFGs
  are disabled because `red_pitaya_ps.v` already supplies them. The fork's
  ADC PLL and reset circuitry are unchanged.
- The only BD IP is PS7; the full synthesized netlist has exactly one direct
  XADC primitive and no black boxes. No official AXI XADC is imported.
- `board.xdc` preserves all active author package-pin/electrical settings.
  Four invalid trailing Tcl comments are removed in this target copy, not
  the legacy file. Stale false paths naming nonexistent clocks are omitted.
  The 8 ns ADC clock and legacy 3.4 ns ADC input-delay assumption remain.
- `build.tcl` pins the tool/part, explicitly lists the 29 original RTL sources,
  generates the wrapper, and provides BD/synthesis/implementation stages in
  new output directories. It emits checkpoints/reports, never BIN/DTBO/FSBL
  boot images. Generated PS initialization files are not for board deployment.
- Six source-preservation regressions check the exact documented PS delta,
  unchanged active I/O settings, valid local source list, target/tool contract,
  and absence of image generation and timing/severity waivers.

The pinned official
[Z20_G2 build](https://github.com/RedPitaya/RedPitaya-FPGA/blob/728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674/red_pitaya_vivado_Z20_G2.tcl)
also explicitly uses a 16-bit DDR interface. This does not validate the exact
Pro board's boot DDR configuration or expose its full advertised RAM capacity.
Those remain separate checks; no boot/OS files were changed.

### Actual build evidence

Final build outputs remain in local Windows `TEMP/z20-ce2f7712` with its
adjacent `.log`; source and report hashes, commands, tool and numerical
results are recorded in `.agents/z7020-full-build-evidence.json`.

- PS shell generation/validation, full RTL synthesis, optimization, placement
  and routing completed with exit code 0 on `xc7z020clg400-1`.
- Synthesis log: 315 warnings, **0 critical warnings, 0 errors**. Historical
  RTL warnings remain (forward declarations, generate syntax, width truncation,
  unused bits, and implicit nets). These have not all been functionally audited.
- Final routed design: 13,814 LUTs, 10,434 flip-flops, 34 BRAM tiles,
  36 DSP48s, one PS7 and one direct XADC. Resource capacity is not the blocker.
- **Timing did not close:** setup WNS **-4.369 ns**, TNS -5205.906 ns,
  6,802 failing endpoints; hold WHS **-2.362 ns**, 28 failing endpoints.
- 6,798 setup-failing endpoints are in the 125 MHz ADC/DSP domain; the worst
  reported path is the two-output IQ quadrature filter control to
  `modulator/secondproduct1/D[4]`, with a 10.703 ns datapath. Four additional
  setup endpoints fail in the 250 MHz PWM domain (WNS -0.356 ns).
- All 28 hold failures are ADC input paths under the retained legacy delay
  constraint. This is not a measured ADC/PCB timing model: min/max delay,
  clock relationship and board revision must be derived, not guessed.
- Default DRC reports 133 warnings, no errors. Separately, methodology reports
  **one critical TIMING-17 finding**: the DNA_PORT clock lacks a generated-clock
  constraint. A log with zero critical warnings is NOT an overall clean result.
  It also flags missing I/O delays, identical min/max ADC delays and four
  inherited overlapping PWM IOSTANDARD assignments.
- `check_timing` reports one unclocked sequential pin, two unconstrained
  internal endpoints, 16 inputs without input delay and 46 outputs without
  output delay. CDC classifies its 150 analyzed endpoints as safely timed,
  but excludes unclocked paths/unconstrained inputs. It does not prove external
  TTL/reset safety or override the setup/hold failures.

The initial exploratory build exposed read-only GP0 ID-width assignment and
four XDC-comment errors; these were corrected before the final fresh build.
The resulting timing failures were retained, not suppressed with false paths,
multicycle exceptions, lowered clock frequencies or severity overrides.

### Regressions and packaging

- Real PID XSim contract: 341 checks passed again; artifacts at local
  `TEMP/pyrpl-pid-rtl-phoa__8e`. This is behavioral simulation of the PID/filter
  RTL, not full-top or post-route timing simulation.
- Checkout unittests: 59 passed (previous 53 plus six source guards).
  Nose NG safe subset: 24 passed; overlaps some unittest cases.
- `uv sync --extra test` passed without lock-bypass flags; no metadata,
  dependency or lockfile changes. All 116 project Python files compiled with
  SyntaxWarning treated as an error.
- A fresh Python 3.14.4 environment installed the newly built 153-entry wheel
  and passed dependency checks. From outside the checkout, the 59-test suite
  passed with one expected skip (checkout-only Git-ignore policy). Package
  imports and the real ipykernel used the fresh installation; source guards
  used the extracted source archive.
- Wheel inspection verified exact original BIN, exactly the two approved
  DTBOs, byte-identical DTS sources and the packaged preflight module. Target
  and simulation sources are in the source archive, not the runtime wheel.
- Original BIN/DTBO hashes and the ignored local notebook hash are unchanged.
  No board was contacted and no compatibility main was advanced.

### Next implementation work

The PS/AXI regeneration and full build are now reproducible; the former
milestone's first build gate is complete, **not** the entire Z7020 port.

1. Characterize enabled/cascaded filters, IQ control updates and bus transactions
   in simulation. Optimize measured critical paths with cycle/bit-accurate
   equivalence checks before considering any latency-changing pipeline work.
2. Derive ADC min/max I/O constraints from the exact converter/clock/board,
   constrain the DNA divider, and review DIO, reset crossings and DAC/PWM I/O.
3. Repeat full implementation and close timing/CDC/methodology findings.
4. Only after those repo-side gates, derive separately named Z7020 BIN/DTBO
   artifacts and their matching loader/provenance regressions. The current
   loader continues to reject Z7020; physical acceptance remains deferred.
