# PS configuration derived from this fork's ip/system_bd.tcl at 6e76d87.
# Keep MIO/DDR provenance explicit: legacy 16-bit DDR, 512 MiB PL aperture.
# This is NOT an FSBL/boot-image configuration or a claim to use all Pro RAM.
# Disable the abandoned GP1/AXI-XADC path; retain GP0 and HP0/HP1.
# red_pitaya_ps.v already instantiates the four FCLK BUFGs.
proc configure_fork_ps7 {ps} {
    set_property -dict [list \
        CONFIG.PCW_ENET0_ENET0_IO {MIO 16 .. 27} \
        CONFIG.PCW_ENET0_GRP_MDIO_ENABLE {1} \
        CONFIG.PCW_ENET0_PERIPHERAL_CLKSRC {IO PLL} \
        CONFIG.PCW_ENET0_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_EN_CLK1_PORT {1} \
        CONFIG.PCW_EN_CLK2_PORT {1} \
        CONFIG.PCW_EN_CLK3_PORT {1} \
        CONFIG.PCW_EN_RST1_PORT {1} \
        CONFIG.PCW_EN_RST2_PORT {1} \
        CONFIG.PCW_EN_RST3_PORT {1} \
        CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {125} \
        CONFIG.PCW_FPGA1_PERIPHERAL_FREQMHZ {250} \
        CONFIG.PCW_FPGA3_PERIPHERAL_FREQMHZ {200} \
        CONFIG.PCW_GPIO_MIO_GPIO_ENABLE {1} \
        CONFIG.PCW_I2C0_I2C0_IO {MIO 50 .. 51} \
        CONFIG.PCW_I2C0_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_MIO_16_PULLUP {disabled} \
        CONFIG.PCW_MIO_16_SLEW {fast} \
        CONFIG.PCW_MIO_17_PULLUP {disabled} \
        CONFIG.PCW_MIO_17_SLEW {fast} \
        CONFIG.PCW_MIO_18_PULLUP {disabled} \
        CONFIG.PCW_MIO_18_SLEW {fast} \
        CONFIG.PCW_MIO_19_PULLUP {disabled} \
        CONFIG.PCW_MIO_19_SLEW {fast} \
        CONFIG.PCW_MIO_20_PULLUP {disabled} \
        CONFIG.PCW_MIO_20_SLEW {fast} \
        CONFIG.PCW_MIO_21_PULLUP {disabled} \
        CONFIG.PCW_MIO_21_SLEW {fast} \
        CONFIG.PCW_MIO_22_PULLUP {disabled} \
        CONFIG.PCW_MIO_22_SLEW {fast} \
        CONFIG.PCW_MIO_23_PULLUP {disabled} \
        CONFIG.PCW_MIO_23_SLEW {fast} \
        CONFIG.PCW_MIO_24_PULLUP {disabled} \
        CONFIG.PCW_MIO_24_SLEW {fast} \
        CONFIG.PCW_MIO_25_PULLUP {disabled} \
        CONFIG.PCW_MIO_25_SLEW {fast} \
        CONFIG.PCW_MIO_26_PULLUP {disabled} \
        CONFIG.PCW_MIO_26_SLEW {fast} \
        CONFIG.PCW_MIO_27_PULLUP {disabled} \
        CONFIG.PCW_MIO_27_SLEW {fast} \
        CONFIG.PCW_MIO_28_PULLUP {disabled} \
        CONFIG.PCW_MIO_28_SLEW {fast} \
        CONFIG.PCW_MIO_29_PULLUP {disabled} \
        CONFIG.PCW_MIO_29_SLEW {fast} \
        CONFIG.PCW_MIO_30_PULLUP {disabled} \
        CONFIG.PCW_MIO_30_SLEW {fast} \
        CONFIG.PCW_MIO_31_PULLUP {disabled} \
        CONFIG.PCW_MIO_31_SLEW {fast} \
        CONFIG.PCW_MIO_32_PULLUP {disabled} \
        CONFIG.PCW_MIO_32_SLEW {fast} \
        CONFIG.PCW_MIO_33_PULLUP {disabled} \
        CONFIG.PCW_MIO_33_SLEW {fast} \
        CONFIG.PCW_MIO_34_PULLUP {disabled} \
        CONFIG.PCW_MIO_34_SLEW {fast} \
        CONFIG.PCW_MIO_35_PULLUP {disabled} \
        CONFIG.PCW_MIO_35_SLEW {fast} \
        CONFIG.PCW_MIO_36_PULLUP {disabled} \
        CONFIG.PCW_MIO_36_SLEW {fast} \
        CONFIG.PCW_MIO_37_PULLUP {disabled} \
        CONFIG.PCW_MIO_37_SLEW {fast} \
        CONFIG.PCW_MIO_38_PULLUP {disabled} \
        CONFIG.PCW_MIO_38_SLEW {fast} \
        CONFIG.PCW_MIO_39_PULLUP {disabled} \
        CONFIG.PCW_MIO_39_SLEW {fast} \
        CONFIG.PCW_PRESET_BANK1_VOLTAGE {LVCMOS 2.5V} \
        CONFIG.PCW_QSPI_PERIPHERAL_CLKSRC {IO PLL} \
        CONFIG.PCW_QSPI_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_QSPI_PERIPHERAL_FREQMHZ {125} \
        CONFIG.PCW_SD0_GRP_CD_ENABLE {1} \
        CONFIG.PCW_SD0_GRP_CD_IO {MIO 46} \
        CONFIG.PCW_SD0_GRP_WP_ENABLE {1} \
        CONFIG.PCW_SD0_GRP_WP_IO {MIO 47} \
        CONFIG.PCW_SD0_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_SPI0_PERIPHERAL_ENABLE {0} \
        CONFIG.PCW_SPI1_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_SPI1_SPI1_IO {MIO 10 .. 15} \
        CONFIG.PCW_TTC0_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_UART0_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_UART0_UART0_IO {MIO 14 .. 15} \
        CONFIG.PCW_UART1_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_UART1_UART1_IO {MIO 8 .. 9} \
        CONFIG.PCW_UIPARAM_DDR_BUS_WIDTH {16 Bit} \
        CONFIG.PCW_UIPARAM_DDR_PARTNO {MT41J256M16 RE-125} \
        CONFIG.PCW_USB0_PERIPHERAL_ENABLE {1} \
        CONFIG.PCW_USB0_RESET_ENABLE {1} \
        CONFIG.PCW_USB0_RESET_IO {MIO 48} \
        CONFIG.PCW_USE_S_AXI_HP0 {1} \
        CONFIG.PCW_USE_S_AXI_HP1 {1} \
        CONFIG.PCW_FPGA2_PERIPHERAL_FREQMHZ {50} \
        CONFIG.PCW_USE_FABRIC_INTERRUPT {0} \
        CONFIG.PCW_USE_M_AXI_GP0 {1} \
        CONFIG.PCW_USE_M_AXI_GP1 {0} \
        CONFIG.PCW_USE_S_AXI_HP2 {0} \
        CONFIG.PCW_USE_S_AXI_HP3 {0} \
        CONFIG.PCW_S_AXI_HP0_ID_WIDTH {6} \
        CONFIG.PCW_S_AXI_HP1_ID_WIDTH {6} \
        CONFIG.PCW_FCLK_CLK0_BUF {FALSE} \
        CONFIG.PCW_FCLK_CLK1_BUF {FALSE} \
        CONFIG.PCW_FCLK_CLK2_BUF {FALSE} \
        CONFIG.PCW_FCLK_CLK3_BUF {FALSE} \
    ] $ps
}
