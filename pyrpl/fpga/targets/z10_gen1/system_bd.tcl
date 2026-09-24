# Recreate the author's Z7010 BD with Vivado 2023.2, not the Pro PS shell.
# The original ip/system_bd.tcl stays untouched. Each adaptation is explicit.
set legacy [file join [file dirname [info script]] ../../ip/system_bd.tcl]
set handle [open $legacy r]
set source [read $handle]
close $handle
set source [string map [list \
    {set scripts_vivado_version 2015.4} {set scripts_vivado_version 2023.2} \
    {CONFIG.ID_WIDTH {0}} {CONFIG.ID_WIDTH {6}} \
    {[get_bd_pins xadc/s_axi_aclk]} {} \
] $source]
regsub -line {^CONFIG.PCW_IRQ_F2P_INTR[^\n]*\n} $source {} source
# The wrapper already provides all four BUFGs; do not insert duplicates in IP.
# Retain the original MIO, DDR, GP1/converter/reset topology and address map.
set injection {
  set_property -dict [list CONFIG.PCW_FCLK_CLK0_BUF FALSE \
      CONFIG.PCW_FCLK_CLK1_BUF FALSE CONFIG.PCW_FCLK_CLK2_BUF FALSE \
      CONFIG.PCW_FCLK_CLK3_BUF FALSE] [get_bd_cells processing_system7]
  foreach index {0 1} {
      set_property CONFIG.ASSOCIATED_BUSIF S_AXI_HP$index [get_bd_ports S_AXI_HP${index}_aclk]
  }
}
set source [string map [list {  save_bd_design} "$injection\n  validate_bd_design\n  save_bd_design"] $source]
eval $source
puts "PYRPL_Z7010_LEGACY_DERIVED_BD_REVIEW"
