# Packaged hardware artifacts

This fork's DSP behavior is defined by the preserved
`pyrpl/fpga/red_pitaya.bin`. Do not replace it with an official PyRPL image or
a new local build. Its SHA-256 is:

```text
dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed
```

The author produced that image for an original-generation STEMlab 125-14 with
a Zynq-7010 on Red Pitaya OS 1.04-18. Its complete reproducible-build
provenance is unavailable.

For Red Pitaya OS 2.07+, this fork packages two source-derived companion
overlays. They are identical except for the firmware basename required by the
installed Red Pitaya `overlay.sh`:

| file | purpose |
| --- | --- |
| `red_pitaya_os2_z10.dts` | source using historical OS 2 `fpga.bit.bin` |
| `red_pitaya_os2_z10.dtbo` | compiled `fpga.bit.bin` overlay; SHA-256 `41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9` |
| `red_pitaya_os2_z10_fpga_bin.dts` | source using newer OS 2 `fpga.bin` |
| `red_pitaya_os2_z10_fpga_bin.dtbo` | compiled `fpga.bin` overlay; SHA-256 `99f0fd0c3ce394fb0c86e4dec95895b8a5855cc80ebbfd5fedc961fb9ed4a35c` |

The overlay enables the implemented fabric clocks and AXI interfaces. It does
not contain the AXI XADC node found in maintained PyRPL: this fork instantiates
the Zynq `XADC` primitive directly in `rtl/red_pitaya_ams.v` and exposes it
through the PyRPL register map. Each BIN/DTBO pair is restricted in software to
exact Z7010 ecosystem profile/path pairs: original profiles 1 and 2
(`z10_125`), standard Gen 2 profiles 20 and 31 (`z10_125_v2`), and Pro Gen 2
profiles 21 and 32 (`z10_125_pro_v2`). It is not approved for Z7020, another
converter family, early OS 2, or OS 3.

No FPGA artifact was changed for Gen 2 support. Red Pitaya's own ecosystem
build matrix selects the same `MODEL=Z10` FPGA build for all three Z7010 path
families, and its published Gen 2 development schematic preserves the FPGA
package pins used by this image. The remaining field-validation boundary is
electrical and functional, especially the Gen 2 DAC stage: full scale is
+/-2 V into high impedance or +/-1 V into 50 ohms. Software must not silently
rescale the fork's register contract based on board generation because it
cannot detect the attached load.

# Directory structure

|  path           | contents
|-----------------|-------------------------------------------------------------
| `fpga/Makefile` | main Makefile, used to run FPGA related tools
| `fpga/*.tcl`    | TCL scripts to be run inside FPGA tools
| `fpga/archive/` | archive of XZ compressed FPGA bit files
| `fpga/doc/`     | documentation (block diagrams, address space, ...)
| `fpga/ip/`      | third party IP, for now Zynq block diagrams
| `fpga/rtl/`     | Verilog (SystemVerilog) "Register-Transfer Level"
| `fpga/sdc/`     | "Synopsys Design Constraints" contains Xilinx design constraints
| `fpga/red_pitaya_os2_z10*.dts` | sources for the OS 2.07+ Z7010 overlays

# Build process

Xilinx Vivado 2015.4 (including SDK) is required. If installed at the default location, then the next command will properly configure system variables:
```bash
. /opt/Xilinx/Vivado/2015.4/settings64.sh
```

The default mode for building the FPGA is to run a TCL script inside Vivado. Non project mode is used, to avoid the generation of project files, which are too many and difficult to handle. This allows us to only place source files and scripts under version control.

The next scripts perform various tasks:

| TCL script                      | action
|---------------------------------|---------------------------------------------
| `red_pitaya_vivado_project.tcl` | creates a Vivado project for graphical editing
| `red_pitaya_vivado.tcl`         | creates the bitstream and reports

To generate a new bit file and reports, run these two commands:
```bash
source /opt/Xilinx/Vivado/2015.4/settings64.sh
make
```

This produces a new hardware artifact; it must not silently replace the
hash-pinned fork image.

# OS 2 device-tree overlay

Device tree is used by Linux to describe features and address space of memory mapped hardware attached to the CPU.

On OS 2.07+, `overlay.sh` loads both the FPGA image and its DTBO. Historical
releases stage custom firmware as `fpga.bit.bin`; newer ecosystem source uses
`fpga.bin`. Because `fpgautil` copies the input basename into
`/lib/firmware`, the overlay's `firmware-name` must match. PyRPL inspects the
installed script and selects the corresponding tracked variant. An unfamiliar
contract is rejected before upload.

