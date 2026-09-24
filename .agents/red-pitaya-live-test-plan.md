# Red Pitaya live-test plan

Candidate summary updated 2026-09-15. The detailed standard Z7010 Gen 2
checklist below remains separate from the focused Pro signal repeat in
`z7020-signal-repeat-preparation.md`. This is not permission for an agent to
contact or program a board.

## Current candidates and historical checkpoints

| Target | Branch / historical commit | Evidence and next step |
| --- | --- | --- |
| Author-board Python 3.9 baseline | `407a9d1`, original Z7010, OS 1.04-18 | Field-tested comparison point; no OS downgrade is required for this work |
| Python 3.14 implementation | `c535358` | Historical Python upgrade checkpoint, not the current OS 2 test checkout |
| Original-board OS 2 | `gen1-os2/main`, signal results recorded at `8c6f4df` | Loading/connection, DC notes, triangle trace and PID setup recorded; user reports both 1 Hz and 1 kHz passing; see `gen1-os2-signal-field-result-20260915.md` for scope |
| Standard Gen 2, OS 2 | `gen2-os2/feature/device-upgrade`, checkpoint `3fc4307` | Offline readiness committed; user deferred loader, functional, and analog field measurements |
| Pro / Z7020 | `gen2-pro-os2/feature/device-upgrade`, original-logic image `779a031` | Loading, connection and PID metadata reads passed; focused Gen 1 signal repeat prepared; timing remains unclosed |

Implementation commits `10f0e68`, `7aa600e`, `ddb1077`, and `80b6291`
are historical references. They predate fixes found during the original-board
OS 2 field test. Do not check them out as the current test candidate.

Record the actual tested commit and any working-tree differences at each
session. A new worktree is optional, not a required extra copy of the project.
Do not overwrite another worker's files or switch a dirty checkout blindly.
Later evidence belongs in a new commit; do not rewrite previous validation.

## Prepare the local environment and notebook

Run `uv sync --extra test` and the offline commands in `AGENTS.md` on the
candidate. Copy `test.ipynb.template` to `test.ipynb` only if the local
notebook does not already exist. Otherwise transfer the desired new cells
without replacing saved experiments. The template is tracked; the local
notebook and its device-specific results are ignored.

Use the notebook's brief Markdown explanations and run one step at a time:

1. Set the hostname and confirm that the intended checkout supplies PyRPL.
2. Run read-only preflight. This opens SSH but does not program the FPGA.
3. Program the FPGA in its own cell.
4. Connect the monitor server/PyRPL in a separate cell.
5. Read the fork register metadata, then proceed to the bench measurements.

The packaged alternative to step 2 is
`uv run python -m pyrpl.redpitaya_preflight HOSTNAME`. User-run acceptance
steps belong in the notebook, not in agent-only live scripts.

Before loading, identify the actual board and wiring. The active target is
standard STEMlab 125-14 Gen 2, Z7010, profile 20 or 31, path `z10_125_v2`,
OS major 2 release 2.07 or later. Record the ecosystem release, profile,
installed overlay contract, candidate revision, Python version, local asset
hashes, cabling, termination, and measurement equipment. Keep passwords out of
the tracked template/records; the user permits factory-default credentials in
their ignored local development notebook.

Keep experimental actuators disconnected and begin with a passive loopback
or dummy load. The template clears direct fast-output routes before driving
its selected output. Connecting PyRPL can apply saved configuration; it is
not a read-only operation even when FPGA reload is disabled.

## Loader and connection acceptance

The preflight must identify one of the installed overlay's supported fixed
basenames, `fpga.bit.bin` or `fpga.bin`. It selects the corresponding
approved DTBO, not an overlay chosen from an OS build-number exception.

A successful load and connection requires:

- approved original BIN and matching DTBO hashes before upload;
- successful overlay command and FPGA Manager state `operating`;
- expected image identity in `/tmp/loaded_fpga.inf` and retained loader logs;
- monitor connection and positive register metadata;
- disconnect/reconnect without FPGA reprogramming.

The source contract additionally expects PID PSR/ISR/gain width 12/32/30.
Positive generic register metadata alone is not an analog or fork-feature
measurement. Preserve diagnostics after failure; do not substitute another
bitstream, bypass refusal, or automatically retry programming.

An installed `fpga.bin` contract needs its own live evidence when a device
with that contract is available. Do not edit a board's `overlay.sh` just to
manufacture another test configuration.

## Functional measurements

The expanded template provides a starting bench sequence:

| Notebook step | What to observe |
| --- | --- |
| ASG and ADC loopback | Low-amplitude 1 kHz tone; measure frequency, amplitude, offset, polarity, and ADC scale |
| Internal scope / FFT | Compare the ADC trace with the internal ASG reference; the local FFT is not a PyRPL spectrum-analyzer test |
| Proportional / hold / integrator | Internal PID routing, retained output during pause, release, saturation and recovery |
| 16-step sequence | Signed values, indices 0 through 15, manual advance, and wrap readback |
| External TTL | PID0 hold on DIO0_P and sequence advance on DIO3_P; common ground and 3.3 V logic |
| Slow inputs | Read the fork's direct-XADC channels; this does not exercise slow outputs |
| Cleanup and reconnect | End acquisition, clear test output routes, and reconnect without another FPGA load |

Repeat fast-I/O measurements on both used channels and record whether the load
is high impedance or 50 ohms. Gen 2 nominal output full scale differs with
load (+/-2 V high impedance, +/-1 V into 50 ohms). Do not silently change
PyRPL normalization to compensate for an unmeasured load.

Additional measurements are still needed for the intended application:

- calibrated ADC/DAC amplitude and offset over the operating range;
- PyRPL spectrum-analyzer operation, separately from the local FFT;
- the used filters and a passive/dummy-plant closed loop, including sign,
  latency, saturation, recovery, and stability;
- external TTL polarity, edge timing, hold transient, and maximum intended
  sequence rate (a manual software pulse does not measure these);
- used slow outputs, with correct PWM routing and measured voltage;
- GUI/qasync and a fresh ipykernel connect/close cycle without reprogramming;
- at least 30 minutes of operation, followed by reconnect, logging exceptions,
  disconnects and drift.

Compare the fork-specific behavior with the existing original-board reference
where measurements are available. Do not claim equivalence solely from source
inspection, a loader pass, or absence of Python exceptions.

## Record results and promotion

Save device-specific raw outputs in the local notebook or other local logs.
Add a sanitized summary, tested revision, hashes, setup, measurements and
remaining limitations to `.agents/red-pitaya-gen2-upgrade-changelog.md` in
a new evidence commit.

Do not advance/create `gen2-os2/main` from this offline readiness work.
Promotion follows the agreed field results. This does not reopen or undo the
user's existing `gen1-os2/main` promotion.
