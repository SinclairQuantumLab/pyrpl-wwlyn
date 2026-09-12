# Read-only timing attribution from an existing checkpoint. No constraint,
# placement, routing, source, checkpoint or bitstream modification.
if {$argc != 2} { error "Specify INPUT_DCP and NEW_REPORT_DIRECTORY" }
set checkpoint [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
if {[file exists $output]} { error "Choose a new report directory" }
file mkdir $output
cd $output
open_checkpoint $checkpoint

proc block_of {name} {
    if {[string match *i_pid/* $name]} { return PID }
    if {[string match *iq_2_outputs/* $name]} { return IQ_TWO_OUTPUT }
    if {[string match *.iq/* $name]} { return IQ }
    if {[string match *iir* $name]} { return IIR }
    if {[string match *pwm* $name]} { return PWM }
    if {[string match *adc_dat* $name]} { return ADC_INPUT }
    if {[string match *i_scope/* $name]} { return SCOPE }
    if {[string match *trigger* $name]} { return TRIGGER }
    if {[string match *i_hk/* $name]} { return HOUSEKEEPING }
    return OTHER
}

set metadata [open [file join $output metadata.txt] w]
puts $metadata "checkpoint=$checkpoint"
puts $metadata "vivado=[version -short]"
puts $metadata "part=[get_property PART [current_design]]"
set first [get_timing_paths -max_paths 1]
puts $metadata "path_properties=[list_property $first]"
close $metadata
report_timing_summary -file [file join $output timing_summary.rpt]
report_timing -delay_type max -max_paths 12 -nworst 1 \
    -file [file join $output worst_setup.rpt]
report_timing -delay_type min -max_paths 4 -nworst 1 \
    -file [file join $output worst_hold.rpt]
report_clocks -file [file join $output clocks.rpt]

set summary [open [file join $output groups.tsv] w]
puts $summary "type\tstart_block\tend_block\tpaths\tworst_slack_ns"
foreach direction {max min} {
    set paths [get_timing_paths -delay_type $direction -slack_lesser_than 0 \
        -max_paths 20000 -nworst 1]
    if {[llength $paths] >= 20000} { error "Increase query cap; findings are truncated" }
    set rows [open [file join $output ${direction}_paths.tsv] w]
    puts $rows "slack_ns\tstart\tend\tstart_block\tend_block"
    set groups [dict create]
    foreach path $paths {
        set start [get_property STARTPOINT_PIN $path]
        set end [get_property ENDPOINT_PIN $path]
        set slack [get_property SLACK $path]
        set from [block_of $start]
        set to [block_of $end]
        puts $rows "$slack\t$start\t$end\t$from\t$to"
        set key [list $from $to]
        if {![dict exists $groups $key]} { dict set groups $key [list 0 $slack] }
        lassign [dict get $groups $key] count worst
        dict set groups $key [list [expr {$count+1}] [expr {min($worst,$slack)}]]
    }
    close $rows
    dict for {key values} $groups {
        lassign $key from to
        lassign $values count worst
        puts $summary "$direction\t$from\t$to\t$count\t$worst"
    }
    puts "ATTRIBUTION_${direction}_PATHS [llength $paths]"
}
close $summary

set pid_cells [get_cells -quiet -hierarchical -filter {NAME =~ *i_pid/* && IS_SEQUENTIAL == 1}]
if {![llength $pid_cells]} { error "No PID sequential cells found" }
report_timing -to $pid_cells -delay_type max -max_paths 12 -nworst 1 \
    -file [file join $output pid_destinations.rpt]
report_timing -from $pid_cells -to $pid_cells -delay_type max -max_paths 12 -nworst 1 \
    -file [file join $output pid_internal.rpt]
set adc_cells [get_cells -quiet -hierarchical -filter {NAME =~ adc_dat* && IS_SEQUENTIAL == 1}]
report_timing -from $adc_cells -to $pid_cells -delay_type max -max_paths 4 -nworst 1 \
    -file [file join $output adc_to_pid.rpt]
close_design
puts "SHARED_TIMING_ATTRIBUTION_COMPLETE (reports only)"
exit 0
