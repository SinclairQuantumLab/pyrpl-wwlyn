# Per-root PID/filter repair rollout — 2026-09-12

## Applied flow

Each `genX-osY` root now has its own develop integration line and a
`fix/pid-rtl-shadowing` topic. Existing feature/refactor/fix refs and mains
were retained; none was renamed, deleted, rebased or force-updated.
Future root topics integrate through `root/develop`, then `root/main` after
the root's release/field criteria. Global develop remains the cross-root
integration branch and was not advanced by this isolated rollout.

The source merge checkpoint is `14117e3`: functional fixes through `43a9764`
plus shared guidance and original-Z7010 timing investigation. The root fixes
retain the same common commit ancestry, not copied code/cherry-picked copies.

| Root | New develop | New fix topic merge | Develop seed |
| --- | --- | --- | --- |
| `gen1-os1` | `d7d19c9` | `e438a95` | Existing root main. |
| `gen1-os2` | `784a1fc` | `4c6f95c` | Main `efa5a00`, with existing topic `183b5be` reconciled. |
| `gen2-os2` | `3fc4307` | `aa48bbb` | Existing standard Gen 2 candidate. |
| `gen2-pro-os2` | `ef7f1c1` | `a551d28` | Existing Pro candidate. |

The Gen1/OS2 ancestry reconciliation produced an identical tree to its main;
the topic had an equivalent notebook-policy change under another commit.
All other existing root topics were already ancestors of their selected seed.
Their histories are therefore represented without importing unrelated work.

The repair topics are NOT merged back into root develops or mains. That
integration step remains for an explicit request. No Gen2/Pro main was created.
The old Pro candidate/develop already contained earlier PID declaration and
shadowing fixes; its new fix topic adds the remaining filter/pause-net repair.

## Per-root validation

The agent-only `validate_root_rollout.py` executed each suite in a temporary
checkout, with offscreen Qt, fake device hostname and isolated user config.
It used normal uv sync/run, without locked/frozen flags, and never executed
the user notebook or contacted hardware.

| Root | Python files compiled | Checkout + fresh-wheel unittests (each) | Safe Nose tests | Wheel entries |
| --- | ---: | ---: | ---: | ---: |
| Gen1/OS1 | 112 | 13 | 21 | 147 |
| Gen1/OS2 | 114 | 37 | 21 | 153 |
| Gen2/OS2 | 116 | 57 | 28 | 153 |
| Gen2 Pro/OS2 | 117 | 63 | 28 | 153 |

- Every root independently passed the real XSim contract: 342 PID checks and
  20,480 filter comparisons. Source identity was verified against common
  `14117e3` for the entire RTL and simulation trees.
- Every root passed fresh Python 3.14 wheel installation, dependency checks
  and an actual ipykernel regression outside the checkout. Checkout-only
  source guards used that root's checkout; runtime imports used the fresh wheel.
- OS2 roots also ran loader regressions; Gen2 roots additionally ran PID-write
  and clean-template guards; Pro additionally ran its build-source guards.
- Original BIN SHA-256 remained
  `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
  OS2 wheels retain exactly the two approved DTBOs and matching DTS files.
  OS1 gained no DTBO. Simulation is source-archive-only; no Pro target leaked
  into the other roots, and the Pro runtime wheel still excludes target files.
- Root loader/preflight code, dependency lock, Python selection, pin/PS/target
  settings, BIN/DTS/DTBO assets and each root's notebook/template were checked
  unchanged against its develop seed. Only the common source fixes/tests and
  the simulation wheel exclusion (where previously absent) affect product files.
- Conflicts occurred only in AGENTS.md. Root-specific scope, loader/Pro test
  requirements and ignored-notebook policies were retained alongside shared
  repair/branching policy. No product-code conflict required an alternative fix.
- Per-root evidence is also committed as `.agents/pid-repair-application.md`
  on each new fix topic.

Full local logs, result manifests, simulation outputs, wheels/source archives
and fresh validation environments remain under
`TEMP/pyrpl-root-rollout-642432c1/{gen1-os1,gen1-os2,gen2-os2,gen2-pro-os2}`.
The disposable `worktree` child is removed after verification; recorded test
paths identify the checkout used at validation time. No user checkout is
removed. The root validator itself compiled with SyntaxWarning treated as error.

## Preserved state and remaining work

Global main `dcd4805`, global develop `2703645`, Gen1/OS1 main `d7d19c9`,
Gen1/OS2 main `efa5a00`, all old root topic refs and the restored
`working-vs1` checkout at `d3a2405` remain unchanged. No push was performed.
The main working directory remains on common `fix/pid-rtl-shadowing`.
Its local notebook stays unstaged and retains SHA-256
`9769f6beee473a990a8a2d1b36cd500fa3b367066d38bca1b2f96757d65ed9f7`.

This propagates SOURCE repairs. It does not generate/deploy a replacement
image, establish timing closure, rerun the Pro full build or advance field
acceptance. The original-Z7010 timing investigation and each port's separate
pending gates remain as documented. This aggregate report/validator commit
is bookkeeping after the root merges, not additional unapplied RTL changes.
