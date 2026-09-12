# Common PID RTL repairs — 2026-09-12

## Scope and provenance

The user approved separating pre-existing RTL defects from the Z7020 platform
port. Common repairs belong on a topic based on `develop`, merge into
`develop`, then propagate by merge to the development candidates that need
them. No commissioned compatibility main or original BIN is updated.

`fix/pid-rtl-shadowing` starts at `develop` commit `0138ba0`.
The PID source there is the same Git blob
`d293ac95b80503311d04d1dcaaa19321b3ef1e02` as the original baseline
`387faf3` and the pre-port merge `cd4bd73`. The two repairs were first
mixed with Z7020 development in `6e76d87`; this topic separates their
provenance without rewriting that existing history.

## Prerequisite: declaration visibility

Move the unchanged `IBW = ISR+14` constant and `int_shr` declaration
before the register-bus case that references them. This changes neither the
expression, width, register address nor clocked algorithm. It is an RTL-tool
compatibility prerequisite, not a Z7020-specific circuit change.

An actual run of XSim 2023.2 against the unmodified common source failed with
`VRFC 10-3380: identifier 'int_shr' is used before its declaration`.
The retained log is in local Windows `TEMP/pyrpl-pid-rtl-nhrwdvqk`.
There is no claim that a particular earlier simulator accepted this code.

With only the declaration move applied, compilation/elaboration succeeded,
but the real PID bench failed **34 of 341 checks** with unknown output X.
Logs remain at `TEMP/pyrpl-pid-rtl-y11yyqm6`. This isolates declaration
compatibility from the existing disconnected D-input defect. The declaration
commit alone is intentionally not a passing PID behavioral checkpoint.

The self-checking bench/runner are extracted unchanged from `6e76d87`.
They are added with the following bug-fix commit, not with this prerequisite.
XSim returns zero even for the failing bench's fatal termination; the runner
correctly reports failure when the pass token is absent.

## Default PI signal-shadowing repair

The disabled derivative generate branch declared a second `kd_reg_s`.
Its zero assignment did not drive the outer signal used by `pid_sum`.
Remove that inner declaration and make the outer continuously driven signal
a wire. No arithmetic expression, cycle boundary or enabled-D implementation
is changed. `DERIVATIVE=1` remains unsupported and unvalidated.

After this one logical connection repair, the same real RTL bench passed
**341 of 341 checks** in XSim 2023.2. Logs and source hashes remain at local
`TEMP/pyrpl-pid-rtl-06hi8nw8`. The corrected PID Git blob is exactly
`853dedbdd7aa83b67ac25a383967537b4b46fd0e`, identical to the previously
validated `6e76d87` version. This split introduces no further PID redesign.

The shared regression files are kept unchanged from `6e76d87`; they are
source-distribution development assets and excluded from the runtime wheel.

## Common-branch validation

- `uv sync --extra test` passed without lock-bypass flags. The dependency
  list and `uv.lock` are unchanged from `0138ba0`.
- Python 3.14 script/event-loop tests: 8 passed; actual ipykernel: 1 passed.
  The safe Nose NG memory/proxy/Python 3.9/Python 3.14 subset passed 17 tests
  (overlaps the unittest cases).
- All 111 Python files in this common checkout compiled with SyntaxWarning
  treated as an error.
- Source archive and 147-entry common wheel built successfully. A fresh
  Python 3.14.4 wheel installation passed dependency checks and the same nine
  script/kernel unittests from outside the checkout.
- Wheel inspection verified the pinned original BIN, no simulation/target
  sources and no DTBO additions. The source archive contains byte-identical
  simulation sources. Common `develop` does not import any Z7020 platform
  files, OS 2 loader changes or device-specific notebook changes.
- The common PID file is identical to the previously simulated Pro source;
  no additional synthesis or new hardware artifact is needed for this
  history/scope separation. This does not close the Pro timing findings.

## Boundaries

- Scope is the default `DERIVATIVE=0` PI implementation. No D-mode repair,
  PID/filter redesign, pipeline stage, fixed-point width, gain, hold/sequence
  behavior or feedback-latency change is authorized by this split.
- Timing failures are not automatically classified as common defects.
  Existing-source, tool/constraint and device-specific causes need evidence.
- Original BIN provenance is not sufficient to infer its behavior from the
  simulated source. Keep it byte-identical; source repair is not permission
  to rebuild/distribute replacement images.
- No physical board is contacted, and no notebook is executed or modified.

## Continued common implementation review — 2026-09-12

The user requested working on the shared fix topic and explicitly prohibited
propagation to any device/OS root until requested. This work stays on
`fix/pid-rtl-shadowing`; no merge into `develop` or any compatibility branch
is performed. The earlier integration commits remain unchanged.

The reference is the author's Z7010 RTL lineage, not an OS1-specific PID.
OS loading is outside this task. Z7010 and Z7020 full-design timing findings
must be assessed separately. This step fixes demonstrated source connections
and strengthens characterization; it does not claim to close timing.

### Enabled-filter failure isolated and repaired

The expanded real-RTL contract initially failed immediately after reset
release when an LPF stage was enabled: the expected numeric output was X.
The original wrapper connects SHIFTBITS bits to an LPF port declared as
SHIFTBITS+1 bits. XSim 2023.2 reported VRFC 10-3091.

The independent two-instance `.agents/probe_filter_port.sv` confirmed the
cause: the original 5-bit connection was observed at the LPF input as
`z00011`, while explicit padding yielded `000011`. After reset release,
the former produced X state/output; the latter retained numeric state.
This is an observed simulator connection result, not an assumption that the
warning is harmless padding and not proof about the historical hardware BIN.

