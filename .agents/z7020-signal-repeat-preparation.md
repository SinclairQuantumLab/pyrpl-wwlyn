# Pro OS 2: repeat the Gen 1 signal experiment

Prepared after the user's Gen 1 run on 2026-09-15. Its reviewed field record
is committed on `gen1-os2/main` at `8c6f4df`, path
`.agents/gen1-os2-signal-field-result-20260915.md`. No common repair was merged.

The complete Gen 1 notebook was backed up byte-for-byte before preparing the
Pro copy: `.agents/local-notebooks/test-gen1-os2-signals-20260915.ipynb`, SHA-256
`400175e08399579287d9a6c6acd2f81cacfdac2340f1554b8f3ed00bac604ccb`.
Its user-entered factory-default password is preserved locally, as requested.

The target remains `gen2-pro-os2/feature/device-upgrade`, original-logic image
checkpoint `779a031`; profile 22 / `z20_125_v2` / Z7020. No RTL, loader, BIN,
DTBO, clock, driver normalization or library calibration changes are made for
this notebook update. Known original-source simulation/timing findings remain.

## Repeated procedure

The notebook retains separate preflight / programming / connection steps and
then replaces the earlier broad bench checklist with the user's focused tests:

1. PID0 DC source on OUT1, PID1 read-only IN1 monitor; commands
   `[-0.5, -0.25, 0, 0.25, 0.5]`.
2. Capture paired RP output / IN1 / Rigol readings and fit OUT1 and IN1
   separately. Never copy the Gen 1 board's four calibration coefficients.
3. ASG0 triangle at amplitude 0.4, **1 Hz and 1 kHz**. The user clarified that
   both worked on Gen 1. The saved code/plot documents 1 Hz; 1 kHz success is
   user-reported. Use hardware-buffered scope acquisition for the 1 kHz run,
   then restore 1 Hz for the saved PID-disturbance condition.
4. Capture 5,000 polled input readings and elapsed times, plot and record the
   Rigol observations. SSH/sleep is not treated as an exact sampling clock.
5. P=0, I=-150000, physical target 0.5 V using the newly measured IN1 fit.
   Keep ASG0 routed as a summed disturbance, matching the saved Gen 1 state;
   distinguish calculated setpoint from external response/measurement.
6. Turn off direct outputs, explicitly skip missing modules. Reconnect is
   optional and not another FPGA load.

The local copy targets the previously identified Pro board at `192.168.50.175`.
The tracked template stays free of device addresses, passwords and outputs.
Termination/jumper/instrument details and measurements must be recorded for
the new board; its analog full scale is not assumed identical to Gen 1.

## Preserved Gen 1 dependency edits

Before switching, only the unstaged Gen 1 `pyproject.toml` / `uv.lock` changes
were stashed as `Gen1 OS2 local ipykernel dependency state before Pro signal
test`, object `f01b7ed520bfd54dfc75a2faf8cca9e6bc314624`. This stash was not
dropped or applied to another branch. Pro already contains the ipykernel
runtime dependency and exactly the same lockfile via `0ec5cc2`; its additional
packaging declarations are retained. The saved Gen 1 state remains recoverable.

No notebook cell was executed and no device was contacted during preparation.

## Offline validation

Full agent validation passed at local `TEMP/pyrpl-two-frequency-15cfb474`:
73 checkout unittests, 25 Nose tests, all 119 Python files compiled, 155-entry
wheel inspection, fresh Python 3.14 installation and dependency checks. The
fresh 73-test suite passed with one expected checkout-only ignore-policy skip.
The new pure/mocked tests cover separate IN/OUT calibration, invalid data,
DC-output cleanup after interrupted input, both triangle frequencies and the
1 kHz hardware-scope path. They do not execute real device cells.

Local-notebook syntax/clean-state checks passed; the user's password assignment
matches the Gen 1 notebook, the hostname is the Pro target, and no Gen 1 fit
coefficients were copied. Original RTL and every FPGA asset remain unchanged.
