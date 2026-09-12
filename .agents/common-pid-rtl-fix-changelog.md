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
