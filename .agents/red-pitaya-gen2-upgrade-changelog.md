# Z7010 Gen 2 repository upgrade

Candidate branches: `gen2-os2/feature/device-upgrade` and
`gen2-pro-os2/feature/device-upgrade` (originally developed on
`develop/red-pitaya-upgrade`)

Original implementation commit: `80b6291199dfb7a7d784e4c0d355c5905735621f`.
It predates the corrected preflight probes and native uv packaging; do not
check it out as the current live-test candidate. Continue from the standard
candidate branch and record the tested revision as described in
`.agents/red-pitaya-live-test-plan.md`.

This upgrade is repository-side only. It did not contact, restart, or program
a Red Pitaya and did not modify or rebuild the fork bitstream or either DTBO.

## Implemented scope

The OS 2.07+ loader recognizes these exact profile ID, FPGA path, and Zynq
combinations:

| Profile IDs | FPGA path | Target |
| --- | --- | --- |
| 1, 2 | `z10_125` | Original STEMlab 125-14 Z7010 |
| 20, 31 | `z10_125_v2` | Standard STEMlab 125-14 Gen 2 Z7010 |
| 21, 32 | `z10_125_pro_v2` | Pro STEMlab 125-14 Gen 2 Z7010 |

A mismatched ID/path pair, Z7020, early OS 2, OS 3, or an unrecognized loader
contract still fails before upload or board mutation. The preflight JSON now
includes the model, generation, variant, documented high-impedance DAC full
scale, and field-validation state.

## Why the FPGA artifacts are unchanged

At Red Pitaya ecosystem commit
`0e46d64396a57752bf97315789d6cc6c9fbddad8`, `Makefile.x86` maps the original,
standard Gen 2, and Pro Gen 2 Z7010 asset families to the same
`FPGA_MODEL = Z10`. At RedPitaya-FPGA commit
`728a4f37e9c0a9b5ba1d9b7a0d44c38bbd2dc674`, that model uses one Z10 project
and one package-pin constraint set. Red Pitaya's published Gen 2 development
schematic independently confirms the Z7010 part and relevant converter, GPIO,
PWM, XADC, and serial-link package pins.

This supports reusing the fork's exact Z7010 programmable-logic image and its
already derived OS 2 overlay. It does not justify substituting an official
PyRPL artifact or rebuilding the fork image.

## Analog behavior boundary

Red Pitaya documents the Gen 2 DAC as +/-2 V full scale into high impedance and
+/-1 V into 50 ohms. The software cannot determine the attached load. The
upgrade therefore preserves PyRPL's original register normalization and emits
a warning for Gen 2 rather than applying an ambiguous factor-of-two correction.

Before using a closed loop on Gen 2, measure ASG output amplitude and offset
with the actual load, verify ADC and slow-analog scaling, and then test scope,
spectrum analyzer, PID, and the fork-specific triggered setpoint sequence.

## Remaining acceptance gate

Static compatibility and offline loader behavior are covered. Hardware support
must still be described as field-validation pending until an explicitly
authorized controlled test verifies overlay success, FPGA Manager state,
monitor connection, fork register signatures, analog scale, and the intended
control functions on the exact Gen 2 board.

## Offline validation

Validated with CPython 3.14.4 without contacting a board:

- `python -m unittest pyrpl.test.test_redpitaya_fpga_loader`: 25 passed;
- Python 3.14 and real-ipykernel compatibility unittests: 9 passed;
- selected Nose NG memory, proxy, Python 3.9 regression, and Python 3.14
  regression tests: 17 passed;
- forced `compileall`: passed;
- `pip check`: no broken requirements;
- wheel build, fresh-environment install, and the installed copy of all 25
  loader tests: passed;
- wheel inspection found exactly the two authorized DTBOs and the packaged
  preflight module; and
- the fork BIN and both DTBO SHA-256 values remained exactly those recorded in
  `AGENTS.md`.

## OS 2 preflight corrections propagated

The original-generation board exposed three preflight defects in the shared
OS 2 loader: shell completion markers, interactive SSH timeout, and the Zynq
profile query. The four corrective commits were selectively backported with
`git cherry-pick -x` to this Gen 2 candidate. The Gen 2 profile/path gates
remain unchanged. All 26 fake-SSH loader regressions pass on CPython 3.14.4;
no Gen 2 device was contacted or programmed. The hardware gate above remains
open.

