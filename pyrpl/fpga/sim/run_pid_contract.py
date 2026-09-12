"""Run the real fork PID RTL with XSim; never build or load an FPGA image."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def run(vivado_bin=None, output_root=None):
    fpga = Path(__file__).resolve().parents[1]
    sources = [fpga / 'rtl' / name for name in (
        'red_pitaya_lpf_block.v', 'red_pitaya_filter_block.v',
        'red_pitaya_pid_block.v')]
    sources.append(fpga / 'sim' / 'tb_pid_contract.sv')
    tools = {}
    for name in ('xvlog', 'xelab', 'xsim'):
        executable = (str(Path(vivado_bin) / (name + ('.bat' if os.name == 'nt' else '')))
                      if vivado_bin else shutil.which(name))
        if not executable or not Path(executable).is_file():
            raise RuntimeError(f'{name} unavailable; set --vivado-bin to the Vivado bin directory')
        tools[name] = str(Path(executable).resolve())
    if output_root:
        Path(output_root).mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix='pyrpl-pid-rtl-', dir=output_root))
    print(f'RTL simulation artifacts: {output}', flush=True)
    env = os.environ.copy()
    env['XILINX_VIVADO'] = str(Path(tools['xvlog']).parent.parent)
    commands = [
        [tools['xvlog'], *map(str, sources[:-1])],
        [tools['xvlog'], '--sv', str(sources[-1])],
        [tools['xelab'], 'work.tb_pid_contract', '-s', 'pid_contract', '-debug', 'typical'],
        [tools['xsim'], 'pid_contract', '-runall'],
    ]
    report = {
        'kind': 'behavioral simulation; not synthesis or hardware validation',
        'source_sha256': {str(p.relative_to(fpga)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sources},
        'commands': [], 'passed': False,
    }
    try:
        for index, command in enumerate(commands):
            result = subprocess.run(command, cwd=output, env=env,
                                    capture_output=True, text=True,
                                    errors='replace', timeout=180)
            transcript = result.stdout + result.stderr
            (output / f'{index}-{Path(command[0]).stem}-console.txt').write_text(
                transcript, encoding='utf-8')
            report['commands'].append({'argv': command, 'returncode': result.returncode})
            print(transcript, flush=True)
            if result.returncode:
                raise RuntimeError(f'{Path(command[0]).name} exited {result.returncode}')
        if 'PID_CONTRACT_PASS' not in transcript or 'PID_CONTRACT_FAIL' in transcript:
            raise RuntimeError('Simulation did not report a complete contract pass')
        report['passed'] = True
    finally:
        (output / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vivado-bin', help='Vivado bin directory; otherwise use PATH')
    parser.add_argument('--output-root', help='Parent for a new, retained simulation directory')
    args = parser.parse_args()
    run(args.vivado_bin, args.output_root)
