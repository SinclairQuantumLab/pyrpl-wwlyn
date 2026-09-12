# Compatibility branching model

This repository separates common development from the device/OS combinations
that have independent commissioning evidence.

## Common development

`develop` is the common integration line. Work that is not tied to one Red
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
- `gen2-pro-os2/...` for the Z7010 Gen 2 Pro profile on supported OS 2.

Within a root, use the same topic types, for example
`gen1-os2/feature/os-upgrade` or `gen2-os2/fix/device-profile`.

`<root>/main` is reserved for a commissionable combination. A branch whose
live-device gate is incomplete remains a feature candidate and must not be
represented as a commissioned `main`.

## Propagation

Apply a common change at the earliest applicable common line and merge it
forward:

```text
topic branch -> develop -> compatibility feature -> compatibility main
```

Prefer merge commits so the same commit identity and ancestry are preserved.
Use `git cherry-pick -x` only when a deliberately isolated backport is needed
and merging would import unrelated or incompatible changes. Never rebase a
published compatibility `main` or rewrite its validation history.

## Imported history

The existing commits through `c8355a5` predate this naming model and remain
unchanged. New names and merge commits organize that history without replaying
or rewriting it. In particular:

- `387faf3` is the author-fork baseline;
- `ddb1077` is the last OS 2 implementation commit before Gen 2 support;
- `80b6291` and `c8355a5` are the current Z7010 Gen 2 candidate changes.

The old remote `origin/develop/*` references are retained until an explicit
remote migration is authorized.
