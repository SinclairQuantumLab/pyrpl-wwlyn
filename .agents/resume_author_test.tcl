# Resume only the original-RTL synthesis checkpoint; no source/constraint edits.
if {$argc != 2} { error "Specify POST_SYNTH_DCP and NEW_OUTPUT_DIR" }
if {[version -short] ne "2023.2"} { error "Requires Vivado 2023.2" }
set checkpoint [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
set export_script [file normalize [file join [file dirname [info script]] \
    ../pyrpl/fpga/targets/z20_gen2/export_author_test.tcl]]
if {[file exists $output]} { error "Output directory already exists" }
file mkdir $output
cd $output
open_checkpoint $checkpoint
if {[get_property PART [current_design]] ne "xc7z020clg400-1"} {
    error "Incorrect FPGA part"
}
opt_design
place_design
phys_opt_design
write_checkpoint post_place.dcp
route_design
write_checkpoint post_route.dcp
report_utilization -file post_route_utilization.rpt
report_timing_summary -file post_route_timing.rpt
report_drc -file post_route_drc.rpt
report_cdc -file post_route_cdc.rpt
report_clock_interaction -file post_route_clock_interaction.rpt
report_methodology -file post_route_methodology.rpt
report_io -file post_route_io.rpt
report_timing -delay_type max -max_paths 12 -nworst 1 -file worst_setup.rpt
report_timing -delay_type min -max_paths 4 -nworst 1 -file worst_hold.rpt
close_design
set argv [list [file join $output post_route.dcp] [file join $output image]]
source $export_script
