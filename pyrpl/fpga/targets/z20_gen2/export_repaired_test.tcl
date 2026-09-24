# Separately export the user-authorized repaired-source Z7020 test candidate.
# Usage: vivado ... -source export_repaired_test.tcl -tclargs INPUT_DCP NEW_OUTPUT
# No timing exceptions, severity overrides, overwrite or device operations.
if {$argc != 2} { error "Specify the repaired routed checkpoint and a NEW output directory" }
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
write_bitstream red_pitaya_z20_gen2_repaired.bit
set bif [open image.bif w]
puts $bif "all: { red_pitaya_z20_gen2_repaired.bit }"
close $bif
close_design
puts "REPAIRED_CANDIDATE_EXPORTED_NOT_TIMING_SIGNOFF"
exit 0
