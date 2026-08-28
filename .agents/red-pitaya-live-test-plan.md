# Red Pitaya live-test plan

This is the device-ready acceptance plan for the preservation-first Python,
OS-loader, and Z7010 Gen 2 upgrades. No step in this document authorizes board
access by itself. Each session still requires explicit live-device approval.

## Commit map

| Test gate | Candidate commit | Hardware and OS | Status |
| --- | --- | --- | --- |
| Known-good comparison | `407a9d1` | Original STEMlab 125-14 Z7010, OS `1.04-18`, CPython 3.9 | Already field-tested; retain as the comparison and recovery point |
| Python 3.14 acceptance | `c535358` | Original STEMlab 125-14 Z7010, OS `1.04-18` | Pending |
| OS 2, `fpga.bit.bin` contract | `ddb1077` | Original STEMlab 125-14 Z7010, OS 2.07+ whose installed `overlay.sh` fixes `/opt/pyrpl/fpga.bit.bin` | Pending |
| OS 2, `fpga.bin` contract | `ddb1077` | Original STEMlab 125-14 Z7010, OS 2.07+ whose installed `overlay.sh` fixes `/opt/pyrpl/fpga.bin` | Pending |
| Final-branch original-board regression | Gen 2 implementation commit: **TBD** | Original STEMlab 125-14 Z7010, one of the OS 2 images accepted above | Blocked until the current Gen 2 working tree is committed |
| Standard Gen 2 acceptance | Same Gen 2 implementation commit: **TBD** | STEMlab 125-14 Gen 2 Z7010, profile 20 or 31 with `z10_125_v2`, OS 2.07+ | Pending device |
| Pro Gen 2 acceptance | Same Gen 2 implementation commit: **TBD** | STEMlab 125-14 Pro Gen 2 Z7010, profile 21 or 32 with `z10_125_pro_v2`, OS 2.07+ | Pending device; required before claiming Pro support |
| Unsupported-board refusal | Same Gen 2 implementation commit: **TBD** | Z7020 or TI-based Gen 2 board | Optional read-only safety test; never attempt an FPGA load |

`ddb1077` is the test checkout for the committed original-board OS 2 work. It
contains the loader introduced by `10f0e68`, support for both known fixed
firmware basenames added by `7aa600e`, and the read-only preflight added by
`ddb1077`.

Do not assign the Gen 2 gates to a working-tree snapshot. Commit the current
implementation and offline evidence first, then replace every **TBD** above
with that one immutable commit ID before attaching hardware.

## Required order

1. Commit the Gen 2 repository implementation and record its ID here.
2. Test `c535358` on the already-known original Z7010 and OS `1.04-18`. This
   isolates Python 3.14 from all OS 2 and Gen 2 changes.
3. Test `ddb1077` on an original Z7010 with each available OS 2 overlay
   contract. Both contracts are required if both device images can be made
   available.
4. Test the final Gen 2 commit on an original Z7010 running an already-passed
   OS 2 image. This catches regressions introduced by widening the profile
   table.
5. Test that same final commit on a standard Z7010 Gen 2 board.
6. Test it separately on a Pro Z7010 Gen 2 board before claiming the Pro
   profiles field-validated.

A pass at a later gate does not retroactively replace an earlier isolation
gate. In particular, a Gen 2 pass does not prove the author's original-board
behavior was preserved.

## Prepare each session

- Use a separate Git worktree at the exact candidate commit. Do not switch the
  main development tree while it contains uncommitted work.
- Build a fresh CPython 3.14 environment using the commands in `AGENTS.md` and
  run the required offline tests before allowing that worktree to contact a
  board.
