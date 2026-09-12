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

The runner was validated with Vivado 2023.2. The test keeps DERIVATIVE=0,
the fork's normal PI configuration. DERIVATIVE=1 was already documented as
non-functional and is not enabled, repaired or validated by this checkpoint.
The enabled prefilter, top-level DIO/manual-pulse routing, CDC/metastability,
full-board clocking, timing closure and analog behavior need separate tests.

The retained Z7010 BIN is not rebuilt. These source contracts and timing
observations do not prove bit-for-bit equivalence to that historical artifact.
