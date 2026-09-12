# Z7020 module-level synthesis checkpoint. This is NOT a full board build.
# vivado -mode batch -source synth_pid.tcl -tclargs NEW_OUTPUT_DIRECTORY
if {$argc != 1} { error "Specify a new output directory" }
if {[version -short] ne "2023.2"} {
    error "This reproducible module checkpoint targets Vivado 2023.2"
}
set fpga_root [file normalize [file join [file dirname [info script]] ../..]]
set output [file normalize [lindex $argv 0]]
if {[file exists $output]} { error "Output already exists; choose a new directory" }
file mkdir $output
cd $output
create_project -in_memory -part xc7z020clg400-1
foreach source {red_pitaya_lpf_block.v red_pitaya_filter_block.v red_pitaya_pid_block.v} {
    read_verilog [file join $fpga_root rtl $source]
}
synth_design -top red_pitaya_pid_block -mode out_of_context -flatten_hierarchy rebuilt
create_clock -name pid_clk -period 8.000 [get_ports clk_i]
write_checkpoint pid_post_synth.dcp
report_utilization -file pid_post_synth_utilization.rpt
report_timing_summary -file pid_post_synth_timing.rpt
puts "PYRPL_Z7020_PID_SYNTHESIS_PASS"
# No placement/routing, PS wrapper, I/O constraints or bitstream generation.
close_project
exit 0
