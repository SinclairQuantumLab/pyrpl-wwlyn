# Z7020 original-logic baseline: first field result

Recorded 2026-09-15 (local America/Chicago); the board log timestamp for the
programming operation is 2026-09-16 00:56:46 UTC. The user executed the notebook
and reported success. The agent inspected saved outputs only, without executing
cells or contacting the board.

## Observed scope

Saved `test.ipynb` steps 1–5 (execution counts 2–6) contain no error output:

1. Project `.venv` and local PyRPL checkout selected the separately packaged
   `red_pitaya_z20_gen2_author.bit.bin`; wwlyn RTL `387faf3`, no common repairs.
2. Read-only preflight identified `192.168.50.175` as STEMlab 125-14-Z7020
   Pro v2.0, profile `22`, FPGA path `z20_125_v2`, Zynq `Z7020`, ecosystem OS
   reported by the loader as `2.07-3`. Installed overlay basename: `fpga.bit.bin`.
3. FPGA programming returned `PYRPL_OVERLAY_OK`; the FPGA Manager state was
   `operating`, and the update log reported successful BIN loading in 83 ms.
   `/tmp/loaded_fpga.inf` identified
   `pyrpl_/opt/pyrpl/fpga.bit.bin_/opt/pyrpl/fpga.dtbo`.
4. PyRPL connected and its fork register checks passed, without another FPGA load.
5. PID0 input filter read `[0, 0, 0]`; metadata read PSR=12, ISR=32, GAINBITS=30,
   sequence_index=0 and sequence_setpoint=0.0.

The remote load log's MD5 `ae92fa98ac14d240dc319e6f68f90341` matches the local
image. Preflight recorded its SHA-256 as
`f6728daaf863f6c48a1d8b27a7262d7fb7653c489f37db36acd6cbb9cc4a7307`, and the
selected overlay SHA-256 as
`41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9`.

This verifies the observed loading/connection/register-read path, not physical
signal fidelity, PID dynamics or the entire design. No later analog/oscilloscope
measurement results are present in this saved notebook. Build timing remains
unclosed and the untouched-source XSim declaration-order failure remains as
documented in [the build/test record](z7020-author-baseline-test.md). No common
repair or compatibility-main promotion is included in this checkpoint.

## Preserved local evidence

Before switching branches, the entire saved notebook was copied byte-for-byte
to `.agents/local-notebooks/test-gen2-pro-os2-author-baseline-20260915.ipynb`.
Verified SHA-256:
`dfe2247c1c1c8403d8053a9185f3611ce282dd33a1c75657163e6d3e3221cd0e`.

The notebook and backup remain ignored, not committed. This concise record
preserves the result without checking in device-specific notebook state or
credentials. The backup directory is also locally excluded so that changing
to an older compatibility branch cannot accidentally expose those notebooks.

## Commit-time validation

The separately requested dependency checkpoint is `0ec5cc2` (existing
`ipykernel>=7.3.0` addition and uv lock refresh). With that dependency state,
`.agents/validate_author_candidate.py` passed again; output is at local
`TEMP/pyrpl-author-final-25c69603`. Results: 119 Python files compiled, 70
checkout unittests, 25 Nose tests, 155-entry wheel inspection, and fresh Python
3.14 installation/dependency checks; the fresh 70-test suite had the expected
single checkout-only skip. No live cells were run by this validation.