The wrapper now connects `{1'b0, set_filter[...]}`. Register fields, shift
range/clamp, recurrence, state widths, truncation and pipeline registers are
unchanged. The LPF module's public port width is retained. No upper setting
bit is reinterpreted and no extra filter feature is introduced.

Both files before this repair are byte-identical Git blobs to `387faf3`:

- filter wrapper: `1cfa3ee02b61f55820fcdd71156d7a26736a168b`;
- LPF: `3bd14e0a257aad1649750e511cc0a39950fe6d82`.

Retained Windows TEMP evidence:

- `pyrpl-pid-rtl-42kio_lg`: expanded bench before the connection repair,
  failure at cycle 1 / 29 ns in the three-stage case;
- `pyrpl-filter-port-03d0137e`: independent narrow/padded port comparison;
- `pyrpl-pid-rtl-07bdevf1`: explicit-padding fix, all five filter cases pass.
  The IIR test width was corrected from the exploratory 14 to the actual
  17-bit input-prefilter width before this successful run.

### Explicit PID pause connections

The PID declared unused `pause_*_on_sync` nets but assigned/used the undeclared
`pause_i`, `pause_p`, `pause_d` nets. Rename only those three declarations to
the nets actually used. Their equations and destinations are unchanged.
A `default_nettype none` guard inside the module body catches future implicit
internal connections; `default_nettype wire` after the module prevents leakage
to subsequent sources. Legacy ANSI port declarations remain unchanged.

With the guard and old declarations, XSim rejected the three missing names
(TEMP `pyrpl-pid-rtl-kk5xaylv`). After correcting the declarations the entire
contract passed again (`pyrpl-pid-rtl-8z5vz72o`). An initial exploratory guard
before the ANSI header also required explicit port net types; it was moved
inside the body rather than expanding this repair into a port rewrite.

### Validation and remaining scope

- Real XSim 2023.2: **342 PID checks** (the prior 341 plus filter-completion
  gating) and **20,480 enabled-filter comparisons** passed. The five cases
  characterize PID, IQ input, four-stage 24-bit IQ quadrature, trigger and
  17-bit IIR input-prefilter configurations. They do not simulate complete
  IQ/IIR modules or prove the PID bus interaction with enabled filters.
- Filter checks use a separate integer recurrence model without forcing or
  reading DUT state. Each checks before/after the clock: signed rails,
  impulses, deterministic random data, reset, LPF/HPF/bypass, mixed cascades,
  every encoded shift and the existing clamp. Bypass state evolution,
  delta-register delay, wrap/truncation and four-cycle PID bypass latency
  are retained, not optimized away.
- The runner hashes/compiles both testbenches and all three real RTL sources.
  Four Python regressions validate source inclusion and failure reporting,
  including zero-exit `$fatal`, missing pass token and nonzero tool exit.
- Plain `uv sync --extra test`, 112 Python file compilations with
  SyntaxWarning as error, 13 checkout unittests (including real ipykernel),
  and the safe Nose NG subset of 21 tests passed. Some tests overlap.
  Nose needs the root regression file paths, not dotted `tests.*` names;
  the initial dotted invocation failed import and was rerun correctly.
- A fresh CPython 3.14.4 environment installed the 147-entry wheel, passed
  dependency checks and all 13 unittests from outside the checkout. Four
  runner tests intentionally exercise checkout development assets; runtime
  package and kernel use the fresh wheel environment. Wheel inspection
  verified the exact original BIN, no DTBO additions and no simulation files.
  The source archive contains byte-identical simulation assets and runner
  regressions. Package/test artifacts are at local
  `TEMP/pyrpl-common-review-8d06809a`.
- `.agents/synth_common_pid.tcl` also ran the actual PID/filter sources
  through Vivado 2023.2 out-of-context synthesis on the original
  `xc7z010clg400-1` part. It emitted reports/checkpoint only: 835 LUTs,
  545 flip-flops, 4 DSPs, no black boxes; synthesis reported 0 errors,
  0 critical warnings and 57 warnings. The 8 ns post-synthesis estimate
  was WNS +0.617 ns / WHS +0.190 ns. There is no placement/routing, actual
  clock insertion/skew or external I/O model, so these are NOT full-design
  timing closure and not a before/after performance comparison.
  Output: `TEMP/pyrpl-common-review-8d06809a/z7010-pid-synth`.
  This run's exact local source SHA-256 values (including working-copy
  line endings) are:
  - wrapper: `16234a28b5ca889d9fbd42aa5833c8a867a307ea84bba626fb257bfb22eb3784`;
  - PID: `74bfc901e3158dd6fc7ab5d0ed5b1933e284766afc0e7c3b298a7ebbf6213db1`.
- Remaining: integrated PID-with-enabled-filter behavior, full IQ/IIR/trigger
  datapaths, bus/control updates, Z7010 full-system timing baseline and cause
  attribution, and separately each port's constraints/timing/CDC findings.
  No clock lowering, additional latency, PID/filter redesign, D-mode repair,
  image generation or physical device access occurred.

Branch switching required care because this old common topic still tracks
`test.ipynb`, whereas the outgoing Pro branch ignores it. The exact local
file was moved aside and restored unchanged; its SHA-256 remains
`9769f6beee473a990a8a2d1b36cd500fa3b367066d38bca1b2f96757d65ed9f7`.
It therefore appears modified relative to the common topic's historical copy,
but it was not edited, executed or staged. Notebook-policy migration is not
part of this RTL change. The other restored `working-vs1` worktree is untouched.
