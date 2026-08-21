# CPython 3.14 upgrade changelog and reproduction runbook

This record describes the complete migration from the repository's completed
CPython 3.9 state to CPython `3.14.*`. It is intended to let a human maintainer
or an AI agent review every material decision, reproduce the upgrade in a new
worktree, and distinguish compatibility-only edits from behaviorally
substantial changes.

## Executive answer: this was not only a dependency-version upgrade

Several changes were qualitatively substantial beyond resolving dependency
versions:

1. The abandoned Quamash event-loop integration was replaced by qasync and a
   three-mode integration for scripts, terminal IPython, and modern ipykernel.
   This changes event-loop ownership and how synchronous waits coexist with a
   host-owned asyncio loop.
2. `scipy.misc.derivative` was replaced by an in-tree five-point numerical
   derivative implementation. It preserves the intended calculation but can
   differ by tiny floating-point amounts.
3. Deleted NumPy aliases were removed throughout runtime, GUI, documentation,
   and tests, enabling NumPy 2 rather than holding the application on NumPy
   1.23.
4. Qt timer, geometry, cleanup, and logging behavior was hardened for current
   PyQt5/pyqtgraph, including deterministic widget handler teardown.
5. Red Pitaya connection teardown was made safe and idempotent even when a
   connection failed before SSH/channel construction.
6. Packaging metadata was promoted from placeholder state to a coherent
   distribution identity, including the runtime version, license expression,
   project URLs, classifiers, and an independently verified wheel.
7. A Windows CPython 3.14 CI gate, an actual-kernel compatibility test, a
   runtime compatibility suite, and a wheel-content verifier were added.

No FPGA bitstream, DTBO, RTL, register map, or hardware programming algorithm
was changed in this 3.14 migration.

## Boundary and commit sequencing

The Python 3.14 work was developed as uncommitted changes on branch
`develop/python-upgrade`, initially based on:

```text
adbca0a7dd7d023638f1d16133b38ad26094845f  Upgraded to python 3.9
```

That hash identifies the original pre-amendment commit. The user intends to
amend it with the standalone 3.9 changelog first. Amendment changes the 3.9
commit ID. The Python 3.14 commit must then use the amended 3.9 commit as its
parent and contain every file in this record except
`.agents/python-3.9-upgrade-changelog.md`.

Do not use the original hash as a permanent release boundary after amendment.
Record the new parent in the eventual 3.14 commit message or release notes.

## Scope and platform contract

The resulting supported environment is:

- CPython `3.14.*`.
- x86-64 Windows as the resolved/validated binary-wheel environment.
- PyQt5, not PyQt6.
- NumPy 2 and current SciPy/lmfit major lines within tested bounds.
- qasync as the Qt/asyncio bridge.
- Modern ipykernel with top-level `await` support.
- Nose NG's `nosetests` executable for selected inherited legacy tests.
- uv as the lock, synchronization, command, and wheel-build frontend.

This is not a declaration that every inherited PyRPL test or historical
documentation page is modernized. Hardware-coupled tests remain opt-in, and
historical documentation is explicitly marked as archival.

## Complete file inventory

The implementation/release commit should contain the following 48 files after
the 3.9 changelog has been amended into its parent: 42 modifications inherited
from the migration work, four new validation files, and two new `.agents`
documentation files. `AGENTS.md` is counted among the 42 modifications.

### Environment, packaging, release, and documentation

