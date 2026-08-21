# Upgrade runbooks

This directory contains detailed, historical records for substantial changes
to this PyRPL fork. It exists so a maintainer or an AI agent can reconstruct
why the repository is in its current state, distinguish one upgrade from the
next, and repeat an upgrade without relying on conversational history.

Read [`../AGENTS.md`](../AGENTS.md) first. It is the authoritative concise set
of current working rules, safety constraints, and supported-environment
decisions. These runbooks preserve the chronological and per-file detail that
would make `AGENTS.md` too large.

## Upgrade records

- [`python-3.9-upgrade-changelog.md`](python-3.9-upgrade-changelog.md) records
  the completed CPython 3.9, packaging, and Red Pitaya modern-OS migration.
  It is deliberately standalone because the user intends to add only that file
  to the existing 3.9 commit by amending it.
- [`python-3.14-upgrade-changelog.md`](python-3.14-upgrade-changelog.md)
  records the subsequent CPython 3.14 migration, including NumPy 2, qasync,
  ipykernel, packaging metadata, tests, CI, and known residual risks.

## Commit-boundary rule

The two records belong to different commits:

1. Amend the existing `Upgraded to python 3.9` commit with only
   `.agents/python-3.9-upgrade-changelog.md`.
2. Commit `.agents/README.md`, `.agents/python-3.14-upgrade-changelog.md`, the
   `AGENTS.md` link, and all Python 3.14 implementation/test/documentation
   changes together in the following commit.

Do not add this index to the 3.9 amendment. The 3.9 changelog has no dependency
on the index and remains readable by itself.

The original, pre-amendment 3.9 commit ID was
`adbca0a7dd7d023638f1d16133b38ad26094845f`. Amending it necessarily gives it
a new ID and rebases the uncommitted 3.14 work onto that new parent. Treat the
commit ID recorded here as reconstruction evidence, not as the permanent
release identifier.

## Documentation hygiene

- Never add passwords, private configuration, tokens, or machine-specific
  notebook values to a runbook.
- Record exact commands, versions, file inventories, limitations, and failed
  exploratory checks when they affect reproducibility.
- Distinguish offline tests from explicitly authorized physical-device tests.
- If an exact source artifact cannot be reconstructed from a public provenance
  reference, preserve its digest and identify the release commit containing
  the byte-for-byte copy.
- Update a historical runbook only to correct a factual error or add missing
  evidence. Put new current constraints in `AGENTS.md`.