The clean `test.ipynb.template` separates the future user's preflight,
programming, server connection, and initial register read. It has not been run
against a Gen 2 device and does not change the field-validation state.

## Standard Gen 2 readiness (2026-09-12)

This iteration starts from `143ef23` on
`gen2-os2/feature/device-upgrade` and targets the standard Z7010 board only.
The Pro candidate is not advanced. A separately requested Z7020 feasibility
assessment is read-only and does not authorize a port or a new FPGA image.

- New regressions exposed permissive profile parsing: an ID such as
  `20invalid`, a path such as `z10_125_v2/other`, or Zynq text starting with
  `0` could be mistaken for an approved value. Duplicate fields also silently
  selected the last value. Parsing now requires one complete field per probe.
  There is no release/build-specific exception or change to the profile table.
- A source-derived profile fixture is independent of the response generator.
  A local POSIX-shell test also executes the actual command's `printf` and
  exit-status composition, including individual subcommand failures. Its
  stand-in executable is not presented as a real hardware profile tool.
- New PID regressions characterize the unchanged signed 14-bit sequence
  packing, 16-slot length, scalar/sequence rounding distinction, software
  trigger/reset addresses, signed readback, and gain/integrator bounds.
- The template now provides ASG/ADC measurement, internal proportional/hold/
  integrator tests, 16-step sequence/wrap readback, physical TTL observations,
  slow-input readings, cleanup, and reconnect steps. It keeps programming and
  server connection separate and introduces no confirmation-token cell.
- Template regressions check clean notebook structure, Python syntax, the
  separation of device operations, and the scope helper using synthetic data.
  The source distribution now includes the template alongside these tests.

The preserved RTL ties PID0/1/2 hold to DIO0_P/1_P/2_P and setpoint advance to
DIO3_P/4_P/5_P (`red_pitaya_dsp.v`, PID instances). PID gain width is 30 and
the sequence contains 16 signed 14-bit words (`red_pitaya_pid_block.v`). These
are source/API contracts, not new field measurements. Neither the BIN, either
DTBO, nor the PID/RTL implementation is changed by this readiness work.

Closed-loop behavior, physical TTL timing, slow outputs, long-duration/GUI
operation and Gen 2 analog scaling remain live measurements. The template's
local FFT is not a validation of PyRPL's spectrum-analyzer module. No Gen 2
device has been contacted or programmed during this work.

### Validation of this readiness iteration

On CPython 3.14.4, with offscreen Qt, temporary user directories and the fake
hostname:

- Plain `uv sync --extra test` succeeded; dependency declarations and
  `uv.lock` remained unchanged (only the source-archive include list changed).
- Loader unittests: 32 passed, including the locally executed POSIX-shell
  probe test; PID contract tests: 7 passed; template tests: 5 passed.
- Python 3.14 and real-ipykernel regressions: 9 passed.
- Selected Nose NG memory/proxy/Python 3.9/Python 3.14/PID regressions:
  24 passed. Some overlap the unittest run; these are not 24 additional
  distinct cases.
- All 114 tracked/unignored Python source files compiled, with SyntaxWarning
  promoted to an error.
- `uv build --no-sources` built the source archive and a wheel from it.
  The wheel contained 153 entries, including the exact original BIN, exactly
  the two approved DTBOs, byte-identical DTS sources, and the preflight module.
  The source archive contained the clean template and its regression test,
  but not the local `test.ipynb`.
- Installation of the wheel with its test extra into a fresh CPython 3.14.4
  environment passed `uv pip check`. All 32 installed loader tests and the
  21 Python/runtime/PID/template tests passed against that installed package
  from outside the checkout, including a real ipykernel.
- `git diff --check` passed. Original BIN/DTBO hashes and the ignored local
  notebook hash were unchanged. No compatibility main or Pro branch moved.

qasync still has the previously recorded Python 3.16 deprecation warning.
This does not fail the Python 3.14 tests. The local ipykernel test also emits
its TCP transport warning; it does not connect to a Red Pitaya.

The user-requested parallel assessment is recorded separately in
`red-pitaya-z7020-feasibility.md`. It changes neither this target's hardware
scope nor the preserved FPGA artifacts.

The user requested committing this offline checkpoint and deferring physical
Gen 2 testing to a later session. The pending measurements remain in
`red-pitaya-live-test-plan.md`; this checkpoint does not promote a Gen 2 main.