| Status | File | Change |
| --- | --- | --- |
| Modified | `.gitignore` | Ignores local `.venv/` and `.pytest_cache/`. |
| Modified | `.python-version` | Selects Python 3.14 instead of 3.9. |
| Modified | `AGENTS.md` | Replaces 3.9 bounds/workflow with current 3.14 constraints, safety rules, CI authority, and the `.agents` link. |
| Added | `.agents/README.md` | Indexes the standalone upgrade records and explains the two-commit staging boundary. |
| Added | `.agents/python-3.14-upgrade-changelog.md` | This detailed migration and reproduction record. |
| Added | `.github/workflows/python314.yml` | Adds the authoritative Windows Python 3.14 offline, legacy, wheel, and CLI CI gate. |
| Modified | `Documentation.md` | Marks historical instructions as non-authoritative. |
| Modified | `README.md` | Rewrites installation, quick-start, validation, hardware-safety, documentation, upgrade, and license guidance for this fork. |
| Modified | `docs/source/conf.py` | Updates documentation mocks from Quamash to qasync. |
| Modified | `docs/source/developer_guide/api/asynchronous/benchmark.rst` | Updates asynchronous examples for integer timers/current behavior. |
| Modified | `docs/source/developer_guide/api/asynchronous/index.rst` | Describes qasync instead of Quamash and updates PyQt5-era examples. |
| Modified | `docs/source/index.rst` | Adds a prominent historical-archive warning for inherited Sphinx content. |
| Modified | `pyproject.toml` | Sets Python 3.14, real distribution metadata, bounded dependencies, test extras/dev group, URLs, license, and root package mapping. |
| Modified | `pyrpl.yml` | Makes the Conda bootstrap select Python 3.14 and install `-e .[test]`. |
| Modified | `uv.lock` | Regenerates the complete Python 3.14 dependency graph. |

### Runtime, numerical, async, GUI, and device cleanup

| Status | File | Change |
| --- | --- | --- |
| Modified | `pyrpl/__init__.py` | Imports NumPy warnings from `numpy.exceptions`; establishes script, terminal-IPython, and ipykernel loop modes. |
| Modified | `pyrpl/__main__.py` | Reuses the selected loop, avoids re-running an active host loop, and aligns CLI help with the distribution command. |
| Modified | `pyrpl/async_utils.py` | Reworks futures, timers, blocking waits, sleeps, host-loop compatibility, and misuse errors around qasync. |
| Modified | `pyrpl/curvedb.py` | Replaces deleted NumPy scalar aliases with supported dtypes. |
| Modified | `pyrpl/hardware_modules/ams.py` | Replaces deleted NumPy scalar aliases. |
| Modified | `pyrpl/hardware_modules/asg.py` | Replaces deleted NumPy scalar aliases. |
| Modified | `pyrpl/hardware_modules/iir/__init__.py` | Updates IIR-facing dtype/docs compatibility. |
| Modified | `pyrpl/hardware_modules/iir/iir.py` | Replaces deleted aliases and corrects invalid escape text. |
| Modified | `pyrpl/hardware_modules/iir/iir_theory.py` | Replaces deleted aliases and aligns numerical documentation. |
| Modified | `pyrpl/hardware_modules/iq.py` | Replaces deleted aliases and corrects invalid escape text. |
| Modified | `pyrpl/hardware_modules/pid.py` | Replaces deleted NumPy scalar aliases. |
| Modified | `pyrpl/hardware_modules/scope.py` | Replaces deleted aliases and corrects invalid escape text. |
| Modified | `pyrpl/hardware_modules/trig.py` | Makes the trigonometric docstring raw so Python 3.14 does not emit an invalid-escape `SyntaxWarning`. |
| Modified | `pyrpl/memory.py` | Converts Qt timer intervals to strict integer milliseconds. |
| Modified | `pyrpl/modules.py` | Removes the transitive `six.with_metaclass` dependency in favor of native Python 3 metaclass syntax. |
| Modified | `pyrpl/pyrpl.py` | Aligns application/widget integration with current event-loop and teardown behavior. |
| Modified | `pyrpl/redpitaya.py` | Makes client/server/SSH teardown safe and idempotent after partial connection failures. |
| Modified | `pyrpl/software_modules/lockbox/input.py` | Replaces removed `scipy.misc.derivative` with an explicit five-point central difference. |
| Modified | `pyrpl/software_modules/loop.py` | Converts Qt timer intervals to strict integer milliseconds. |
| Modified | `pyrpl/software_modules/network_analyzer.py` | Replaces deleted NumPy scalar aliases. |
| Modified | `pyrpl/software_modules/spectrum_analyzer.py` | Replaces deleted NumPy scalar aliases. |
| Modified | `pyrpl/widgets/module_widgets/iir_widget.py` | Replaces aliases and keeps current plotting dtype behavior. |
| Modified | `pyrpl/widgets/module_widgets/module_manager_widget.py` | Rounds computed positions before passing integer coordinates to Qt. |
| Modified | `pyrpl/widgets/module_widgets/na_widget.py` | Stops returning from `finally`, allowing exceptions to propagate normally. |
| Modified | `pyrpl/widgets/module_widgets/schematics.py` | Uses integer move coordinates and `QPointF` for floating polygon geometry. |
| Modified | `pyrpl/widgets/pyrpl_widget.py` | Uses integer timer intervals and explicitly stops/disconnects/closes its Qt logging handler during `_clear()`. |

