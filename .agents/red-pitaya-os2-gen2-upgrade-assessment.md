# Red Pitaya OS 2 and Gen 2 upgrade assessment

Assessment branch: `develop/red-pitaya-upgrade`

Baseline: `c535358` (`Upgrade the fork to Python 3.14`)

This document records the pre-implementation offline investigation. It did not
contact a Red Pitaya, execute the live notebook, change the packaged bitstream,
create a DTBO, or run Vivado. The subsequently authorized OS 2 implementation
and its still-pending live gates are recorded separately in
`.agents/red-pitaya-os2-upgrade-changelog.md`.

## Outcome

The repository can realistically be extended to Red Pitaya OS 2. OS 2 support
for the author's original STEMlab 125-14 should not require changing the
fork-specific FPGA signal-processing RTL or rebuilding its bitstream. It does
require replacing the unsafe legacy loading path with OS-aware FPGA Manager
integration and producing or otherwise proving a device-tree overlay that
matches this exact fork image.

OS 2 also has two loading eras. Official documentation assigns OS 2.00 through
2.05-37 to direct `fpgautil` use and OS 2.07-43 or newer to `overlay.sh` (with
bitstream-only `fpgautil` still available). The recommended first target here
is a pinned OS 2.07 release; claiming all OS 2 versions would require testing
both paths.

"Gen 2" is not one hardware target. The expected effort depends on the exact
model:

| Target | Expected FPGA-side depth | Assessment |
| --- | --- | --- |
| Original STEMlab 125-14 (Z7010) on OS 2 | Device-tree/loader integration; no DSP RTL change expected | Practical next target |
| STEMlab 125-14 or 125-14 PRO Gen 2 (Z7010) | Board-profile validation; potentially no bitstream rebuild | Plausible, but requires bench validation |
| STEMlab 125-14 PRO Z7020 Gen 2 | Significant platform port and rebuild; preserve/adapt custom RTL | Bounded engineering project, not a complete rewrite |
| TI-based Gen 2 variants | Converter/platform redesign and new drivers | Major specialist project; not a preservation-first upgrade |

OS 2 plus a Gen 2 board combines the OS-loader work with the corresponding
board row. OS version alone never proves FPGA compatibility.

## Local evidence

### The current loader is legacy-only

`pyrpl/redpitaya.py` uploads the image as `/opt/pyrpl/fpga.bin` and executes a
shell redirection to `/dev/xdevcfg`. It neither detects the ecosystem release
nor invokes `/opt/redpitaya/sbin/overlay.sh`, supplies a DTBO, or verifies FPGA
Manager state.

That path is appropriate to the author's recorded OS 1.04-18 environment, but
it is unsafe on OS 2. If `/dev/xdevcfg` is absent, root shell redirection can
create a regular file and report no shell error without programming the FPGA.
OS 2 support must positively choose the modern path and must never fall back to
that behavior.

The earlier modern-loader implementation and tests on this repository's
`main` branch are useful reference material. They include fixed OS-specific
filenames, missing-DTBO refusal, FPGA Manager checks, `/dev/xdevcfg` character
device validation, and invalid FPGA-metadata failures. They should be reviewed
and selectively ported rather than merged wholesale.

### The existing BIN is not inherently a legacy-only format

