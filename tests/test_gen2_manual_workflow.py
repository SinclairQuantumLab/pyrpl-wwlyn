"""Validate the tracked notebook without running its live-device cells."""

import ast
import contextlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

os.environ['MPLBACKEND'] = 'Agg'
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['REDPITAYA_HOSTNAME'] = '_FAKE_'
_TEST_USER_DIR = tempfile.TemporaryDirectory(prefix='pyrpl-template-test-')
os.environ['PYRPL_USER_DIR'] = _TEST_USER_DIR.name


class TestGen2ManualWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.notebook = json.loads(
            (cls.root / 'test.ipynb.template').read_text(encoding='utf-8'))
        cls.code = {cell['id']: ''.join(cell['source'])
                    for cell in cls.notebook['cells']
                    if cell['cell_type'] == 'code'}

    def test_notebook_is_clean_valid_and_explains_each_code_cell(self):
        import nbformat
        nbformat.validate(nbformat.from_dict(self.notebook))
        previous = None
        for cell in self.notebook['cells']:
            if cell['cell_type'] == 'code':
                self.assertEqual('markdown', previous)
                self.assertIsNone(cell['execution_count'])
                self.assertEqual([], cell['outputs'])
                compile(''.join(cell['source']), cell['id'], 'exec')
            previous = cell['cell_type']

    def test_only_template_is_intended_for_version_control(self):
        if not (self.root / '.gitignore').exists():
            self.skipTest('Git ignore policy applies to a repository checkout')
        ignore = (self.root / '.gitignore').read_text(encoding='utf-8')
        self.assertIn('/test.ipynb', ignore.splitlines())
        self.assertNotIn('/test.ipynb.template', ignore.splitlines())

    def test_programming_and_connection_are_separate(self):
        for cell_id, server_reload in (('template-preflight', False),
                                       ('template-program', False),
                                       ('template-connect', True),
                                       ('template-reconnect', False)):
            tree = ast.parse(self.code[cell_id])
            constructors = [node for node in ast.walk(tree)
                            if isinstance(node, ast.Call)
                            and isinstance(node.func, ast.Name)
                            and node.func.id in ('RedPitaya', 'Pyrpl')]
            self.assertEqual(1, len(constructors))
            kwargs = {kw.arg: kw.value for kw in constructors[0].keywords}
            self.assertIs(ast.literal_eval(kwargs['reloadfpga']), False)
            self.assertIs(ast.literal_eval(kwargs['reloadserver']), server_reload)
            if cell_id in ('template-preflight', 'template-program'):
                self.assertIs(ast.literal_eval(kwargs['autostart']), False)
        load_cells = [cell_id for cell_id, source in self.code.items()
                      if any(isinstance(node, ast.Call)
                             and isinstance(node.func, ast.Attribute)
                             and node.func.attr == 'update_fpga'
                             for node in ast.walk(ast.parse(source)))]
        self.assertEqual(['template-program'], load_cells)

    def test_credentials_are_prompted_and_no_notebook_load_guard_exists(self):
        source = '\n'.join(self.code.values())
        self.assertNotIn('CONFIRM_FPGA_LOAD', source)
        assignments = [node for node in ast.walk(ast.parse(source))
                       if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name)
                               and target.id == 'SSH_PASSWORD'
                               for target in node.targets)]
        self.assertEqual(1, len(assignments))
        self.assertIsInstance(assignments[0].value, ast.Call)
        self.assertEqual('getpass', assignments[0].value.func.id)

    def test_scope_helper_uses_real_api_and_cleans_up_after_failure(self):
        import numpy as np
        import matplotlib.pyplot as plt
        from pyrpl.hardware_modules.scope import Scope

        class FakeScope:
            stopped = False

            def setup(self, **kwargs):
                for name in kwargs:
                    if not hasattr(Scope, name):
                        raise AssertionError('Unknown scope setting: ' + name)

            def curve(self, timeout):
                raise TimeoutError('synthetic acquisition timeout')

            def stop(self):
                self.stopped = True

        scope = FakeScope()
        namespace = {'rp': SimpleNamespace(asg0=object(), scope=scope)}
        exec(compile(self.code['template-bench'], 'template-bench', 'exec'),
             namespace)
        with self.assertRaises(TimeoutError):
            namespace['capture_scope']('in1', 'asg0')
        self.assertTrue(scope.stopped)

        # Exercise the shape and plotting path too, without calling PyRPL I/O.
        scope.curve = lambda timeout: np.zeros((2, 16))
        scope.times = np.arange(16, dtype=float)
        with patch.object(plt, 'show'), contextlib.redirect_stdout(io.StringIO()):
            times, data = namespace['capture_scope']('in1', 'asg0')
        self.assertEqual((2, 16), data.shape)
        np.testing.assert_array_equal(times, scope.times)
        plt.close('all')


if __name__ == '__main__':
    unittest.main()
