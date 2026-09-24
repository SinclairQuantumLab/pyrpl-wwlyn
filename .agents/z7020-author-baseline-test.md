# Z7020 original-logic first-device test — 2026-09-15

## Scope and branch

The user requires wwlyn's original FPGA logic plus the Z7020/OS 2 platform
adaptation, **before** the common PID/filter repairs. This is an experimental
baseline comparison, not a commissioned release or a timing-closed design.

Subsequent user-run results confirm loading, connection and PID metadata reads;
see [the first field result](z7020-author-baseline-field-result.md). Statements
below about no live execution describe preparation/build time, not that later
user-run test. Physical signal measurements remain pending.

Work remains on `gen2-pro-os2/feature/device-upgrade`. At the user's explicit
request to rewrite the unpushed topic, its tip moved from the common-fix merge
`ef7f1c1` to `188dbfe042f9592dbf24ed5209bc43e207542cfe`. No new revert commit
was made. Older platform commits were not rebased. The removed merge remains
reachable from the unchanged `gen2-pro-os2/develop`; the common and per-root
fix topics are intact. No develop/main was changed, no push was made, and the
other worker's `pyrpl_change_python39_clean` worktree was not touched.
The redundant provisional `feature/author-baseline-test` and
`feature/device-acceptance` refs had no unique commits and were removed.

All 38 files in `pyrpl/fpga/rtl` match wwlyn commit
`387faf3012c21925c9905d81a95cb681ac7d1b22` (RTL tree
`d197c476ad28d31866fc6752196b78ba2f41d82d`). The target's `author_rtl.json`
and automated regression check file names and Git blob hashes, normalizing
Windows checkout line endings. This intentionally retains original declaration
order, shadowing and filter wiring. It does not prove that a modern-tool rebuild
has the same behavior as the author's historical Z7010 BIN.

## Artifact and loader

- Target: `xc7z020clg400-1`; Vivado/Bootgen 2023.2.
- Separate image: `pyrpl/fpga/red_pitaya_z20_gen2_author.bit.bin`, 4,045,568 bytes.
- SHA-256: `f6728daaf863f6c48a1d8b27a7262d7fb7653c489f37db36acd6cbb9cc4a7307`.
- Packaged provenance: adjacent `red_pitaya_z20_gen2_author.json`.
- Full source/report/checkpoint hashes: `z7020-author-baseline-build.json` here.
- Original Z7010 BIN remains byte-identical (`dc6e71fb...cee9ed`) and the default.

The notebook explicitly selects the new image. Only its exact hash together
with profile **22 / z20_125_v2 / Z7020** enables the experimental OS 2 path.
The original Z7010 image is still rejected on Z7020; this is not a blanket
authorization of all Z7020 profiles. Legacy loading of the new image is rejected.

The two existing fork DTBOs are reused byte-for-byte, selected according to
the installed `overlay.sh` firmware basename. Their historical `_z10` names do
not mean a different overlay is required: the generated PS handoff retains
125/250/50/200 MHz FCLKs and 64-bit HP0/HP1, and the untouched RTL retains direct
XADC. No official AXI-XADC overlay or third DTBO was imported.

## Actual build findings — not passing functional validation

The full build started in local `TEMP/z20-orig-279a0ec2` and was interrupted
during routing. The saved synthesis checkpoint was reopened by
`.agents/resume_author_test.tcl`; optimization/place/physical optimization/route
completed in `TEMP/z20-route-89433de7` without changing source or constraints.
The separate target exporter performed normal bitstream-generation DRC and
wrote the `.bit`, followed by Bootgen conversion. Commands for a fresh full
build/export are in `pyrpl/fpga/targets/z20_gen2/README.md`.

| Check | Result |
| --- | --- |
| Routing | 21,886/21,886 nets, 0 routing errors |
| Bitstream DRC | 0 errors, 133 warnings; no severity waivers |
| Setup timing | WNS **-4.490 ns**, TNS -5796.621 ns, 7,318 failing endpoints |
| Hold timing | WHS **-2.362 ns**, 28 failing endpoints |
| Methodology | TIMING-17 critical warning for the DNA clock |
| Missing constraints | 2 internal endpoints, 16 input delays, 46 output delays |
| Original RTL XSim | **Compilation fails:** `int_shr` used before declaration |

The actual PID XSim runner was invoked; artifacts are at local
`TEMP/pyrpl-pid-rtl-6xfg3rff`. Its failure is not replaced by the passing results
from the repaired branch. Synthesis accepts the declaration order with warnings;
successful bitstream generation does not override the simulation or timing
findings. No DSP fixes, added pipeline cycles, reduced clocks, false paths or
DRC waivers were introduced for this experiment. Hardware behavior is untested.

## Offline software and package validation

`.agents/validate_author_candidate.py` completed successfully with evidence at
local `TEMP/pyrpl-author-package-7e0f3f34`:

- `uv sync --extra test`, without locked/frozen flags.
- All 119 project Python files compiled, with SyntaxWarning treated as an error.
- Checkout unittest suite: **70 passed**, including real-ipykernel event-loop,
  loader, artifact/source identity and notebook-structure regressions.
- Nose NG safe subset: **25 passed** (overlaps some unittest cases).
- Fresh CPython 3.14 wheel installation and dependency check passed; the same
  70-test suite completed with one expected checkout-only Git-ignore skip.
- Wheel: 155 entries; correct original BIN, separate experimental BIN and JSON,
  exactly the two approved DTBOs and their DTS sources. No agent notes, target
  sources or simulation sources in the runtime wheel; source archive checked.
- Both recognized firmware basenames and mocked uploads are tested. No test
  contacted the board or programmed hardware.

## User-run notebook

The tracked starter is `test.ipynb.template`; the ignored local `test.ipynb`
sets the already identified unit's address to `192.168.50.175`. Neither contains
a password or executed outputs. Restart/select the project's `.venv` kernel
before using the newly changed loader. Execute each step separately:

1. Local interpreter/package/image and build-record check (no board access).
2. Password prompt and read-only preflight.
3. Upload/program this experimental image and matching overlay.
4. Start/connect PyRPL without another FPGA load.
5. Continue the explained register/bench comparisons, recording actual results.

Programming and connecting are separate cells. There is no artificial `LOAD`
confirmation token. The notebook explains device mutations and experimental
output precautions in its short Markdown cells. No cells were executed during
preparation; field results and any main promotion remain pending.

The previous local notebook, including saved results, is preserved byte-for-byte
at `.agents/local-notebooks/test-gen1-os2-before-z7020-20260915.ipynb`:
SHA-256 `9769f6beee473a990a8a2d1b36cd500fa3b367066d38bca1b2f96757d65ed9f7`.
Both the local notebook and backup directory are ignored; the backup may contain
old credentials and must not be staged or shared.
