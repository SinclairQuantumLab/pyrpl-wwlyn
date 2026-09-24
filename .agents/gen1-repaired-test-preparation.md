# Gen1 repaired-image bench preparation — 2026-09-24

The user requested preparing `gen1-os1/develop` and `gen1-os2/develop` in
the same sense as the repaired Pro develop: a real, separately named image,
explicit loader selection and a clean, stepwise notebook. No physical device
was contacted or programmed. Accepted mains and original-logic images remain
separate; this is not a main-promotion or timing-repair task.

## Image and platform

The common RTL is byte-identical (after Git line-ending normalization) to
`e7479166c03c15bdd244e2153e974b4596815041`. It contains the declaration,
disabled-D, padding/pause and literal-zero repairs already merged into these
develops. No RTL was changed for this preparation. The real XSim run passed
342 PID checks and five filter families with 4,096 comparisons each:
`C:/Users/imaq/AppData/Local/Temp/pyrpl-pid-rtl-958cq0bz/result.json`.

The new `z10_gen1` target derives the author's original Z7010 PS design and
constraints, not the Pro PS shell. Its explicit Vivado 2015.4 → 2023.2
adaptations are documented beside the target. Full synthesis, placement,
routing and separate export are required. The export retains the author's
uncompressed BIT → SMAPx32/disablebitswap BIN conversion and filename
`red_pitaya_z10_gen1_repaired.bin`. It is not a reproduction of the original
2015.4 binary. Raw report/artifact hashes and open timing findings are in
`z7010-repaired-build-evidence.json`.

The first exploratory route/export (`z10-repair-86cd9547`) was **not
packaged**. Its clock report established that six old false-path statements
refer to nonexistent clocks, but the seventh (`clk_fpga_0` → `adc_clk`) is
valid. That exception was restored before the final fresh build; no new
timing exceptions were added. Two earlier attempts failed during the Tcl
adaptation, before synthesis (`z10-repair-42c0b526`, `z10-repair-a8e91ce5`).

## Loader separation

- OS2 keeps its existing overlay loader, exact original-board profiles 1/2
  and both hash-pinned firmware-name DTBOs. The repaired hash is an additional
  explicitly approved candidate, not a replacement default or expanded
  device family. Preflight identifies the selected image lineage.
- OS1 uses `/dev/xdevcfg`, not overlays. The repaired path reads ecosystem
  version, `fw_printenv -n hw_rev`, and character-device status before any
  mutation. It accepts only exact original 125-14 identities, including the
  vendor's old `STEM_14_B_v1.0` alias. Unknown identity, EEPROM warnings,
  Gen2/Z7020/other ADC families, OS2/OS3 and ordinary files at `/dev/xdevcfg`
  are rejected. It checks the staged hash and the programming exit status.
- EEPROM mapping provenance: Red Pitaya's
  [hardware-profile mapping](https://github.com/RedPitaya/RedPitaya/blob/master/rp-api/api-hw-profiles/src/common.cpp).
  Unlike that API's convenience fallback, an unknown model is never treated
  as the standard 125-14 by this guard.

## Notebook and user handoff

The tracked template selects `pyrpl.z10_repaired.repaired_file()`, so its
first cell checks the candidate hash locally. Steps separate preflight,
programming and connection, followed by metadata, paired DC measurements,
1 Hz and 1 kHz triangles, and the original negative-I feedback test with an
ASG disturbance. The analog cells are selectively reused from Pro develop
`acf7969`; no Pro loader/platform/image is imported. The Gen2 full-scale
description is removed. Measured input and output calibrations stay local.

Existing local notebooks/settings/results must remain unchanged. Restart the
kernel after changing branches, select the corresponding checkout's `.venv`,
and use a new copy of that branch's template. Never overwrite a saved bench
notebook merely to update its starter. `uv sync --extra test` supplies the
notebook kernel without locked/frozen flags.

Record the candidate hash, board/OS, preflight output, programming result,
PID metadata and physical observations. A successful limited bench test
does not establish timing closure. Timing investigation/redesign and main
promotion require separate user direction.

## OS2 offline validation

- Existing loader regressions: 24 passed; new shared/candidate and OS2
  selection tests: 14 passed. Rejected hardware performs no upload/mutation.
- Python 3.14 compatibility: 8 passed; real ipykernel regression: 1 passed;
  safe legacy memory/proxy subset: 5 passed. `compileall` passed for package/tests.
- Built sdist and wheel with normal `uv build`; installed the wheel into a
  fresh CPython 3.14.4 environment. Candidate tests: 14 passed with 3 expected
  source-only skips; Python/kernel tests: 8 + 1 passed there too.
- Wheel inspection verified both exact BIN hashes, both unchanged DTBOs, and
  exclusion of FPGA target/simulation sources. Artifacts are under
  `C:/Users/imaq/AppData/Local/Temp/gen1-os2-repaired-wheel-20260924`.
- No device tests were run. The accepted mains and primary ignored notebook
  remain unchanged; its SHA-256 before/after preparation is
  `aae3dfb2864824a560554fd9b47ae6643d944b07cc248e6e117cc83bbf639415`.

## OS1 integration and validation

- Selectively backported build `e7dc8f9` and artifact/helper `504e442` with
  `cherry-pick -x`; no OS2 or Pro platform/DTBO/loader merge. Adapted the
  notebook/guidance from OS2 preparation `714b4e5` for the legacy path.
- Added the existing non-interactive SSH `execute()` interface to OS1 and
  routed only repaired-image selection through the checked legacy loader.
  The explicit original-image filename path is retained (also fixes its
  previously uninitialized `source` local). Defaults still select the author BIN.
- OS1's old tracked notebook was untracked, not discarded. Its unchanged
  local archive is `.agents/local-notebooks/test-gen1-os1-historical-20260924.ipynb`
  (SHA-256 `1ab79241580370b0de18aa5d541e2b41462a0e3e755463c6dce6e30b2216f89f`).
  Prior Git history also retains it. The primary Pro notebook was restored
  unchanged. AGENTS now follows the same template/ignored-copy policy as OS2/Pro.
- Shared/OS1 loader and notebook checks plus Python/kernel regressions:
  24 passed, followed by the added staging-failure cleanup regression and its
  seven-test legacy-guard group. `compileall` passed. RTL/build/image identity
  with OS2 was checked, so no duplicate Vivado/XSim build was needed.
- Fresh CPython 3.14.4 wheel install: 16 candidate tests passed with 3 expected
  source-only skips. Wheel inspection verified both BIN hashes, no DTBOs,
  and exclusion of FPGA target/simulation sources. Final artifact directory:
  `C:/Users/imaq/AppData/Local/Temp/gen1-os1-repaired-wheel-final-20260924`.
- Cleanup hardening `aaca6d7` restores read-only mount even if staging-directory
  creation fails after remount; it is also propagated to OS2. This changes no
  FPGA artifact, RTL or default image selection.