- Confirm that `pyrpl/fpga/red_pitaya.bin` has SHA-256
  `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
  For OS 2 also confirm both approved DTBO hashes from `AGENTS.md`.
- Record the board label, Zynq part, ecosystem release, profile ID, profile
  FPGA path, installed `overlay.sh` hash/content, Python version, candidate
  commit, loading configuration, cabling, termination, and test-equipment
  calibration. Do not commit passwords or machine-specific PyRPL config.
- Use a recoverable SD-card image, keep console/recovery access available,
  disconnect experimental actuators, and begin with Red Pitaya outputs
  disconnected. Use a passive loopback or dummy load for the functional test.

For the legacy `1.04-18` load, positively establish that the board is the
original STEMlab 125-14 Z7010 and that `/dev/xdevcfg` is a character device.
The ecosystem version must come from `/opt/redpitaya/version.txt` (version
`1.04`, build `18`), not only `/root/.version`.

For OS 2, first run the packaged read-only command:

```powershell
.venv\Scripts\python.exe -m pyrpl.redpitaya_preflight HOSTNAME
```

The preflight still contacts the device and therefore needs explicit approval.
It must report an exact allowed profile/path pair, Z7010, OS 2.07+, an approved
local BIN and matching DTBO, and one of the two recognized fixed overlay
basenames. A preflight refusal ends the session; do not bypass it.

## Mutating loader acceptance

Only after the preparation and preflight gates pass, make one explicitly
authorized connection with `reloadfpga=True` and `reloadserver=True`. Use a
small sanitized test program or scratch notebook; do not run or rewrite the
tracked `test.ipynb` as a general-purpose acceptance harness.

An OS 2 loader pass requires all of the following:

1. Upload begins only after the local BIN and selected DTBO hashes pass.
2. The selected DTBO `firmware-name` matches the basename fixed inside the
   device's installed `overlay.sh`.
3. The overlay command succeeds without an SSH loss or board reboot.
4. FPGA Manager reports `operating`.
5. `/tmp/update_fpga.txt` reports success and `/tmp/loaded_fpga.inf` identifies
   the expected fork image.
6. The monitor client connects and the fork-specific register metadata check
   is positive.
7. A clean disconnect/reconnect with both reload flags false succeeds.

Preserve the staged files and diagnostics if any condition fails. Do not
automatically retry a failed overlay or loader operation.

## Functional acceptance sequence

Run the same low-energy sequence on the original OS 1 reference, the original
OS 2 targets, and each Gen 2 target so the results can be compared directly.

1. **Basic access:** read identification/register metadata and acquire an idle
   scope trace without exceptions, zero-bandwidth metadata, or obvious clock
   errors.
2. **ASG and fast I/O:** generate a low-amplitude 1 kHz sine into a known-safe
   loopback/load; measure frequency, amplitude, offset, polarity, clipping,
   and scope scaling with calibrated external equipment.
3. **Spectrum:** acquire the same signal and confirm the fundamental frequency
   and amplitude are consistent with the time-domain measurement.
4. **PID/filter path:** use only a passive electrical loop or dummy plant;
   verify small-signal routing, setpoint, sign, gain, saturation, and recovery.
5. **Fork-specific behavior:** exercise the author's triggered-setpoint path
   and confirm timing, trigger polarity, resulting setpoint, and register
   readback against the original-board result.
6. **Slow analog:** test each used slow input/output channel at conservative
   levels and compare offset, gain, polarity, and settling.
7. **Runtime integration:** after the one successful load, verify headless
   script operation, a PyQt/qasync GUI connect-and-close cycle, and a fresh
   Python 3.14 ipykernel connect-and-close cycle with reload disabled.
8. **Stability:** operate the passive test setup for at least 30 minutes, then
   disconnect and reconnect without reprogramming; record exceptions,
   disconnects, and drift.

For Gen 2, record whether OUT1/OUT2 is high impedance or 50 ohms. Measure the
actual DAC full scale and commanded amplitude/offset relationship in both load
conditions that are available. The expected hardware limits are approximately
`+/-2 V` into high impedance and `+/-1 V` into 50 ohms. Do not change PyRPL's
normalization to hide a load-dependent difference. Also verify ADC scaling and
slow analog independently instead of inferring them from a successful load.

## Immediate stop conditions

Stop without retrying or trying a different asset if any of these occurs:

- profile ID, FPGA path, Zynq part, OS version, overlay basename, or local hash
  is missing or mismatched;
- the board is Z7020, TI-based, 4-input, a slave variant, or otherwise outside
  the exact allowed Z7010 profiles;
- `/dev/xdevcfg` is not a character device during a legacy test;
- SSH disappears, uptime resets, the overlay reports failure, FPGA Manager is
  not `operating`, or loaded-image identity is not the fork image;
- fork register metadata fails, measured clocks/frequencies are inconsistent,
  or an output exceeds the planned safe voltage;
- a test would require an FPGA rebuild, a different DTBO, or bypassing a
  preflight refusal.

After a stop, collect only read-only diagnostics until the failure is reviewed.

## Evidence commits after live tests

Keep raw device-specific logs outside Git. Add sanitized measurements,
versions, hashes, cabling/termination, and pass/fail evidence to the applicable
upgrade changelog in a new non-rewriting commit. Suggested commit subjects are:

- `Document Python 3.14 legacy-board field validation`
- `Document original-board OS 2 field validation`
- `Document Z7010 Gen 2 field validation`

If standard and Pro Gen 2 are tested on different dates, use separate evidence
commits and do not mark the untested family field-validated. Never amend an
already-shared implementation commit merely to add later bench evidence.
