# Export a separate test candidate, using the original Z7010 BIN conversion.
if {$argc != 2} { error "Specify INPUT_DCP and NEW_OUTPUT" }
if {[version -short] ne "2023.2"} { error "Pinned to Vivado 2023.2" }
set checkpoint [file normalize [lindex $argv 0]]
set output [file normalize [lindex $argv 1]]
if {[file exists $output]} { error "Choose a NEW output directory" }
file mkdir $output
cd $output
open_checkpoint $checkpoint
if {[get_property PART [current_design]] ne "xc7z010clg400-1"} {
    error "Not the original Gen1 Z7010 target"
}
report_route_status -file route_status.rpt
report_clocks -file clocks.rpt
report_timing_summary -file timing_summary.rpt
report_drc -ruledeck bitstream_checks -file bitstream_drc.rpt
set_property BITSTREAM.GENERAL.COMPRESS FALSE [current_design]
write_bitstream red_pitaya_z10_gen1_repaired.bit
write_cfgmem -format BIN -size 2 -interface SMAPx32 -disablebitswap \
    -loadbit "up 0x0 red_pitaya_z10_gen1_repaired.bit" red_pitaya_z10_gen1_repaired.bin
close_design
puts "REPAIRED_Z7010_CANDIDATE_EXPORTED_NOT_TIMING_SIGNOFF"
exit 0