### Tests and validation helpers

| Status | File | Change |
| --- | --- | --- |
| Modified | `pyrpl/test/test_base.py` | Updates test logging/event-loop references from Quamash to qasync. |
| Modified | `pyrpl/test/test_hardware_modules/test_pid_na_iq.py` | Replaces deleted NumPy scalar aliases in tests. |
| Modified | `pyrpl/test/test_pyqtgraph_benchmark.py` | Uses integer Qt timer intervals. |
| Modified | `pyrpl/test/test_redpitaya_fpga_loader.py` | Adds a 13th loader test for idempotent cleanup after no/partial connection. |
| Added | `pyrpl/test/test_ipykernel_compatibility.py` | Starts a real kernel and verifies imports, top-level awaits, Qt-backed futures, blocking compatibility, and kernel survival. |
| Added | `pyrpl/test/test_python314_compatibility.py` | Adds 11 focused runtime, NumPy, derivative, Qt, asyncio, CLI, subprocess, and cleanup tests. |
| Added | `pyrpl/test/verify_wheel.py` | Validates wheel files, metadata, dependency bounds, entry point, license, version, and absence of the scaffold package. |

The standalone `.agents/python-3.9-upgrade-changelog.md` must not appear in
this commit because it belongs to the amended parent.

## Interpreter, metadata, and packaging changes

### Version alignment

The following sources are aligned on Python `3.14.*`:

- `.python-version` contains the 3.14 selector.
- `pyproject.toml` declares `requires-python = "==3.14.*"`.
- `pyrpl.yml` selects `python=3.14`.
- `uv.lock` was regenerated under the new constraint.
- CI installs Python 3.14 explicitly.

The validated local patch release was CPython `3.14.4`. The project promises
the `3.14.*` line rather than only that patch release.

### Distribution identity

The earlier `0.1.0` placeholder metadata was corrected to match the runtime:

| Field | Result |
| --- | --- |
| Name | `sinclair-pyrpl-wwlyn` |
| Version | `0.9.5.0` |
| Runtime version source | `pyrpl.__version__` also reports `0.9.5.0` |
| Description | Sinclair Lab PyRPL fork for Red Pitaya DSP and lockbox control |
| Python | `==3.14.*` |
| License expression | `GPL-3.0-or-later` |
| Included license | Root `LICENSE` |
| CLI | `sinclair-pyrpl-wwlyn = pyrpl.__main__:main` |
| Package mapping | Root `pyrpl/`; empty `module-root` |
| Required resolver platform | Windows AMD64 |

The license expression uses “or later,” not GPL-3.0-only, because the existing
source headers expressly grant GPL version 3 or any later version. Repository,
issues, and documentation URLs, keywords, and classifiers were also added.

### Wheel correctness

The new verifier rejects a wheel unless it contains at least:

- `pyrpl/__init__.py`.
- Required global configuration YAML.
- `pyrpl/fpga/red_pitaya.bin`.
- `pyrpl/fpga/red_pitaya.dtbo`.
- The root `LICENSE` in distribution metadata.
- The expected distribution name, version, Python requirement, license,
  Paramiko range, and console entry point.

It also rejects the obsolete `src/pyrpl_change` scaffold as packaged runtime
content. The isolated wheel smoke test imports outside the repository so an
editable checkout cannot shadow a broken wheel.

## Dependency migration

### Direct constraints and validated resolutions

