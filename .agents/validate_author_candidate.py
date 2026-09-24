"""Agent-only offline/package validation of the unrepaired Z7020 test candidate."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import warnings
import zipfile


def validate(repo, output, base):
    repo, output = Path(repo).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env.update(QT_QPA_PLATFORM='offscreen', REDPITAYA_HOSTNAME='_FAKE_',
               PYRPL_USER_DIR=str(output / 'user-config'))
    results = {'base': base, 'repo': str(repo), 'commands': [], 'passed': False}

    def run(command, label, cwd=repo):
        print(label, flush=True)
        completed = subprocess.run(command, cwd=cwd, env=env, text=True,
                                   capture_output=True, errors='replace', timeout=600)
        transcript = completed.stdout + completed.stderr
        (output / (label + '.txt')).write_text(transcript, encoding='utf-8')
        results['commands'].append({'label': label, 'argv': command,
                                    'returncode': completed.returncode})
        if completed.returncode:
            print(transcript, flush=True)
            raise RuntimeError(f'{label} failed with {completed.returncode}')
        return transcript

    try:
        protected = ['pyrpl/fpga/red_pitaya.bin', 'pyrpl/fpga/sdc', 'pyrpl/fpga/ip',
                     'uv.lock', '.python-version', 'pyrpl.yml']
        protected.extend(str(p.relative_to(repo)) for p in (repo / 'pyrpl/fpga').glob('*.dt*'))
        protected.extend('pyrpl/fpga/targets/z20_gen2/' + name for name in
                         ('build.tcl', 'board.xdc', 'system_bd.tcl', 'ps_config.tcl'))
        run(['git', 'diff', '--exit-code', base, '--', *protected], 'preservation')
        run(['git', 'diff', '--exit-code', '387faf3', '--', 'pyrpl/fpga/rtl'],
            'author-source-identity')
        run(['uv', 'sync', '--extra', 'test'], 'uv-sync')
        paths = run(['git', 'ls-files', '--cached', '--others', '--exclude-standard',
                     '--', '*.py'], 'python-file-list').splitlines()
        with warnings.catch_warnings():
            warnings.simplefilter('error', SyntaxWarning)
            for name in sorted(set(paths)):
                compile((repo / name).read_bytes(), name, 'exec')
        results['compiled_python'] = len(set(paths))

        cases = ['tests.test_python314_compatibility', 'tests.test_ipykernel_compatibility',
                 'tests.test_z7020_author_baseline', 'tests.test_z7020_author_loader']
        for name in ('test_fork_pid_compatibility', 'test_gen2_manual_workflow',
                     'test_z7020_build_contract'):
            if (repo / 'tests' / (name + '.py')).is_file():
                cases.append('tests.' + name)
        if (repo / 'pyrpl/test/test_redpitaya_fpga_loader.py').is_file():
            cases.append('pyrpl.test.test_redpitaya_fpga_loader')
        results['unittest_cases'] = cases
        run(['uv', 'run', '--extra', 'test', 'python', '-m', 'unittest', *cases], 'unittest')
        nose = ['pyrpl.test.test_memory', 'pyrpl.test.test_proxyproperty',
                'tests/test_python39_compatibility.py', 'tests/test_python314_compatibility.py',
                'tests/test_ipykernel_compatibility.py']
        if (repo / 'tests/test_fork_pid_compatibility.py').is_file():
            nose.append('tests/test_fork_pid_compatibility.py')
        run(['uv', 'run', '--extra', 'test', 'nosetests', *nose], 'nose')
        results['rtl_simulation'] = 'FAILED separately: untouched int_shr declaration order; not repaired'
        run(['uv', 'build', '--out-dir', str(output / 'dist')], 'build')
        wheel = next((output / 'dist').glob('*.whl'))
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            assert hashlib.sha256(archive.read('pyrpl/fpga/red_pitaya.bin')).hexdigest() == (
                'dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed')
            candidate = 'pyrpl/fpga/red_pitaya_z20_gen2_author.bit.bin'
            record = json.loads(archive.read('pyrpl/fpga/red_pitaya_z20_gen2_author.json'))
            assert hashlib.sha256(archive.read(candidate)).hexdigest() == record['bitstream_sha256']
            assert record['common_pid_filter_fixes_included'] is False
            assert not record['timing_closed']
            assert not any(n == 'test.ipynb' or n.startswith('.agents/') for n in names)
            dtbos = {n for n in names if n.endswith('.dtbo')}
            expected_dtbos = {p.relative_to(repo).as_posix()
                              for p in (repo / 'pyrpl/fpga').glob('*.dtbo')}
            assert dtbos == expected_dtbos
            for name in dtbos | {n for n in names if n.endswith('.dts')}:
                assert archive.read(name) == (repo / name).read_bytes()
            assert not any('/sim/' in n or '/targets/' in n for n in names)
            results['wheel_entries'] = len(names)
            results['dtbos'] = sorted(dtbos)
        with tarfile.open(next((output / 'dist').glob('*.tar.gz'))) as archive:
            prefix = archive.getnames()[0].split('/')[0]
            archive.extractall(output / 'source', filter='data')
            source_root = output / 'source' / prefix
            for path in (repo / 'pyrpl/fpga/sim').iterdir():
                if path.is_file():
                    name = path.relative_to(repo).as_posix()
                    assert archive.extractfile(prefix + '/' + name).read() == path.read_bytes()
        fresh = output / 'fresh'
        run(['uv', 'venv', '--python', '3.14', str(fresh)], 'fresh-venv')
        python = str(fresh / 'Scripts/python.exe')
        run(['uv', 'pip', 'install', '--python', python, str(wheel) + '[test]'], 'fresh-install')
        run(['uv', 'pip', 'check', '--python', python], 'fresh-dependencies')
        installed_cases = [name.removeprefix('tests.') for name in cases]
        code = (
            'import sys,unittest; from pathlib import Path; import pyrpl; '
            'print("Installed package:",pyrpl.__file__); '
            'assert Path(pyrpl.__file__).resolve().is_relative_to(Path(sys.prefix)); '
            f'sys.path.insert(0,{str(source_root / "tests")!r}); '
            f'suite=unittest.defaultTestLoader.loadTestsFromNames({installed_cases!r}); '
            'result=unittest.TextTestRunner(verbosity=1).run(suite); '
            'raise SystemExit(not result.wasSuccessful())'
        )
        run([python, '-I', '-c', code], 'fresh-unittest', output)
        results['passed'] = True
    finally:
        (output / 'result.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in results.items() if k != 'commands'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo')
    parser.add_argument('output')
    parser.add_argument('base')
    args = parser.parse_args()
    validate(args.repo, args.output, args.base)
