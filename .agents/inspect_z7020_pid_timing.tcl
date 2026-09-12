# Read-only analysis of an existing offline checkpoint; no synthesis or load.
if {$argc != 2} { error "Specify INPUT_DCP and NEW_REPORT_DIRECTORY" }
set checkpoint [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
if {[file exists $output]} { error "Choose a new report directory" }
file mkdir $output
cd $output
open_checkpoint $checkpoint
set pid_cells [get_cells -hier -filter {NAME =~ *i_pid/* && IS_SEQUENTIAL == 1}]
if {![llength $pid_cells]} { error "No PID sequential cells found" }
puts "PID_SEQUENTIAL_CELLS [llength $pid_cells]"
report_timing -to $pid_cells -delay_type max -max_paths 12 -nworst 1 \
    -file [file join $output pid_destinations_setup.rpt]
report_timing -from $pid_cells -to $pid_cells -delay_type max -max_paths 12 -nworst 1 \
    -file [file join $output pid_to_pid_setup.rpt]
report_timing -to $pid_cells -delay_type min -max_paths 4 -nworst 1 \
    -file [file join $output pid_destinations_hold.rpt]
foreach direction {max min} {
    set path [get_timing_paths -to $pid_cells -delay_type $direction -max_paths 1]
    if {![llength $path]} { error "No $direction PID timing path found" }
    puts "PID_${direction}_SLACK [get_property SLACK $path]"
    puts "PID_${direction}_START [get_property STARTPOINT_PIN $path]"
    puts "PID_${direction}_END [get_property ENDPOINT_PIN $path]"
}
close_design
exit 0
