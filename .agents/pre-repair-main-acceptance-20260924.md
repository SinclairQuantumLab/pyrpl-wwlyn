# Device/OS mains: acceptance of the pre-repair baselines

## Authority and evidence

On 2026-09-24 the user confirmed that all four device/OS combinations had
already been tested with actual devices and worked well, and explicitly
requested their promotion to the corresponding mains before adopting the
shared PID/filter repairs. This is user-reported field acceptance, not a new
agent-run test or a claim that every possible profile/operating condition was
tested. No board was contacted, programmed or restarted for this promotion.

The date above records the confirmation, not an inferred date for the tests.
No new per-board measurements, exact executed commit IDs or additional OS
versions were supplied with that confirmation. The snapshots below identify
the selected original-logic release baselines; they are not newly verified
records of the precise working trees used in every experiment.

## Selected baselines

| Main | Source snapshot before acceptance documentation | Selection |
| --- | --- | --- |
| `gen1-os1/main` | `3eacfe2454d5b70e91a75eab4490d0c2f4b373ee` | Existing main; identical to pre-repair develop. |
| `gen1-os2/main` | `1141c3206a8fb10f23710f7503bab6a46aa535ca` | Existing main with the newer Gen1 signal record; reconcile pre-repair develop `20f2229` without changing product files. |
| `gen2-os2/main` | `926feee21010f8c0075a2d72228c23ce2cec266b` | Original-logic standard Gen2 device-upgrade candidate; also pre-repair develop. |
| `gen2-pro-os2/main` | `7cb67e263c3643cb09f2580fcf666502381ffcf7` | Original-logic Pro device-upgrade candidate, not the older partially repaired Pro develop. |

All four selected RTL trees match author checkpoint
`387faf3012c21925c9905d81a95cb681ac7d1b22`. The original Z7010 BIN remains
`dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
Pro retains the separately built original-logic Z7020 image
`red_pitaya_z20_gen2_author.bit.bin`, SHA-256
`f6728daaf863f6c48a1d8b27a7262d7fb7653c489f37db36acd6cbb9cc4a7307`,
for exact profile 22 / `z20_125_v2` / Z7020. No profile whitelist, FPGA image,
overlay, loader, dependency or notebook changes are part of this promotion.

## Gen1 OS2 ancestry is not a missing runtime update

Pre-repair develop contains `784a1fc` (topic-history reconciliation) and
`183b5be` (notebook/template policy) outside main's ancestry. Main already has
equivalent notebook/product contents. Conversely, main contains `8c6f4df`,
the newer Gen1 signal-bench record. Reconciling these histories must retain
that evidence; the pre-repair merge has exactly main's existing tree.

The earlier Gen1 local `ipykernel`/lock edits remain separately preserved in
stash `f01b7ed`; the Gen1 field record identifies those working-tree differences.
They are not missing changes from pre-repair develop and are not silently
applied by this promotion.

## Scope of acceptance

This confirmation supersedes older pending-field-test / no-main statements
for these selected baselines. Historical logs and build-provenance JSON retain
their original statements about what had been tested at the time. Previously
recorded Gen1 signal observations and the Pro loading/register-read record
remain evidence of their respective scopes, not expanded retroactively into
new measurements. Gen2 standard and the later Pro functional success are
recorded here as the user's confirmation.

Timing remains an open finding whose hardware relevance and need for changes
are not established by this promotion. Acceptance does not imply timing
closure, passing untouched-source XSim, historical BIN equivalence or proof
across all temperatures, voltages, boards and modes.

The four develops retain their separate shared-repair merges (`7e137eb`,
`4f4c472`, `19e0617`, `0702cc1`). These repaired sources are NOT promoted to
main. Pro develop additionally lacks later original-logic candidate platform
updates; reconciling those with repaired development is separate work. No
develop/main history is rewritten and no remote is pushed here.
