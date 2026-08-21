from ._version import __version_info__, __version__

__author__ = "Leonhard Neuhaus <neuhaus@lkb.upmc.fr>"
__license__ = "GNU General Public License v3 or later (GPLv3+)"

# manage warnings of numpy and scipy
import warnings
import numpy as np
from numpy.exceptions import ComplexWarning, VisibleDeprecationWarning
# pyqtgraph is throwing a warning on ScatterPlotItem
warnings.simplefilter("ignore", VisibleDeprecationWarning)
# pyqtgraph is throwing a warning on ScatterPlotItem
warnings.simplefilter("error", ComplexWarning)
# former issue with IIR, now resolved
#from scipy.signal import BadCoefficients
#warnings.simplefilter("error", BadCoefficients)

#set up loggers
import logging
logging.basicConfig()
logger = logging.getLogger(name=__name__)
# only show errors or warnings until userdefine log level is set up
logger.setLevel(logging.INFO)

# enable ipython QtGui support if needed
import asyncio

IPYTHON = None
IPYTHON_ASYNC_LOOP = None
try:
    from IPython import get_ipython
    IPYTHON = get_ipython()
    if IPYTHON is not None:
        try:
            IPYTHON_ASYNC_LOOP = asyncio.get_running_loop()
        except RuntimeError:
            # Terminal IPython has no running asyncio loop and still relies on
            # the traditional Qt GUI input hook.
            IPYTHON.run_line_magic("gui", "qt")
except Exception as e:
    logger.debug('Could not enable IPython gui support: %s.' % e)

# get QApplication instance
from qtpy import QtCore, QtWidgets
APP = QtWidgets.QApplication.instance()
if APP is None:
    logger.debug('Creating new QApplication instance "pyrpl"')
    APP = QtWidgets.QApplication(['pyrpl'])


async def _pump_qt_from_ipykernel():
    """Keep Qt responsive without replacing ipykernel's asyncio loop."""
    try:
        while True:
            APP.processEvents()
            await asyncio.sleep(0.01)
    except asyncio.CancelledError:
        pass


IPYTHON_QT_PUMP = None
if IPYTHON_ASYNC_LOOP is not None:
    IPYTHON_QT_PUMP = IPYTHON_ASYNC_LOOP.create_task(
        _pump_qt_from_ipykernel(), name="pyrpl-qt-event-pump")

# get user directories
import os
try:  # first try from environment variable
    user_dir = os.environ["PYRPL_USER_DIR"]
except KeyError:  # otherwise, try ~/pyrpl_user_dir (where ~ is the user's home dir)
    user_dir = os.path.join(os.path.expanduser('~'), 'pyrpl_user_dir')

# make variable directories
user_config_dir = os.path.join(user_dir, 'config')
user_curve_dir = os.path.join(user_dir, 'curve')
user_lockbox_dir = os.path.join(user_dir, 'lockbox')
default_config_dir = os.path.join(os.path.dirname(__file__), 'config')
# create dirs if necessary
for path in [user_dir, user_config_dir, user_curve_dir, user_lockbox_dir]:
    if not os.path.isdir(path):
        os.mkdir(path)  # pragma: no cover

# try to set log level (and automatically generate custom global_config file)
from .pyrpl_utils import setloglevel
from .memory import MemoryTree
global_config = MemoryTree('global_config', source='global_config')
try:
    setloglevel(global_config.general.loglevel, loggername=logger.name)
except:  # pragma: no cover
    pass

# main imports
from .redpitaya import RedPitaya
from .hardware_modules import *
from .attributes import *
from .modules import *
from .curvedb import *
from .pyrpl import *