| Dependency | Declared constraint | Validated resolution | Reason/notes |
| --- | --- | ---: | --- |
| scp | `>=0.15,<1` | `0.16.1` | SSH copy helper. |
| matplotlib | `>=3.10.5,<4` | `3.11.1` | Python 3.14-compatible plotting line. |
| SciPy | `>=1.16.1,<2` | `1.18.0` | Python 3.14 wheels; removed `misc.derivative` handled in source. |
| PyYAML | `>=6.0.3,<7` | `6.0.3` | Configuration serialization. |
| pandas | `>=2.3.3,<4` | `3.0.5` | Curve database support. |
| pyqtgraph | `>=0.14,<1` | `0.14.0` | Current PyQt5 plotting API. |
| NumPy | `>=2.3.2,<3` | `2.5.2` | First supported Python 3.14/NumPy 2 line used here. |
| Paramiko | `>=4,<6` | `5.0.0` | Older source uses `async=` syntax, which is invalid on Python 3.14. |
| PyQt5 | `>=5.15.11,<6` | `5.15.11` | Stable-ABI bindings validated on CPython 3.14. |
| PyQt5-Qt5 | transitive | `5.15.19` | Native Qt bundle. |
| PyQt5-sip | transitive | `12.19.0` | Binding support. |
| QtPy | `>=2.4.3,<3` | `2.4.3` | Qt abstraction. |
| nbconvert | `>=7.16,<8` | `7.17.1` | Notebook conversion integration. |
| jupyter-client | `>=8.6,<9` | `8.9.1` | Real-kernel regression infrastructure. |
| netifaces2 | `>=0.0.22,<1` | `0.0.22` | Provides the `netifaces` import via a validated Windows stable-ABI wheel. |
| lmfit | `>=1.3.4,<2` | `1.3.4` | Compatible with NumPy 2. |
| qasync | `>=0.28,<0.29` | `0.28.0` | Maintained replacement for Quamash. |
| ipykernel | `>=6.31,<8` | `7.3.0` | Modern host-owned asyncio loop and top-level await. |
| IPython | transitive | `9.16.1` | Kernel/interactive runtime. |
| nose-ng | `>=1.4.3,<2` | `1.4.3` | Maintained `nosetests`; original Nose imports removed stdlib APIs. |

The lock contained 85 package records. The synchronized default environment
contained 81 installed packages including the development dependency. A clean
runtime wheel environment installed 80 packages.

### Intentional removals/replacements

- Quamash `0.6.1` was removed and replaced by qasync `0.28.0`.
- Original Nose `1.3.7` was removed and replaced by Nose NG `1.4.3`.
- `scipy.misc.derivative` is no longer required.
- Runtime source no longer relies on transitive `six` for metaclass syntax.
- Original `netifaces` remains replaced by `netifaces2`; its import name is
  intentionally still `netifaces`.

`nose-ng` appears in both `[project.optional-dependencies].test` and
`[dependency-groups].dev`. That duplication is intentional: the test extra
supports pip/Conda editable installation, while the dev group makes normal uv
development commands include the runner without making it a runtime
dependency.

## NumPy 2 migration

The Python 3.9 state held NumPy below 1.24 because runtime and test code used
removed aliases. The 3.14 work replaces active uses as follows:

| Removed alias | Replacement |
| --- | --- |
| `np.float` | built-in `float` |
| `np.int` | built-in `int` |
| `np.complex` | built-in `complex` |

The changes span curve storage, AMS/ASG/IIR/IQ/PID/scope modules, network and
spectrum analyzers, widget code, tests, and nearby documentation/comments.
The replacements preserve the intended Python scalar/dtype semantics. The
CurveDB regression specifically creates and reads data on NumPy 2 to ensure
the migration is not merely import-clean.

Invalid escape sequences that became `SyntaxWarning` failures under the strict
3.14 validation were also corrected in IIR, IQ, scope, and trigonometric
documentation strings. Compilation is run with
`PYTHONWARNINGS=error::SyntaxWarning` in CI so regressions fail.

NumPy warning classes are imported from `numpy.exceptions`, their supported
NumPy 2 location.

## SciPy derivative replacement

`scipy.misc.derivative` was removed from supported SciPy. The lockbox input
code now computes the first derivative using a five-point central difference:

```text
f'(x) = [f(x - 2h) - 8f(x - h) + 8f(x + h) - f(x + 2h)] / (12h)
```

with `h = 1e-6`.

This is a fourth-order finite-difference approximation and is appropriate for
the prior call's intended first derivative. A regression verifies that the
derivative of a quadratic is `6` at `x = 3` within floating-point tolerance.
Because the evaluation stencil and implementation changed, last-bit numerical
differences from historical SciPy output are possible and should not be hidden
when comparing saved calibration data.

## Qt and asyncio architecture

This is the largest qualitative runtime change.

### Why loop ownership matters

