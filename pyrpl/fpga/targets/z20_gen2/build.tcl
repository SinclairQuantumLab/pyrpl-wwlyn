# Full-fork development checkpoint, not a load-ready FPGA artifact generator.
# Usage: vivado -mode batch -source build.tcl -tclargs NEW_OUTPUT_DIR ?bd|synth|implement?
if {$argc < 1 || $argc > 2} { error "Specify a new output directory and optional stage" }
set stage [lindex $argv 1]
if {$stage eq ""} { set stage synth }
if {$stage ni {bd synth implement}} { error "Unknown stage: $stage" }
if {[version -short] ne "2023.2"} { error "This target is pinned to Vivado 2023.2" }
set target_dir [file normalize [file dirname [info script]]]
set fpga_root [file normalize [file join $target_dir ../..]]
set output [file normalize [lindex $argv 0]]
if {[file exists $output]} { error "Output already exists; choose a new directory" }
file mkdir $output
cd $output
create_project z20_gen2 [file join $output project] -part xc7z020clg400-1
source [file join $target_dir system_bd.tcl]
set bd [get_files system.bd]
set_property generate_synth_checkpoint false $bd
generate_target all $bd
set wrapper [make_wrapper -files $bd -top]
add_files $wrapper
write_bd_tcl [file join $output generated_system_bd.tcl]
if {$stage eq "bd"} { close_project; exit 0 }

# Explicit original-fork source list. No alternate official top/DSP is read.
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
} {
    read_verilog [file join $fpga_root rtl $name]
}
foreach name {red_pitaya_pll.sv red_pitaya_pwm.sv} {
    read_verilog -sv [file join $fpga_root rtl $name]
}
read_xdc [file join $target_dir board.xdc]
set_property top red_pitaya_top [current_fileset]
update_compile_order -fileset sources_1
synth_design -top red_pitaya_top -flatten_hierarchy none
write_checkpoint [file join $output post_synth.dcp]
report_utilization -file [file join $output post_synth_utilization.rpt]
report_timing_summary -file [file join $output post_synth_timing.rpt]
report_drc -file [file join $output post_synth_drc.rpt]
set black_boxes [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]
if {[llength $black_boxes]} { error "Unresolved black boxes: $black_boxes" }
if {[llength [get_cells -hier -filter {REF_NAME == XADC}]] != 1} {
    error "Expected exactly the fork's one direct XADC primitive"
}
puts "PYRPL_Z7020_FULL_SYNTHESIS_PASS"
if {$stage eq "implement"} {
    opt_design
    place_design
    phys_opt_design
    route_design
    write_checkpoint [file join $output post_route.dcp]
    report_utilization -file [file join $output post_route_utilization.rpt]
    report_timing_summary -file [file join $output post_route_timing.rpt]
    report_drc -file [file join $output post_route_drc.rpt]
    report_cdc -file [file join $output post_route_cdc.rpt]
    report_clock_interaction -file [file join $output post_route_clock_interaction.rpt]
    report_methodology -file [file join $output post_route_methodology.rpt]
    report_io -file [file join $output post_route_io.rpt]
    puts "PYRPL_Z7020_ROUTING_FINISHED_REVIEW_REPORTS"
}
# Deliberately no write_bitstream/write_cfgmem or loader enablement at this stage.
close_project
exit 0
