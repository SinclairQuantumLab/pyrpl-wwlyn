# Fresh original-Gen1 Z7010 build, using the repaired fork RTL unchanged.
# Usage: vivado ... -source build.tcl -tclargs NEW_OUTPUT ?bd|synth|implement?
if {$argc < 1 || $argc > 2} { error "Specify NEW_OUTPUT and optional stage" }
if {[version -short] ne "2023.2"} { error "Pinned to Vivado 2023.2" }
set stage [lindex $argv 1]
if {$stage eq ""} { set stage synth }
if {$stage ni {bd synth implement}} { error "Invalid stage" }
set target_dir [file normalize [file dirname [info script]]]
set fpga_root [file normalize [file join $target_dir ../..]]
set output [file normalize [lindex $argv 0]]
if {[file exists $output]} { error "Choose a NEW output directory" }
file mkdir $output
cd $output
create_project z10_gen1 [file join $output project] -part xc7z010clg400-1
source [file join $target_dir system_bd.tcl]
set bd [get_files system.bd]
set_property generate_synth_checkpoint false $bd
generate_target all $bd
add_files [make_wrapper -files $bd -top]
write_bd_tcl [file join $output generated_system_bd.tcl]
if {$stage eq "bd"} { close_project; exit 0 }
foreach name {
    axi_master.v axi_slave.v axi_wr_fifo.v bus_clk_bridge.v
    red_pitaya_ams.v red_pitaya_asg_ch.v red_pitaya_asg.v red_pitaya_dfilt1.v
    red_pitaya_hk.v red_pitaya_pid_block.v red_pitaya_dsp.v red_pitaya_ps.v
    red_pitaya_scope.v red_pitaya_top.v red_pitaya_adv_trigger.v
    red_pitaya_saturate.v red_pitaya_product_sat.v red_pitaya_iir_block.v
    red_pitaya_iq_modulator_block.v red_pitaya_lpf_block.v red_pitaya_filter_block.v
    red_pitaya_iq_demodulator_block.v red_pitaya_pfd_block.v
    red_pitaya_iq_fgen_block.v red_pitaya_iq_block.v red_pitaya_trigger_block.v
    red_pitaya_prng.v
} { read_verilog [file join $fpga_root rtl $name] }
foreach name {red_pitaya_pll.sv red_pitaya_pwm.sv} {
    read_verilog -sv [file join $fpga_root rtl $name]
}
read_xdc [file join $target_dir board.xdc]
set_property top red_pitaya_top [current_fileset]
update_compile_order -fileset sources_1
# Preserve the author's synthesis/implementation options, unlike the Pro target.
synth_design -top red_pitaya_top -flatten_hierarchy none -bufg 16 -keep_equivalent_registers
write_checkpoint [file join $output post_synth.dcp]
report_utilization -file post_synth_utilization.rpt
report_timing_summary -file post_synth_timing.rpt
report_drc -file post_synth_drc.rpt
if {[llength [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]]} { error "Black boxes remain" }
if {[llength [get_cells -hier -filter {REF_NAME == XADC}]] != 1} { error "Expected one direct XADC" }
if {$stage eq "implement"} {
    opt_design
    power_opt_design
    place_design
    phys_opt_design
    route_design
    write_checkpoint post_route.dcp
    report_utilization -file post_route_utilization.rpt
    report_timing_summary -file post_route_timing.rpt
    report_drc -file post_route_drc.rpt
    report_cdc -file post_route_cdc.rpt
    report_clock_interaction -file post_route_clock_interaction.rpt
    report_methodology -file post_route_methodology.rpt
    report_io -file post_route_io.rpt
    puts "PYRPL_Z7010_ROUTED_REVIEW_REPORTS"
}
close_project
exit 0
