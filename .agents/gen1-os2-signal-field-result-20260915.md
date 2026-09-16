# Gen 1 / OS 2 signal-bench observations — 2026-09-15

The user reports that all notebook tests passed. This record distinguishes
saved observations from manually entered measurement notes and that report.
The agent reviewed the saved notebook and its plotted PNG without executing
cells or contacting the board.

## Identity and preservation

- Checkout: `gen1-os2/main`, `efa5a00`.
- Local dependency differences: `ipykernel>=7.3.0` added to runtime dependencies
  with a uv lock refresh; these do not change RTL or the bitstream.
- Board: `192.168.50.155`, profile 2 / `z10_125` / Z7010, OS reported `2.07-3`.
- Original BIN SHA-256:
  `dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed`.
- Overlay SHA-256:
  `41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9`.
- Byte-identical notebook backup, including user settings, notes, outputs and
  plot: `.agents/local-notebooks/test-gen1-os2-signals-20260915.ipynb`.
- Notebook SHA-256:
  `400175e08399579287d9a6c6acd2f81cacfdac2340f1554b8f3ed00bac604ccb`.

The full notebook remains ignored. Its saved factory-default password is
permitted by the user and is preserved locally, not copied into this record.

## Reviewed results

| Test | Saved evidence |
| --- | --- |
| Preflight | Correct original-board profile, OS 2 overlay and local hashes |
| Programming | `PYRPL_OVERLAY_OK`, FPGA Manager `operating`, correct loaded identity; board log reports 52 ms |
| Image identity | Remote MD5 `445d5fbae304d4ccc7bb5af30e849967` matches the local original BIN |
| Connection / register read | PyRPL connection and fork register checks passed; PID0 input filter `[0, 0, 0]` |
| DC source | PID0 OUT1, P=I=0, adjustable `ival`; PID1 reads IN1 with no direct output |
| Triangle loopback | ASG0 ramp (triangle in this fork), amplitude 0.4, offset 0, saved setting **1 Hz**; 5,000 IN1 readings and a saved repeating triangle plot |
| PID | P=0, I=-150000, limits -1/+1, input IN1 / output OUT1; raw setpoint 0.43310546875 maps through the entered IN1 fit to 0.5000540351562499 V |
| Shutdown | ASG0/1, PID0/1/2 and IQ0/1/2 direct outputs report `off` |

The saved triangle readback statistics in PyRPL units are:

- Mean: 0.050696728515625
- Minimum: -0.3548583984375
- Maximum: 0.4505615234375
- Peak-to-peak: 0.805419921875

The plot visibly contains repeated triangular cycles. Its horizontal axis is
sample index, not elapsed time. Sleep plus SSH overhead does not establish a
uniform 0.5 ms sample interval or measured waveform frequency.

## Manual calibration notes and limits of the record

The notebook's Markdown records commands `[-0.5, -0.25, 0, 0.25, 0.5]` and
Rigol voltages `[-0.572, -0.282, 0.00567, 0.284, 0.572]` V, with entered fits:

```text
V_rigol = 1.14142 * V_rp_output + 0.001534
V_rigol = 1.14380 * V_rp_in1    + 0.004668
```

It reports approximately +14.14% output gain difference, +1.53 mV output
intercept and 2.69 mV RMS residual. The full paired RP-readback sweep is not
saved, so these are recorded as the notebook's manual fit, not independently
recomputed coefficients. No library calibration was changed. These values
belong to this board/channel/cabling/probe/termination/jumper configuration;
they must not be applied to Gen 2 Pro as its calibration.

The dynamic Markdown describes 1 kHz and additional amplitudes, but the retained
code sets `asg.frequency = 1` and amplitude 0.4. This API uses Hz. The next
repeat therefore uses **1 Hz**, not 1 kHz; the old aliasing explanation cannot
be attributed to this retained 1 Hz run. Mean/midrange offsets are observations,
not proof of zero offset or calibration accuracy.

The PID cell's corrected 0.500054 V is a calculated setpoint, not a saved
external-voltmeter measurement. The ASG remains routed to OUT1 during that
cell, so it is a summed disturbance for the PID to reject, not an isolated
PID-only output test. Successful physical response is the user's report;
no external PID trace, bandwidth or settling-time measurement is saved.

There are no saved Python error outputs. The shutdown message for absent
`rp.iir` is a caught missing-module skip, not a failed FPGA operation.
TTL sequence/hold timing, slow analog, all filter modes and long-duration
performance are not covered by these cells. The broader historical gate 6
is not declared fully closed by this narrower signal-bench result.

## Next repeat

Use the original-logic Pro candidate at `779a031`, not a common-repair topic.
Retain the same DC levels, 1 Hz triangle amplitude 0.4 and negative-I feedback
test. Capture fresh paired DC readings and fit the Pro board independently;
record termination/jumper/instrument settings. Keep the ASG-as-disturbance
condition explicit. Do not silently rescale the driver's units or change RTL.
