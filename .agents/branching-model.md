# Compatibility branching model

This repository separates common development from the device/OS combinations
that have independent commissioning evidence.

## Common development

`develop` is an optional common integration line. Work that is not tied to one Red
Pitaya hardware/OS combination uses a conventional topic branch:

- `feature/<topic>` for new functionality;
- `fix/<topic>` for a defect correction;
- `refactor/<topic>` for behavior-preserving restructuring or modernization.

The CPython and uv modernization is retained on
`refactor/python-upgrade` and merged into `develop` with an explicit merge
commit.

## Compatibility roots

Device- or OS-specific development is named under the target root:

- `gen1-os1/...` for the original Z7010 STEMlab 125-14 on legacy OS 1;
- `gen1-os2/...` for the original Z7010 STEMlab 125-14 on supported OS 2;
- `gen2-os2/...` for the standard Z7010 Gen 2 profile on supported OS 2;
- `gen2-pro-os2/...` for the Pro candidate on supported OS 2, including its
  separately authorized, not-yet-load-ready Z7020 port.

Each root has its own ordinary Git development flow. Use `root/develop` to
integrate that root's `feature/*`, `fix/*` and `refactor/*` topics, then promote
validated work to `root/main`. For example, `gen1-os2/fix/device-profile`
merges into `gen1-os2/develop`, not directly into an unrelated root.
Keep topic branches for distinct work; "integration in develop" does not
mean renaming all topics to develop or losing their separate provenance.

`<root>/main` is reserved for a commissionable combination. A branch whose
live-device gate is incomplete remains a feature candidate and must not be
represented as a commissioned `main`.

## Propagation

Merge a ready, focused common topic directly into each authorized
`<root>/develop`, using an explicit merge commit naming the update and target.
Global `develop` is optional when several shared changes need integration;
it is not a mandatory intermediate step. Inspect incoming ancestry to avoid
unrelated changes. Use a root-specific topic only for adaptation, substantial
conflict resolution or separate development/validation. Promotion to each
`<root>/main` remains a separately authorized acceptance step.

The 2026-09-24 integration merges `fix/pid-rtl-shadowing` at `e747916` into
the four root develops. The earlier local per-root repair topics were removed;
do not recreate them automatically. Historical rollout evidence below is
retained, not a current instruction to recreate those branches. No global
develop, compatibility main, image or remote ref is advanced by this merge.

Use `git cherry-pick -x` for intentionally selective backports that must not
import unrelated source-branch history. Never rewrite published main history.

## Classification of port findings

Discovery during a device upgrade does not make a change device-specific.
Existing shared RTL defects use a `fix/*` topic from `develop`; toolchain
compatibility prerequisites can be isolated commits on that topic. Changes
required by board, OS or interface differences stay under that device root.

Keep timing findings unclassified until their causes are established. A port
does not authorize PID/filter redesign, extra latency or lowered clocks.
Merging a shared source repair does not authorize a new packaged BIN or
automatic promotion of any compatibility main.

## Imported history

### Root-develop initialization — 2026-09-12

| Root | Starting point for develop | Reason |
| --- | --- | --- |
| `gen1-os1` | `gen1-os1/main` at `d7d19c9` | Current original-board/OS1 main. |
| `gen1-os2` | `gen1-os2/main` at `efa5a00` | Current promoted OS2 main; also reconcile `183b5be` topic ancestry without changing its identical tree. |
| `gen2-os2` | `gen2-os2/feature/device-upgrade` at `3fc4307` | Latest offline candidate; no field-approved main yet. |
| `gen2-pro-os2` | `gen2-pro-os2/feature/device-upgrade` at `ef7f1c1` | Latest Pro candidate; no field-approved main yet. |

The first common repair source checkpoint is `43a9764`, including its earlier
PID declaration/shadowing prerequisites. Later guidance/evidence commits on
that topic do not change the FPGA implementation. Existing root topic refs
are retained, and no remotes, published history or user worktree are removed.

The existing commits through `c8355a5` predate this naming model and remain
unchanged. New names and merge commits organize that history without replaying
or rewriting it. In particular:

- `387faf3` is the author-fork baseline;
- `ddb1077` is the last OS 2 implementation commit before Gen 2 support;
- `80b6291` and `c8355a5` are the current Z7010 Gen 2 candidate changes.

The old remote `origin/develop/*` references are retained until an explicit
remote migration is authorized.
