# Shared PID/filter repair application: gen2-pro-os2

- Root develop baseline: `ef7f1c1`, the existing Pro development candidate.
- Fix topic: `gen2-pro-os2/fix/pid-rtl-shadowing`.
- Merge source: common `14117e3`; new functional repair checkpoint `43a9764`.
  Earlier PID declaration/shadowing repairs were already in this root's
  baseline and are not duplicated as unrelated cherry-picks.
- All RTL and simulation sources match common exactly. Pro PS/AXI target,
  loader, preserved BIN/DTS/DTBO pair, pin/PS settings, dependency lock and
  notebook template remain at the root baseline.
- The only conflict was notebook guidance; the root's local ignored copy and
  clean tracked template policy were retained. Pro validation rules remain.
- Offline validation: plain uv sync, 117 Python compilations, 63 unittests
  including loader/PID-write/template/Pro-source guards and real ipykernel,
  28 safe Nose tests, actual XSim 342 PID checks plus 20,480 filter comparisons,
  and 63 fresh-wheel tests passed.
- The 153-entry wheel retains the exact BIN/two approved DTBOs and matching
  DTS sources; simulation/target sources remain excluded. Source-archive
  simulation assets were inspected byte-for-byte.
- Retained local evidence: `TEMP/pyrpl-root-rollout-642432c1/gen2-pro-os2`.
- No Pro synthesis/routing rerun, image generation/load, timing closure claim,
  physical acceptance, main creation/promotion or fix-to-develop merge occurred.
  The existing Pro timing findings remain open and its loader still rejects Z7020.