Both sources declare four fabric clocks at 125, 250, 50, and 200 MHz and the
HP0/HP1 fabric interfaces. They do not replace the board's complete base device
tree.

Rebuild only the overlay with Device Tree Compiler 1.7.2 or an explicitly
validated equivalent:

```bash
make os2-dtbo
sha256sum red_pitaya_os2_z10.dtbo
sha256sum red_pitaya_os2_z10_fpga_bin.dtbo
```

The expected hashes are recorded above. The two DTS files must remain identical
except for `firmware-name`. `dtc` emits address-cell
warnings for the AFI overlay nodes; decompiling the tracked result confirms the
intended nodes. Any semantic or binary change requires hardware review and a
new controlled field validation.

# Signal mapping

## XADC inputs

In this fork, PyRPL accesses XADC input data through the direct XADC primitive
and its custom register map. The Linux IIO filenames below describe the
historical board device-tree interface; the OS 2 fork overlay does not add an
AXI XADC/IIO device.

| E2 con | schematic | ZYNQ p/n | XADC in | IIO filename     | measurement target | range |
|--------|-----------|----------|---------|------------------|--------------------|-------|
| AI0    | AIF[PN]0  | B19/A20  | AD8     | in_voltage11_raw | general purpose    | 7.01V |
| AI1    | AIF[PN]1  | C20/B20  | AD0     | in_voltage9_raw  | general purpose    | 7.01V |
| AI2    | AIF[PN]2  | E17/D18  | AD1     | in_voltage10_raw | general purpose    | 7.01V |
| AI3    | AIF[PN]3  | E18/E19  | AD9     | in_voltage12_raw | general purpose    | 7.01V |
|        | AIF[PN]4  | K9 /L10  | AD      | in_voltage0_raw  | 5V power supply    | 12.2V |

### Input range

The default mounting intends for unipolar XADC inputs, which allow for observing only positive signals with a saturation range of *0V ~ 1V*. There are additional voltage dividers use to extend this range up to the power supply voltage. It is possible to configure XADC inputs into a bipolar mode with a range of *-0.5V ~ +0.5V*, but it requires removing R273 and providing a *0.5V ~ 1V* common voltage on the E2 connector.

**NOTE:** Unfortunately there is a design error, where the XADC input range in unipolar mode was thought to be *0V ~ 0.5V*. Consequently the voltage dividers were miss designed for a range of double the supply voltage.

#### 5V power supply

```
                         -------------------0  Vout
           ------------  |  ------------
 Vin  0----| 56.0kOHM |-----| 4.99kOHM |----0  GND
           ------------     ------------
```
Ratio: 4.99/(56.0+4.99)=0.0818
Range: 1V / ratio = 12.2V

#### General purpose inputs

```
                         -------------------0  Vout
           ------------  |  ------------
 Vin  0----| 30.0kOHM |-----| 4.99kOHM |----0  GND
           ------------     ------------
```
Ratio: 4.99/(30.0+4.99)=0.143
Range: 1V / ratio = 7.01


## GPIO LEDs

| LED     | color  | SW driver       | dedicated meaning
|---------|--------|-----------------|----------------------------------
| `[7:0]` | yellow | RP API          | user defined
| `  [8]` | yellow | kernel `MIO[0]` | CPU heartbeat (user defined)
| `  [9]` | reg    | kernel `MIO[7]` | SD card access (user defined)
| ` [10]` | green  | none            | "Power Good" status
| ` [11]` | blue   | none            | FPGA programming "DONE"

For now only LED8 and LED9 are accessible using a kernel driver. LED [7:0] are not driven by a kernel driver, since the Linux GPIO/LED subsystem does not allow access to multiple pins simultaneously.

### Linux access to GPIO

This document is used as reference: http://www.wiki.xilinx.com/Linux+GPIO+Driver

The base value of `MIO` GPIOs was determined to be `906`.
```bash
redpitaya> find /sys/class/gpio/ -name gpiochip*
/sys/class/gpio/gpiochip906
```

GPIOs are accessible at base value + MIO index:
```bash
echo 906 > /sys/class/gpio/export
echo 913 > /sys/class/gpio/export
```

### Linux access to LED

This document is used as reference: http://www.wiki.xilinx.com/Linux+GPIO+Driver

By providing GPIO/LED details in the device tree, it is possible to access LEDs using a dedicated kernel interface.
NOTE: only LED 8 and LED 9 support this interface for now.

To show CPU load on LED 9 use:
```bash
echo heartbeat > /sys/class/leds/led9/trigger
```
To switch LED 8 on use:
```bash
echo 1 > /sys/class/leds/led8/brightness
```