Plain scripts need PyRPL to drive Qt and asyncio. Modern ipykernel already owns
and runs an asyncio loop and must not have it replaced or re-entered. Terminal
IPython often uses a Qt input hook without an already running asyncio task.
Treating all three environments identically causes deadlocks, “event loop is
already running” errors, broken top-level awaits, or frozen Qt timers.

### Mode 1: plain scripts, CLI, and tests

When no external loop is running:

1. PyRPL creates a normal `qasync.QEventLoop(APP)`.
2. PyRPL owns that loop and installs it as the current event loop.
3. Synchronous `PyrplFuture.await_result()` may run it to completion.
4. The CLI calls `LOOP.run_forever()`.

If CLI initialization encounters a loop already running, it does not attempt
to run it a second time.

### Mode 2: modern ipykernel or import inside an active asyncio loop

When import occurs with a running host asyncio loop:

1. PyRPL reuses the host loop.
2. It does not replace the host's policy/current loop.
3. It does not invoke the legacy `%gui qt` magic.
4. It schedules a process-lifetime `IPYTHON_QT_PUMP` task.
5. The task calls `APP.processEvents()` approximately every 10 ms.

This lets a notebook perform top-level `await`, lets Qt timer-backed futures
complete, and keeps later cells alive. The pump is intentionally retained for
the process lifetime; garbage-collecting it would silently stop Qt progress.

### Mode 3: terminal IPython without a running asyncio loop

When an IPython shell exists but asyncio is not already running:

1. PyRPL enables the shell's Qt GUI input hook.
2. It constructs `qasync.QEventLoop(APP, already_running=True)`.
3. The loop is marked as externally/non-PyRPL-owned.

This retains interactive Qt behavior without PyRPL taking over the terminal's
input-processing loop.

### `PyrplFuture.await_result()` behavior

All `PyrplFuture` instances are explicitly associated with the selected
`LOOP`.

- On a PyRPL-owned, nonrunning loop, `await_result()` uses
  `LOOP.run_until_complete(self)`.
- If called synchronously from an active asyncio Task on the PyRPL-owned loop,
  it raises an actionable error telling the caller to `await` the future. A
  synchronous nested run would be invalid.
- Under an externally running host/kernel loop, it uses a small raw nested Qt
  loop that polls future completion every 1 ms. It does not attempt to re-enter
  the host asyncio loop.
- Timeouts use `MainThreadTimer` and report that the timeout “occurred.”

The nested Qt compatibility path exists to retain legacy synchronous PyRPL
calls in notebook cells while respecting kernel ownership. New coroutine code
should prefer `await`.

### `async_utils.sleep()` behavior

- Calling blocking `sleep()` from inside a Task on the PyRPL-owned loop is
  rejected with guidance to use `await asyncio.sleep(...)`.
- Under a host/external loop, the compatibility path continues processing Qt
  events so the UI does not freeze.
- On a nonrunning PyRPL-owned loop, a Qt timer completes a Future for the main
  portion of the interval; the final millisecond is finished precisely. This
  lets already scheduled native asyncio Tasks advance.
- Timer intervals are converted to valid integer milliseconds.

### Known qasync warning

qasync 0.28 works on CPython 3.14 and passed the maintained suite. It currently
emits a deprecation warning related to `asyncio.iscoroutinefunction`, which is
scheduled for removal in Python 3.16. This is not a Python 3.14 failure, but the
`<0.29` pin should be reviewed when a maintained replacement release is
available or before a Python 3.16 upgrade.

## Qt, GUI, and cleanup compatibility

Current PyQt5 is stricter about integer timer intervals and coordinates. The
migration therefore:

- Converts or rounds timer intervals in `memory.py`, software `loop.py`,
  `PyrplWidget`, and pyqtgraph benchmark tests.
- Rounds module-manager and schematic widget move coordinates to integers.
- Uses `QPointF` for schematic polygon points that intentionally retain
  floating coordinates.
- Stops, disconnects, removes, and closes `PyrplWidget`'s logger handler during
  `_clear()`, then clears the reference. This prevents logging shutdown from
  accessing a deleted Qt object.
- Moves the network-analyzer widget's `super().mousePressEvent(...)` return out
  of a `finally` block. A return from `finally` can suppress active exceptions;
  exceptions now propagate normally.
- Retains the 3.9 keyword-based pyqtgraph `GraphicsLayoutWidget` construction.

