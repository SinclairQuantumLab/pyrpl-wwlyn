# Fork PID RTL contract

This test runs the actual PID, filter and LPF sources in XSim. It does not
simulate a substituted Python model, force internal DUT nets, build a bitstream
or contact a board. It is a development regression, not the end-user live test.

From the repository root, with Vivado tools on PATH:

```text
uv run python pyrpl/fpga/sim/run_pid_contract.py
```

Or select a local installation, for example on Windows:

```powershell
uv run python pyrpl/fpga/sim/run_pid_contract.py --vivado-bin C:/Xilinx/Vivado/2023.2/bin
```

The runner parses the design as Verilog and the testbench as SystemVerilog,
then elaborates/runs the default PID configuration. Each run uses a new
temporary directory (or a new child of `--output-root`). It retains console
logs, source hashes and `result.json` even after a test failure. No existing
build output or packaged asset is overwritten. A zero tool exit status alone
does not count as a pass: XSim can return zero after a testbench `$fatal`.

Covered contracts:

- register acknowledgements and PSR/ISR/gain-width metadata;
- positive/negative P, high gain, output limits and four-clock bypass latency;
- held proportional contribution, I accumulation/hold/release and signed
  integral saturation at -8192/+8191;
- all 16 signed sequence words, last-write readback, index/reset/wrap;
- three-sampled-clock trigger synchronization, one advance per sustained
  high and no falling-edge advance;
- differential input mode.

The same run also checks the actual filter cascade against an integer
fixed-point recurrence model at both sides of each clock edge. Five parameter
families cover the PID, IQ input, four-stage 24-bit IQ quadrature, trigger and
17-bit IIR input prefilter (not the IIR biquad itself). Each family makes 4,096
comparisons over signed rails, impulses, deterministic random samples, resets,
bypass/LPF/HPF switching, mixed cascades and every register-encoded shift,
including the existing MAXSHIFT clamp. State keeps evolving during bypass,
and the model preserves the delta-register delay and truncation/wrap behavior.
The PID bench requires all five filter checkers to finish before reporting its
own pass. No checker forces or reads DUT internal state.

The runner was validated with Vivado 2023.2. The test keeps DERIVATIVE=0,
the fork's normal PI configuration. DERIVATIVE=1 was already documented as
non-functional and is not enabled, repaired or validated by this checkpoint.
The complete PID-with-enabled-filter bus/datapath interaction, full IQ/IIR
modules, top-level DIO/manual-pulse routing, CDC/metastability, full-board
clocking, timing closure and analog behavior still need separate tests.

The retained Z7010 BIN is not rebuilt. These source contracts and timing
observations do not prove bit-for-bit equivalence to that historical artifact.
