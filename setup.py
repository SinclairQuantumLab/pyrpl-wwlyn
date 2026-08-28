# note to the developer
# do not forget to make source distribution with
# python setup.py sdist

# much of the code here is from
# https://jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/

#! /usr/bin/env python
from __future__ import print_function
from setuptools import setup
import os

# path to the directory that contains the setup.py script
SETUP_PATH = os.path.dirname(os.path.abspath(__file__))

def read(fname):
    return open(os.path.join(SETUP_PATH, fname), encoding='utf-8').read()

# Version info -- read without importing
_locals = {}
exec(read(os.path.join('pyrpl', '_version.py')), None, _locals)
version = _locals['__version__']

# # read requirements
# # from http://stackoverflow.com/questions/14399534/how-can-i-reference-requirements-txt-for-the-install-requires-kwarg-in-setuptool
# requirements = []
# here = os.path.abspath(os.path.dirname(__file__))
# with open(os.path.join(here, 'readthedocs_requirements.txt')) as f:
#     lines = f.readlines()
#     for line in lines:
#         line = line.strip()
#         if '#' not in line and line:
#             requirements.append(line.strip())
requirements = ['scp>=0.15,<1',
                'matplotlib>=3.10.5,<4', # optional requirement, not needed for core
                'scipy>=1.16.1,<2',
                'pyyaml>=6,<7',
                #'ruamel.yaml' # temporarily disabled
                'pandas>=2.3.3,<4',
                'pyqtgraph>=0.14,<1',
                'numpy>=2.3.2,<3',
                'paramiko>=4,<6',
                'pyqt5>=5.15.11,<6',
                'qtpy>=2.4.3,<3',
                'nbconvert>=7.16,<8',
                'jupyter-client>=8.6,<9',
                # Drop-in fork that provides the netifaces import.
                'netifaces2>=0.0.22,<1',
                'lmfit>=1.3.4,<2',
                # Maintained Qt/asyncio bridge replacing Quamash.
                'qasync>=0.28,<0.29',
                'six>=1.17,<2']
test_requirements = ['ipykernel>=6.31,<8',
                     'nose-ng>=1.4.3,<2']
if os.environ.get('TRAVIS') == 'true':
    requirements += ['pandoc']
if os.environ.get('READTHEDOCS') == 'True':
    requirements += ['pandoc', 'sphinx', 'sphinx_bootstrap_theme']  # mock is needed on readthedocs.io to mock PyQt5
    # remove a few of the mocked modules
    def rtd_included(r):
        for rr in ['numpy', 'scipy', 'pandas', 'scp', 'paramiko',
                   'qasync', 'qtpy', 'asyncio', 'pyqtgraph']:
            if r.startswith(rr):
                return False
        return True
    requirements = [r for r in requirements if rtd_included(r)]

# cannot install pyQt4 with pip:
# http://stackoverflow.com/questions/4628519/is-it-possible-to-require-pyqt-from-setuptools-setup-py
# PyQt4
try:
    long_description = read('README.rst')
except:
    try:
        import pypandoc
        long_description = pypandoc.convert_file('README.md', 'rst')
    except:
        long_description = read('README.md')

def find_packages():
    """
    Simple function to find all modules under the current folder.
    """
    modules = []
    for dirpath, _, filenames in os.walk(os.path.join(SETUP_PATH, "pyrpl")):
        if "__init__.py" in filenames:
            modules.append(os.path.relpath(dirpath, SETUP_PATH))
    return [module.replace(os.sep, ".") for module in modules]


def compile_fpga(): #vivado 2015.4 must be installed for this to work
    cwd = os.getcwd()
    try:
        os.chdir("pyrpl//fpga")
        os.system("make")
    finally:
        os.chdir(cwd)


def compile_server(): #gcc crosscompiler must be installed for this to work
    cwd = os.getcwd()
    try:
        os.chdir("pyrpl//pyrpl_server")
        os.system("make clean")
        os.system("make")
    finally:
        os.chdir(cwd)


setup(name='pyrpl',
      version=version,
      description='DSP servo controller for quantum optics with the RedPitaya',
      long_description=long_description,
      author='Leonhard Neuhaus',
      author_email='neuhaus@lkb.upmc.fr',
      url='http://lneuhaus.github.io/pyrpl/',
      license='GPLv3',
      classifiers=['Programming Language :: Python :: 3.14',
                   'Programming Language :: C',
                   'Natural Language :: English',
                   'Development Status :: 4 - Beta',
                   'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                   'Topic :: Scientific/Engineering :: Human Machine Interfaces',
                   'Topic :: Scientific/Engineering :: Physics'],
      keywords='RedPitaya DSP FPGA IIR PDH synchronous detection filter PID '
               'control lockbox servo feedback lock quantum optics',
      platforms='any',
      python_requires='>=3.14,<3.15',
      packages=find_packages(), #['pyrpl'],
      package_data={'pyrpl': ['fpga/*',
                              'pyrpl_server/*',
                              'config/*',
                              'widgets/images/*']},
      install_requires=requirements,
      # what were the others for? dont remember..
      #setup_requires=requirements,
      #requires=requirements,
      extras_require={'test': test_requirements},
      # install options
      cmdclass={'fpga': compile_fpga,
                'server': compile_server}
      )
