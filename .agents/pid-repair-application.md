# Shared PID/filter repair application: gen2-os2

- Root develop baseline: `3fc4307`, the existing standard Gen 2 candidate.
- Fix topic: `gen2-os2/fix/pid-rtl-shadowing`.
- Merge source: common `14117e3`; functional repair checkpoint `43a9764`,
  including earlier declaration/shadowing fixes `8794f01` and `c596274`.
- All RTL and simulation sources match common exactly. Root-specific loader,
  approved BIN/DTS/DTBO pair, pin/PS settings, dependency lock and notebook
  template remain unchanged. No Pro platform source/profile is imported.
- Agent-guidance conflicts were resolved by keeping the standard candidate's
  scope, notebook and loader test rules while adding common repair policy.
- Offline validation: plain uv sync, 116 Python compilations, 57 unittests
  including loader/PID-write/template tests and a real ipykernel, 28 safe
  Nose tests, actual XSim 342 PID checks plus 20,480 filter comparisons,
  and 57 fresh-wheel tests passed.
- The 153-entry wheel retains the exact BIN/two approved DTBOs and matching
  DTS sources. Simulation assets are source-archive-only and byte-checked.
- Retained local evidence: `TEMP/pyrpl-root-rollout-642432c1/gen2-os2`.
- No image generation/load, timing closure claim, physical acceptance,
  main creation/promotion or merge of this fix into root develop occurred.
