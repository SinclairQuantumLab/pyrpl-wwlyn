# Local tool inventory only: no synthesis, bitstream generation or board access.
puts "PYRPL_TOOL_VERSION=[version -short]"
set part [get_parts -quiet xc7z020clg400-1]
if {[llength $part] != 1} { error "Z7020 target device files not installed" }
create_project -in_memory -part $part
puts "PYRPL_PART=$part"
foreach ip {processing_system7 axi_interconnect proc_sys_reset} {
    set matches [get_ipdefs -all -quiet xilinx.com:ip:${ip}:*]
    if {[llength $matches] == 0} { error "Required IP missing: $ip" }
    puts "PYRPL_IP=$matches"
}
puts "PYRPL_PLATFORM_INVENTORY_PASS"
close_project
exit 0