`MainThreadTimer` also normalizes intervals through rounding and integer
conversion, with a lower bound appropriate to Qt.

## Native metaclass migration

`pyrpl/modules.py` changed the legacy form based on
`six.with_metaclass(ModuleMetaClass, object)` to native Python 3 syntax:

```python
class Module(object, metaclass=ModuleMetaClass):
    ...
```

The inheritance and metaclass were audited as semantically equivalent. This
removes a direct runtime reliance on an undeclared transitive dependency and
does not introduce a new module lifecycle.

## Red Pitaya behavior in the 3.14 change

`endserver()`, `endclient()`, and `end_ssh()` now tolerate being called when
SSH, a channel, or a client was never created or was already closed. Cleanup
can therefore run after partial constructor/connection failures and can run
more than once.

The 3.14 migration did not change:

- `pyrpl/fpga/red_pitaya.bin`.
- `pyrpl/fpga/red_pitaya.dtbo`.
- The OS 2/OS 3 fixed server paths.
- The overlay programming algorithm.
- The guarded legacy `/dev/xdevcfg` behavior.
- FPGA register addresses or expected signature values.
- RTL sources.

The inherited assets remain:

| Artifact | SHA-256 |
| --- | --- |
| `red_pitaya.bin` | `4894f44b7611f2f0cbc18d339596f28476e452de1bac01a30206864ccd92fffe` |
| `red_pitaya.dtbo` | `9c19b99bef128d6069d44e8294ce6f118ee8513e523673ec02e1510d76877020` |

No physical Red Pitaya was contacted during the 3.14 validation. The new
cleanup test is fully offline.

## Documentation changes

The root README was rewritten because inherited directions could install a
different upstream PyRPL package or tell users to copy files into
site-packages. The current README now covers:

- uv-based installation and synchronization.
- Optional Conda bootstrapping around this checkout.
- The real CLI and Python import path.
- Safe offline validation.
- Red Pitaya board/FPGA safety.
- Which documentation sources are authoritative.
- Dependency/lock update procedure.
- Wheel building and GPL licensing.

`Documentation.md` and the Sphinx root are marked historical. Many inherited
pages and notebooks still describe old setup.py, dependency, or release flows.
The archive warning is deliberate: rewriting every historical page without
revalidating its behavior would create false authority. The qasync-specific
asynchronous pages and mocks were updated because they directly affect current
runtime comprehension.

## Tests added and maintained gates

### Python 3.14 compatibility suite

`test_python314_compatibility.py` contains 11 focused tests:

1. The active runtime is CPython 3.14.
2. Distribution metadata version equals `pyrpl.__version__`.
3. CurveDB operations use a NumPy 2-compatible dtype.
4. The replacement derivative returns the expected quadratic slope.
5. A Qt timer completes a `PyrplFuture` with an integer interval.
6. A native coroutine advances through the PyRPL sleep/loop integration.
7. A blocking future wait still advances an already scheduled native task.
8. Blocking sleep inside a PyRPL-owned active Task is rejected with guidance.
9. Import inside a running host loop works in a subprocess without replacing
   or corrupting that loop.
10. The CLI runs the qasync loop and can be stopped cleanly.
11. `PyrplWidget` logging-handler cleanup does not retain a deleted Qt object.

### Actual ipykernel compatibility suite

`test_ipykernel_compatibility.py` launches the exact current Python executable
through `jupyter_client`, with offscreen Qt, an isolated user directory, and a
fake Red Pitaya hostname. It executes separate kernel cells to verify:

1. `import pyrpl` succeeds in the kernel.
2. A subsequent cell can perform normal asyncio top-level `await`.
3. A blocking `PyrplFuture` returns `42`.
4. A direct top-level await of a Qt-backed Future returns `43`.
5. A later cell still runs, proving the integration did not terminate or
   corrupt the host loop.
6. The kernel is shut down in test cleanup.

This subprocess test is important: importing under an actual ipykernel has
different loop ownership from importing under `unittest`.

### Existing loader and legacy coverage

- The FPGA loader module now has 13 tests: the 12 inherited from the 3.9 work
  plus cleanup idempotence.
- Selected MemoryTree, proxy-property, and attribute tests run under
  `nosetests` from Nose NG.
- Pytest is not the authoritative runner for the inherited suite because it
  does not honor all Nose-style class lifecycle conventions.