The fork image is 2,083,740 bytes and has SHA-256
`dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
Its configuration sync word and `SMAPx32`/no-bit-swap generation convention
match the kind of BIN consumed by the modern Red Pitaya loading tools. There is
no static evidence that OS 2 alone requires a new bitstream or a format
conversion.

This conclusion is deliberately narrower than saying the image is already
validated on OS 2: only a controlled device test can establish that.

### A maintained/upstream DTBO is not proven to match this fork

The maintained PyRPL overlay configures the four fabric clocks (125, 250, 50,
and 200 MHz), AXI fabric interfaces, and an AXI XADC Wizard at `0x83c00000`.
This fork instead instantiates the 7-series `XADC` primitive directly in
`pyrpl/fpga/rtl/red_pitaya_ams.v` and exposes its values through the fork's own
register bus. The XADC IP creation, interrupt, and `0x83c00000` address segment
are commented out in `pyrpl/fpga/ip/system_bd.tcl`.

The Tcl file still contains one live reference to `xadc/s_axi_aclk`, and the
tracked implementation report shows one XADC resource. This is a build-source
provenance inconsistency that must be resolved by regenerating and inspecting
the implemented design in the pinned Vivado flow. It is not justification for
using an unrelated overlay.

A safe OS 2 implementation therefore needs a source-controlled, decompilable
fork DTBO (probably clocks and required fabric interfaces, without a fictional
AXI XADC node), generated from and validated against the actual implemented
design. Bitstream-only loading while retaining an already active device tree
is technically possible in some Red Pitaya workflows, but it is not a safe or
reproducible default for this repository.

### A rebuild carries real risk

The existing project targets `xc7z010clg400-1` with Vivado 2015.4. Its saved
post-route utilization is 86.75% of LUTs, 97.11% of slices, 56.67% of block
RAM, 45% of DSPs, and 93% of bonded I/O. More importantly, the saved timing
summary says constraints are not met: WNS is -4.094 ns, TNS is -6951.330 ns,
and 8,093 endpoints fail setup timing; hold WNS is -2.163 ns.

The original image is field-tested, but these reports mean that a fresh image
cannot be accepted merely because Vivado generated a bitstream. Any rebuild
needs constraint review, timing closure or a documented and technically
defensible exception, equivalence checks, and hardware tests. Preserving the
known image is the lower-risk OS 2 strategy.

## Gen 2 detail

### Z7010 Gen 2

The standard and PRO STEMlab 125-14 Gen 2 models retain a Zynq-7010 and the
same basic two-channel 14-bit 125 MS/s converter class. The current official
PyRPL project uses the same constraint content for its normal and Gen 2 Z7010
builds. An external PyRPL report also found that copying the original Z7010
PyRPL image/overlay for explicit loading on a Z7010 PRO Gen 2 board allowed
quick ASG, scope, and spectrum-analyzer tests.

That is strong evidence for reuse, not proof for this custom image. Before
loading it, verify the exact model identifier, FPGA part, PS clock setup, pin
constraints, analog calibration representation, and the scope of unsupported
Gen 2-only connector/features. Then run the fork-specific PID and triggered
setpoint tests, not only generic PyRPL smoke tests.

### Z7020 Gen 2

A Z7010 bitstream cannot be loaded into a Z7020. Current Red Pitaya FPGA
sources provide a PyRPL Z7020 Gen 2 platform script and top-level wrapper, so
this is not a greenfield rewrite. The realistic port is to use that maintained
platform shell and transplant the fork behavior deliberately.

Relative to the current official PyRPL RTL, 22 local RTL files are identical
and nine active files differ, with 676 added and 189 removed lines. The
differing area includes the custom PID/setpoint sequence, DSP trigger routing,
AMS/XADC, IIR, trigger, housekeeping, top-level, product saturation, and AXI
FIFO logic. Those changes and their Python register contract must be audited
and preserved while adapting the processing-system wrapper and build target.

This is significant FPGA refactoring plus verification, but it is bounded and
does not call for rewriting the control algorithms from scratch. Official
documentation and OS-image asset availability have not always agreed on
Z7020 PyRPL support, so it must be treated as a separately qualified target.

### TI converter variants

The TI-based Gen 2 boards use different high-speed converter hardware and
supporting software. They are not a pin-compatible Z7010/Z7020 retarget of this
fork. Supporting them would require a new converter interface/platform layer,
driver integration, calibration work, timing closure, and full bench
qualification. That is outside the scope of a conservative port.

## Realistic AI-agent capability

| Work | General-purpose AI feasibility | Human/hardware requirement |
| --- | --- | --- |
| OS-aware loader, defensive checks, and offline tests | High | Review and one controlled board test |
| Derive/audit a fork DTBO from source and generated design | High with the exact toolchain | FPGA engineer approves the implemented design and live result |
| Z7010 Gen 2 static compatibility review and software integration | Moderate to high | Exact board and analog/function bench tests are mandatory |
| Z7020 platform port | Moderate as an AI-assisted engineering project | Vivado, exact hardware, recovery media, lab equipment, and experienced FPGA review |
| TI variant port | Low for a general-purpose agent acting alone | Converter/FPGA specialist and substantial lab work |

An AI agent can write and review loader code, compare RTL/Tcl/XDC, construct
tests, drive Vivado noninteractively, and triage build reports. It cannot infer
electrical safety from a successful compile, measure analog behavior, prove
that an undocumented bitstream matches a board, or responsibly certify timing
and hardware behavior without the toolchain and physical validation. The
Z7020 work is realistic for AI assistance, not as an autonomous one-shot
upgrade.

## Recommended sequence and acceptance gates

1. **Original Z7010 on a pinned OS 2.07 image (implemented offline).**
   Preserve the exact fork BIN.
   Add capability-based OS detection, the fixed OS 2 staging filename
   `/opt/pyrpl/fpga.bit.bin`, overlay invocation, status/diagnostic capture,
   server checks, and offline regression tests. Do not rely only on
   `/root/.version`; this fork's known legacy image reports inconsistent
   version numbers, so also inspect `/opt/redpitaya/version.txt` and loader
   capabilities.
2. **Produce and audit the fork DTBO (source-level implementation complete).**
   The source-derived overlay preserves the implemented clocks and fabric
   interfaces and omits the unimplemented AXI XADC. It is decompilable and
   hash-pinned. Because the historical BIN is not reproducibly rebuildable,
   it was not replaced by a new Vivado output; hardware validation remains the
   final proof for the preserved BIN/overlay pair.
3. **Controlled OS 2 field validation (pending).** Confirm model/profile before
   upload;
   keep recovery media available. Require overlay success, FPGA Manager state
   `operating`, useful `/tmp/update_fpga.txt` and `/tmp/loaded_fpga.inf`
   diagnostics, monitor-server connection, valid fork register/signature
   metadata, and functional ASG/scope/PID/setpoint tests. Stop retrying if SSH
   disappears and determine whether the board rebooted.
4. **Z7010 Gen 2 validation.** Only after static model/pin/clock proof, test the
   unchanged image and matching overlay on the exact Gen 2 profile. Include
   calibration and analog tests and state which Gen 2-specific features the
   PyRPL image does not expose.
5. **Optional Z7020 project.** Create a separate FPGA-port branch, pin a modern
   RedPitaya-FPGA and Vivado version, adapt the nine changed RTL areas to the
   Z7020 Gen 2 shell, generate a matched BIN/DTBO pair, close timing, and run
   simulation plus complete hardware regression.

## Sources checked

- Red Pitaya FPGA loading by OS version:
  <https://redpitaya.readthedocs.io/en/latest/developerGuide/fpga/getting_started/reprogram_fpga.html>
- OS 2 overlay utility and fixed project paths:
  <https://redpitaya.readthedocs.io/en/latest/appsFeatures/command_line_tools/utils/overlay_util.html>
- Advanced FPGA Manager loading and bitstream-only option:
  <https://redpitaya.readthedocs.io/en/latest/developerGuide/fpga/advanced/fpga_advanced_loading.html>
- Device-tree purpose and generation:
  <https://redpitaya.readthedocs.io/en/latest/developerGuide/fpga/advanced/device_tree.html>
- Gen 2 hardware identification and Z7010 model:
  <https://redpitaya.readthedocs.io/en/latest/developerGuide/hardware/GEN2/125-14_Gen2/top.html>
- Supported applications/model notes:
  <https://redpitaya.readthedocs.io/en/latest/appsFeatures/supportedFeaturesAndApps.html>
- Current Red Pitaya FPGA source:
  <https://github.com/RedPitaya/RedPitaya-FPGA>
- Gen 2 PyRPL field report and maintainer discussion:
  <https://github.com/pyrpl-fpga/pyrpl/issues/586>

Repository comparisons were pinned during this investigation to maintained
PyRPL commit `4d87d093d78dd3275f43974f8a150a80f4a2adeb`, RedPitaya-FPGA
Release-2026.1 commit `09b44cecfc0faae36c8fa0c4f404251424b9af6d`, and Red Pitaya
ecosystem Release-2025.2 commit `54561fd`.
