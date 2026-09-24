# Agent-only source check for the original Z7010 part. No image generation.
if {[version -short] ne "2023.2"} { error "Evidence requires Vivado 2023.2" }
if {$argc != 1} { error "Usage: -tclargs NEW_OUTPUT_DIRECTORY" }
set output [file normalize [lindex $argv 0]]
if {[file exists $output]} { error "Refusing to reuse output directory: $output" }
set repo [file normalize [file join [file dirname [info script]] ..]]
file mkdir $output
cd $output
create_project -in_memory -part xc7z010clg400-1
foreach name {red_pitaya_lpf_block.v red_pitaya_filter_block.v red_pitaya_pid_block.v} {
    read_verilog [file join $repo pyrpl fpga rtl $name]
}
synth_design -top red_pitaya_pid_block -part xc7z010clg400-1 -mode out_of_context
create_clock -name pid_clk -period 8.000 [get_ports clk_i]
if {[llength [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]] != 0} {
    error "Unresolved black boxes in PID synthesis"
}
write_checkpoint [file join $output pid_synth.dcp]
report_utilization -file [file join $output utilization.rpt]
report_timing_summary -file [file join $output timing_estimate.rpt]
puts "COMMON_PID_SYNTH_PASS Z7010; no routing, I/O constraints or timing-closure claim"
