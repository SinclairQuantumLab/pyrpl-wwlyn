# Shared PID/filter repair application: gen1-os2

- Root develop baseline: `784a1fc`, reconciling `efa5a00` main and the
  equivalent `183b5be` topic. That ancestry merge changes no file content.
- Fix topic: `gen1-os2/fix/pid-rtl-shadowing`.
- Merge source: common `14117e3`; functional repair checkpoint `43a9764`,
  including earlier declaration/shadowing fixes `8794f01` and `c596274`.
- All RTL and simulation sources match common exactly. OS2 loader, approved
  BIN/DTS/DTBO pair, pin/PS settings, dependency lock and notebook template
  remain at the root baseline. No other device profile or platform is imported.
- The only conflict was agent guidance: retain the root's ignored-notebook
  policy and OS2 loader tests, and add the shared real-RTL requirements.
- Offline validation: plain uv sync, 114 Python compilations, 37 unittests
  including loader tests/real ipykernel, 21 safe Nose tests, actual XSim
  342 PID checks plus 20,480 filter comparisons, and 37 fresh-wheel tests passed.
- The 153-entry wheel contains the exact BIN/two approved DTBOs and matching
  DTS sources; simulation assets are source-archive-only and byte-checked.
- Retained local evidence: `TEMP/pyrpl-root-rollout-642432c1/gen1-os2`.
- No bitstream rebuild/load, timing closure claim, hardware test, main
  promotion or merge of this fix into root develop was performed.
