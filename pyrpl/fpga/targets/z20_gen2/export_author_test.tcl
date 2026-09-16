# Export an explicitly experimental author-logic baseline from a routed DCP.
# No board access, timing/DRC waivers, clock changes or overwrite of old output.
# Usage: vivado ... -source export_author_test.tcl -tclargs INPUT_DCP NEW_OUTPUT
if {$argc != 2} { error "Specify the original-RTL routed checkpoint and a NEW output directory" }
if {[version -short] ne "2023.2"} { error "This target is pinned to Vivado 2023.2" }
set checkpoint [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
if {[file exists $output]} { error "Output already exists; choose a new directory" }
file mkdir $output
cd $output
open_checkpoint $checkpoint
if {[get_property PART [current_design]] ne "xc7z020clg400-1"} {
    error "Not the Z7020 Gen 2 Pro target"
}
report_route_status -file route_status.rpt
report_timing_summary -file timing_summary.rpt
report_drc -ruledeck bitstream_checks -file bitstream_drc.rpt
# Keep normal Vivado bitstream DRC enforcement. No severity overrides.
write_bitstream red_pitaya_z20_gen2_author.bit
set bif [open image.bif w]
puts $bif "all: { red_pitaya_z20_gen2_author.bit }"
close $bif
close_design
puts "AUTHOR_BASELINE_BIT_EXPORTED_NOT_TIMING_SIGNOFF"
exit 0
