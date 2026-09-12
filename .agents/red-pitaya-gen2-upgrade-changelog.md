# Z7010 Gen 2 repository upgrade

Candidate branches: `gen2-os2/feature/device-upgrade` and
`gen2-pro-os2/feature/device-upgrade` (originally developed on
`develop/red-pitaya-upgrade`)

Implementation commit: `80b6291199dfb7a7d784e4c0d355c5905735621f`.
Use that immutable candidate for the live-device gates recorded in
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
