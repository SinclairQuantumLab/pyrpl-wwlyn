# Shared PID/filter repair application: gen1-os1

- Root develop baseline: `d7d19c9` (`gen1-os1/main`), unchanged by this fix.
- Fix topic: `gen1-os1/fix/pid-rtl-shadowing`.
- Merge source: common `14117e3`; functional repair checkpoint `43a9764`,
  including earlier declaration/shadowing fixes `8794f01` and `c596274`.
- All RTL and simulation sources match the common source exactly. Legacy
  loader, preserved BIN, pin/PS settings, dependency lock and notebook remain
  at the root baseline. No OS2 assets or Pro platform code were imported.
- Offline validation: plain uv sync, 112 Python compilations, 13 unittests
  including a real ipykernel, 21 safe Nose tests, actual XSim 342 PID checks
  plus 20,480 filter comparisons, and 13 fresh-wheel unittests passed.
- The 147-entry wheel retains the exact BIN and has no DTBO/simulation files;
  source archive simulation assets were inspected byte-for-byte.
- Retained local evidence: `TEMP/pyrpl-root-rollout-642432c1/gen1-os1`.
- Source repair only: no bitstream rebuild/load, timing closure claim,
  hardware test, main promotion or merge of this fix into root develop.
