# Vivado 2023.2 PS-only shell for the preserved red_pitaya_ps.v interface.
# No AXI XADC, extra GPIO, HP2/HP3, or imported maintained PyRPL datapath.
source [file join [file dirname [info script]] ps_config.tcl]
create_bd_design system
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 processing_system7]
configure_fork_ps7 $ps

foreach {name mode vlnv} {
    DDR Master xilinx.com:interface:ddrx_rtl:1.0
    FIXED_IO Master xilinx.com:display_processing_system7:fixedio_rtl:1.0
    M_AXI_GP0 Master xilinx.com:interface:aximm_rtl:1.0
    S_AXI_HP0 Slave xilinx.com:interface:aximm_rtl:1.0
    S_AXI_HP1 Slave xilinx.com:interface:aximm_rtl:1.0
} {
    set external [create_bd_intf_port -mode $mode -vlnv $vlnv $name]
    if {$name in {M_AXI_GP0 S_AXI_HP0 S_AXI_HP1}} {
        set width [expr {$name eq "M_AXI_GP0" ? 32 : 64}]
        set id_width [expr {$name eq "M_AXI_GP0" ? 12 : 6}]
        set_property -dict [list CONFIG.PROTOCOL AXI3 CONFIG.ADDR_WIDTH 32 \
            CONFIG.DATA_WIDTH $width CONFIG.FREQ_HZ 125000000] $external
        # Master ID width is propagated from PS7 and is read-only externally.
        if {$mode eq "Slave"} { set_property CONFIG.ID_WIDTH $id_width $external }
    }
    connect_bd_intf_net $external [get_bd_intf_pins processing_system7/$name]
}
foreach {name pin bus} {
    M_AXI_GP0_ACLK M_AXI_GP0_ACLK M_AXI_GP0
    S_AXI_HP0_aclk S_AXI_HP0_ACLK S_AXI_HP0
    S_AXI_HP1_aclk S_AXI_HP1_ACLK S_AXI_HP1
} {
    set clock [create_bd_port -dir I -type clk -freq_hz 125000000 $name]
    set_property CONFIG.ASSOCIATED_BUSIF $bus $clock
    connect_bd_net $clock [get_bd_pins processing_system7/$pin]
}
foreach index {0 1 2 3} {
    set clock [create_bd_port -dir O -type clk FCLK_CLK$index]
    connect_bd_net $clock [get_bd_pins processing_system7/FCLK_CLK$index]
    set reset [create_bd_port -dir O -type rst FCLK_RESET${index}_N]
    set_property CONFIG.POLARITY ACTIVE_LOW $reset
    connect_bd_net $reset [get_bd_pins processing_system7/FCLK_RESET${index}_N]
}

create_bd_addr_seg -range 0x40000000 -offset 0x40000000 \
    [get_bd_addr_spaces processing_system7/Data] [get_bd_addr_segs M_AXI_GP0/Reg] SEG_fork_registers
foreach index {0 1} {
    create_bd_addr_seg -range 0x20000000 -offset 0x0 \
        [get_bd_addr_spaces S_AXI_HP$index] \
        [get_bd_addr_segs processing_system7/S_AXI_HP$index/HP${index}_DDR_LOWOCM] SEG_hp${index}_ddr
}
validate_bd_design
save_bd_design

# Assertions use generated interface metadata, not guessed wrapper widths.
foreach {bus width id_width} {M_AXI_GP0 32 12 S_AXI_HP0 64 6 S_AXI_HP1 64 6} {
    set port [get_bd_intf_ports $bus]
    foreach {key expected} [list DATA_WIDTH $width ID_WIDTH $id_width PROTOCOL AXI3] {
        set actual [get_property CONFIG.$key $port]
        if {$actual ne $expected} { error "$bus $key: expected $expected, got $actual" }
    }
}
if {[llength [get_bd_cells -quiet -hier -filter {VLNV =~ *xadc*}]]} {
    error "The fork uses a direct XADC primitive, not an AXI XADC IP"
}
puts "PYRPL_Z7020_PS_SHELL_PASS"
