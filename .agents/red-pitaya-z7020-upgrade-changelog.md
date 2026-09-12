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
