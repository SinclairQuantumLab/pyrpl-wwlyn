"""Source-preservation guards, not a replacement for Vivado or board tests."""

from pathlib import Path
import re
import unittest


FPGA = Path(__file__).resolve().parents[1] / 'pyrpl' / 'fpga'
TARGET = FPGA / 'targets' / 'z20_gen2'


def active_lines(path):
    return [line.strip() for line in path.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.lstrip().startswith('#')]


def ps_properties(path):
    return dict(re.findall(r'CONFIG\.(PCW_\w+)\s+\{([^}]+)\}',
                           path.read_text(encoding='utf-8')))


class TestZ7020BuildContract(unittest.TestCase):
    def test_ps_configuration_has_only_documented_changes(self):
        original = ps_properties(FPGA / 'ip' / 'system_bd.tcl')
        expected = dict(original)
        del expected['PCW_IRQ_F2P_INTR']
        expected.update({
            'PCW_USE_FABRIC_INTERRUPT': '0',
            'PCW_USE_M_AXI_GP0': '1', 'PCW_USE_M_AXI_GP1': '0',
            'PCW_USE_S_AXI_HP2': '0', 'PCW_USE_S_AXI_HP3': '0',
            'PCW_FPGA2_PERIPHERAL_FREQMHZ': '50',
            'PCW_S_AXI_HP0_ID_WIDTH': '6', 'PCW_S_AXI_HP1_ID_WIDTH': '6',
            **{f'PCW_FCLK_CLK{i}_BUF': 'FALSE' for i in range(4)},
        })
        self.assertEqual(expected, ps_properties(TARGET / 'ps_config.tcl'))

    def test_active_io_constraints_preserve_author_pin_and_electrical_mapping(self):
        def properties(path):
            # Ignore old trailing annotations, which are invalid Tcl arguments.
            return [' '.join(line.split('#', 1)[0].split())
                    for line in active_lines(path) if line.startswith('set_property')]
        self.assertEqual(properties(FPGA / 'sdc' / 'red_pitaya.xdc'),
                         properties(TARGET / 'board.xdc'))

    def test_target_xdc_has_no_invalid_inline_comments_or_timing_waivers(self):
        lines = active_lines(TARGET / 'board.xdc')
        for line in lines:
            self.assertNotIn('#', line)
            self.assertFalse(line.startswith(('set_false_path', 'set_multicycle_path',
                                             'set_clock_groups')))
            self.assertNotIn('SEVERITY', line)
        self.assertIn('create_clock -period 8.000 -name adc_clk [get_ports adc_clk_p_i]',
                      lines)

    def test_full_design_reads_only_existing_fork_rtl(self):
        build = (TARGET / 'build.tcl').read_text(encoding='utf-8')
        names = re.findall(r'\bred_pitaya_\w+\.(?:v|sv)\b|\baxi_\w+\.v\b|\bbus_clk_bridge\.v\b',
                           build)
        self.assertEqual(len(names), len(set(names)))
        self.assertGreater(len(names), 25)
        for name in names:
            self.assertTrue((FPGA / 'rtl' / name).is_file(), name)
        for name in ('red_pitaya_top.v', 'red_pitaya_ps.v', 'red_pitaya_ams.v',
                     'red_pitaya_pid_block.v'):
            self.assertIn(name, names)

    def test_development_build_cannot_emit_or_load_an_image(self):
        build = '\n'.join(active_lines(TARGET / 'build.tcl'))
        self.assertIn('-part xc7z020clg400-1', build)
        self.assertIn('[version -short] ne "2023.2"', build)
        self.assertIn('if {[file exists $output]} { error', build)
        self.assertNotRegex(build, r'\b(write_bitstream|write_cfgmem|program_hw_devices|exec)\b')
        self.assertNotIn('SEVERITY', build)

    def test_ps_shell_uses_one_ps_ip_without_axi_xadc(self):
        shell = '\n'.join(active_lines(TARGET / 'system_bd.tcl'))
        self.assertEqual(['xilinx.com:ip:processing_system7:5.5'],
                         re.findall(r'create_bd_cell -type ip -vlnv (\S+)', shell))
        self.assertIn('M_AXI_GP0 32 12 S_AXI_HP0 64 6 S_AXI_HP1 64 6', shell)
        self.assertIn('-range 0x40000000 -offset 0x40000000', shell)
        self.assertIn('-range 0x20000000 -offset 0x0', shell)
        self.assertIn('validate_bd_design', shell)


if __name__ == '__main__':
    unittest.main()