### Maintained passing totals

The final maintained local gate passed:

- 25 `unittest` tests: 13 loader, 11 Python 3.14 compatibility, and one
  real-kernel test method containing the multi-cell scenario.
- 8 selected Nose NG tests across memory, proxy-property, and attribute files.
- Strict `compileall` with `SyntaxWarning` promoted to error.
- Ruff critical checks.
- Lock consistency, dry synchronization, and installed dependency checks.
- Parsed project metadata checks.
- CLI help.
- Wheel build, structural/metadata verification, clean install, import outside
  the source tree, and isolated CLI invocation.

## Exploratory result that is not part of the gate

A broader fake-device `test_load_save` exploration generated 29 cases. Twenty-
eight passed. One failed because fake HK expansion state was saved as true and
read back as false for `hk.expansion_P1`. This was judged an unrelated or
pre-existing fake-device/setup mismatch, not evidence of a Python 3.14 source
failure.

The result is recorded rather than hidden, but that test is not in the
maintained CI gate. It must not be described as passing unless its fake-device
assumptions are separately repaired and reviewed.

The entire inherited suite was not run. Many tests inherit live Red Pitaya
setup, can mutate outputs, or can hang while waiting for hardware. Avoiding
those tests is an explicit safety decision, not proof that they all pass.

## Authoritative validation commands

Run validation from the repository root on Windows PowerShell. Use a fresh,
temporary user directory so `MemoryTree` tests cannot alter normal user
configuration:

```powershell
$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true
$env:QT_QPA_PLATFORM = "offscreen"
$env:NOSE_IGNORE_CONFIG_FILES = "1"
$env:REDPITAYA_HOSTNAME = "_FAKE_"
$env:PYTHONWARNINGS = "error::SyntaxWarning"
$pyrplTestDir = Join-Path ([IO.Path]::GetTempPath()) `
    ("pyrpl-314-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $pyrplTestDir | Out-Null
$env:PYRPL_USER_DIR = $pyrplTestDir

uv lock --check
uv sync --locked --dry-run
uv sync --locked
uv pip check
uv run --no-sync python -m compileall -q -f pyrpl
uv run --no-sync python -m unittest `
    pyrpl.test.test_redpitaya_fpga_loader `
    pyrpl.test.test_python314_compatibility `
    pyrpl.test.test_ipykernel_compatibility
uv run --no-sync nosetests `
    pyrpl/test/test_memory.py `
    pyrpl/test/test_proxyproperty.py `
    pyrpl/test/test_attribute.py
```

The source also passed critical Ruff checks. If Ruff is available in the
review environment, run the same critical family used during migration:

```powershell
uvx ruff check --select E9,F63,F7,F82 pyrpl
```

### Wheel validation

```powershell
uv build --wheel
$wheel = (Get-ChildItem dist -Filter *.whl | Select-Object -First 1).FullName
uv run --no-sync python pyrpl/test/verify_wheel.py $wheel

uv venv .wheel-venv --python 3.14
uv pip install --python .wheel-venv\Scripts\python.exe $wheel
uv pip check --python .wheel-venv\Scripts\python.exe

$wheelPython = (Resolve-Path .wheel-venv\Scripts\python.exe).Path
$wheelCli = (Resolve-Path `
    .wheel-venv\Scripts\sinclair-pyrpl-wwlyn.exe).Path
$outsideSource = Join-Path ([IO.Path]::GetTempPath()) `
    ("pyrpl-wheel-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $outsideSource | Out-Null
Push-Location $outsideSource
try {
    & $wheelPython -c "import importlib.metadata, pathlib, pyrpl, sys; assert pyrpl.__version__ == importlib.metadata.version('sinclair-pyrpl-wwlyn'); assert pathlib.Path(pyrpl.__file__).is_relative_to(pathlib.Path(sys.prefix))"
    & $wheelCli --help
}
finally {
    Pop-Location
}
```

Importing outside the checkout is essential. Otherwise, the repository source
can shadow the installed wheel and turn a packaging failure into a false pass.

The checked-in `.github/workflows/python314.yml` is the automated authority for
this sequence. It pins uv `0.12.0`, uses `windows-latest` and Python 3.14, sets
PowerShell native-command error propagation, and performs the isolated wheel
smoke test.

## Reproduction procedure from the amended 3.9 state

To repeat the upgrade without access to the original conversation:

1. Start a dedicated branch/worktree at the amended 3.9 commit. Confirm the
   3.9 artifact hashes and run its offline loader test first.
2. Change `.python-version`, `requires-python`, and `pyrpl.yml` together to
   3.14. Do not leave a mixed-interpreter declaration.
3. Update dependency bounds to the table above. Replace Quamash with qasync,
   original Nose with Nose NG, and retain `netifaces2`.
4. Apply the NumPy alias migration everywhere in the file inventory. Search
   source, tests, and current docs for active `np.float`, `np.int`, and
   `np.complex` uses.
5. Replace `scipy.misc.derivative` with the documented five-point formula and
   add its numerical regression.
6. Implement the three event-loop modes. Preserve host-loop ownership under
   ipykernel, keep the Qt pump task alive, and reject synchronous nested-loop
   misuse from active Tasks.
7. Normalize Qt timer/geometry integer arguments, use `QPointF` where float
   geometry is intentional, repair return-from-`finally`, and make logging
   teardown explicit.
8. Convert the `Module` metaclass to native Python 3 syntax and verify that no
   direct runtime import depends on undeclared `six`.
9. Make Red Pitaya teardown idempotent without changing FPGA programming or
   signatures.
10. Align distribution version/metadata and keep the root package mapping and
    CLI entry point.
11. Regenerate `uv.lock`; compare direct resolutions and package counts with
    this record. Investigate, rather than silently accepting, material resolver
    drift.
12. Add the focused runtime, actual-kernel, cleanup, wheel, and CI tests.
13. Update current documentation and mark unverified inherited pages as
    historical.
14. Run the full authoritative offline and wheel validation above.
15. Confirm the FPGA artifact hashes are unchanged and do not contact hardware
    unless a separate user request explicitly authorizes live validation.

Searches useful during reconstruction include:

```powershell
rg -n "np\.(float|int|complex)\b|scipy\.misc\.derivative|quamash|Quamash" `
    pyrpl docs
rg -n "start\([0-9]+\.[0-9]+\)|setInterval\([0-9]+\.[0-9]+\)" pyrpl
rg -n "six\.with_metaclass|from six|import six" pyrpl
```

Review matches rather than mechanically replacing historical prose or names
that are intentionally documenting the migration.

## Local environment transition

During the migration, an active project Jupyter kernel still held the old
Python 3.9 `.venv`. It was stopped before the environment was recreated with
Python 3.14.4. Anyone using this checkout must restart notebook kernels after
the upgrade; an old kernel retains already imported code and its old
interpreter even if files and `.venv` change on disk.

`test.ipynb` was not executed or modified during the 3.14 work. It remains the
separate, sensitive live-device notebook inherited from the 3.9 commit.

## Known residual risks and future work

- qasync's Python 3.16-related deprecation warning needs a future dependency
  review; it is not a 3.14 blocker.
- The broader fake HK expansion save/load mismatch remains outside the
  maintained gate.
- Historical Sphinx pages and notebooks remain archival unless individually
  modernized and tested.
- Hardware-coupled behavior has not been revalidated on a physical board for
  3.14. The migration deliberately did not touch FPGA-loading behavior.
- The distribution is validated on Windows AMD64. Other platforms require
  their own resolver/wheel and GUI validation rather than assuming parity.
- PyQt6 migration is separate work; do not mix it into a reproduction of this
  upgrade.

## Commit review and staging checklist

After the user approves and completes the 3.9 amendment:

- Confirm `git log -1` shows the amended 3.9 commit.
- Confirm `.agents/python-3.9-upgrade-changelog.md` is tracked in the parent and
  is not part of the new diff.
- Confirm all 48 files in this record are present in the 3.14 diff.
- Confirm no notebook, FPGA asset, RTL file, user configuration, credential,
  or unrelated branch content was accidentally changed.
- Run `git diff --check`.
- Run the authoritative offline and wheel gates.
- Inspect both `git diff --stat` and `git diff --name-status` before committing.

Do not use a blanket stage command until the 3.9 amendment is complete and the
file boundary has been verified. A reviewer can stage the 3.14 set after that
check, inspect `git diff --cached --name-status`, and commit it as the distinct
CPython 3.14 upgrade.
