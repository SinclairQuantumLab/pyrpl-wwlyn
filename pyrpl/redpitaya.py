###############################################################################
#    pyrpl - DSP servo controller for quantum optics with the RedPitaya
#    Copyright (C) 2014-2016  Leonhard Neuhaus  (neuhaus@spectro.jussieu.fr)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from . import pyrpl_client
from . import hardware_modules as rp
from .sshshell import SshShell
from .pyrpl_utils import get_unique_name_list_from_class_list, update_with_typeconversion
from .memory import MemoryTree
from .errors import ExpectedPyrplError
from .widgets.startup_widget import HostnameSelectorWidget

import hashlib
import logging
import os
import random
import re
import socket
from time import sleep
import numpy as np

from paramiko import SSHException
from scp import SCPClient, SCPException
from collections import OrderedDict
from uuid import uuid1 as uid


FORK_BITSTREAM_SHA256 = (
    'dc6e71fb04d3a5a67731a5ddb99e7f80395a1c2fee2b8ae59168ce4252cee9ed')
OS2_Z10_DTBO_SHA256 = (
    '41a1c828bc5a7bbe99542353dfd2fbe181927e79b0e7515b86e1abbc006577f9')

# input is the wrong function in python 2
try:
    raw_input
except NameError:  # Python 3
    raw_input = input

# default parameters for redpitaya object creation
defaultparameters = dict(
    hostname='', #'192.168.1.100', # the ip or hostname of the board, '' triggers gui
    port=2222,  # port for PyRPL datacommunication
    sshport=22,  # port of ssh server - default 22
    user='root',
    password='root',
    delay=0.05,  # delay between ssh commands - console is too slow otherwise
    autostart=True,  # autostart the client?
    reloadserver=True,  # reinstall the server at startup if not necessary?
    reloadfpga=True,  # reload the fpga bitfile at startup?
    filename='fpga/red_pitaya.bin',  # local FPGA bitstream
    dtbo_filename='fpga/red_pitaya_os2_z10.dtbo',  # OS 2.07 Z7010 overlay
    recompileserver=False,  # recompile the server source on the redpitaya when the server is re-installed?
    serverbinfilename='fpga.bin',  # name of the binfile on the server
    serverdirname = "//opt//pyrpl//",  # server directory for server app and bitfile
    leds_off=True,  # turn off all GPIO lets at startup (improves analog performance)
    frequency_correction=1.0,  # actual FPGA frequency is 125 MHz * frequency_correction
    timeout=1,  # timeout in seconds for ssh communication
    monitor_server_name='pyrpl_server',  # name of the server program on redpitaya
    silence_env=False,   # suppress all environment variables that may override the configuration?
    gui=True  # show graphical user interface or work on command-line only?
    )


class RedPitaya(object):
    cls_modules = [rp.HK, rp.AMS, rp.Scope, rp.Sampler, rp.Asg0, rp.Asg1] + \
                  [rp.Pwm] * 2 + [rp.Iq] * 3 + [rp.Pid] * 3 + [rp.Trig] * 2
                  #+ [ rp.IIR]

    def __init__(self, config=None,  # configfile is needed to store parameters. None simulates one
                 **kwargs):
        """ this class provides the basic interface to the redpitaya board

        The constructor installs and starts the communication interface on the RedPitaya
        at 'hostname' that allows remote control and readout

        'config' is the config file or MemoryTree of the config file. All keyword arguments
        may be specified in the branch 'redpitaya' of this config file. Alternatively,
        they can be overwritten by keyword arguments at the function call.

        'config=None' specifies that no persistent config file is saved on the disc.

        Possible keyword arguments and their defaults are:
            hostname='192.168.1.100', # the ip or hostname of the board
            port=2222,  # port for PyRPL datacommunication
            sshport=22,  # port of ssh server - default 22
            user='root',
            password='root',
            delay=0.05,  # delay between ssh commands - console is too slow otherwise
            autostart=True,  # autostart the client?
            reloadserver=False,  # reinstall the server at startup if not necessary?
            reloadfpga=True,  # reload the fpga bitfile at startup?
            filename='fpga/red_pitaya.bin',  # local FPGA bitstream
            dtbo_filename='fpga/red_pitaya_os2_z10.dtbo',  # OS 2.07 Z7010 overlay
            serverbinfilename='fpga.bin',  # name of the binfile on the server
            serverdirname = "//opt//pyrpl//",  # server directory for server app and bitfile
            leds_off=True,  # turn off all GPIO lets at startup (improves analog performance)
            frequency_correction=1.0,  # actual FPGA frequency is 125 MHz * frequency_correction
            timeout=3,  # timeout in seconds for ssh communication
            monitor_server_name='pyrpl_server',  # name of the server program on redpitaya
            silence_env=False,   # suppress all environment variables that may override the configuration?
            gui=True  # show graphical user interface or work on command-line only?

        if you are experiencing problems, try to increase delay, or try
        logging.getLogger().setLevel(logging.DEBUG)"""
        self.logger = logging.getLogger(name=__name__)
        #self.license()
        # make or retrieve the config file
        if isinstance(config, MemoryTree):
            self.c = config
        else:
            self.c = MemoryTree(config)
        # get the parameters right (in order of increasing priority):
        # 1. defaults
        # 2. environment variables
        # 3. config file
        # 4. command line arguments
        # 5. (if missing information) request from GUI or command-line
        self.parameters = defaultparameters.copy()
        # get parameters from os.environment variables
        if not self.parameters['silence_env']:
            for k in self.parameters.keys():
                if "REDPITAYA_"+k.upper() in os.environ:
                    newvalue = os.environ["REDPITAYA_"+k.upper()]
                    oldvalue = self.parameters[k]
                    self.parameters[k] = type(oldvalue)(newvalue)
                    if k == "password": # do not show the password on the screen
                        oldvalue = "********"
                        newvalue = "********"
                    self.logger.debug("Variable %s with value %s overwritten "
                                      "by environment variable REDPITAYA_%s "
                                      "with value %s. Use argument "
                                      "'silence_env=True' if this is not "
                                      "desired!",
                                      k, oldvalue, k.upper(), newvalue)
        # settings from config file
        try:
            update_with_typeconversion(self.parameters, self.c._get_or_create('redpitaya')._data)
        except BaseException as e:
            self.logger.warning("An error occured during the loading of your "
                                "Red Pitaya settings from the config file: %s",
                                e)
        # settings from class initialisation / command line
        update_with_typeconversion(self.parameters, kwargs)
        # get missing connection settings from gui/command line
        if self.parameters['hostname'] is None or self.parameters['hostname']=='':
            gui = 'gui' not in self.c.redpitaya._keys() or self.c.redpitaya.gui
            if gui:
                self.logger.info("Please choose the hostname of "
                                 "your Red Pitaya in the hostname "
                                 "selector window!")
                startup_widget = HostnameSelectorWidget(config=self.parameters)
                hostname_kwds = startup_widget.get_kwds()
            else:
                hostname = raw_input('Enter hostname [192.168.1.100]: ')
                hostname = '192.168.1.100' if hostname == '' else hostname
                hostname_kwds = dict(hostname=hostname)
                if not "sshport" in kwargs:
                    sshport = raw_input('Enter sshport [22]: ')
                    sshport = 22 if sshport == '' else int(sshport)
                    hostname_kwds['sshport'] = sshport
                if not 'user' in kwargs:
                    user = raw_input('Enter username [root]: ')
                    user = 'root' if user == '' else user
                    hostname_kwds['user'] = user
                if not 'password' in kwargs:
                    password = raw_input('Enter password [root]: ')
                    password = 'root' if password == '' else password
                    hostname_kwds['password'] = password
            self.parameters.update(hostname_kwds)

        # optional: write configuration back to config file
        self.c["redpitaya"] = self.parameters

        # save default port definition for possible automatic port change
        self.parameters['defaultport'] = self.parameters['port']
        # frequency_correction is accessed by child modules
        self.frequency_correction = self.parameters['frequency_correction']
        # memorize whether server is running - nearly obsolete
        self._serverrunning = False
        self.client = None  # client class
        self._slaves = []  # slave interfaces to same redpitaya
        self.modules = OrderedDict()  # all submodules

        # provide option to simulate a RedPitaya
        if self.parameters['hostname'] in ['_FAKE_REDPITAYA_', '_FAKE_']:
            self.startdummyclient()
            self.logger.warning("Simulating RedPitaya because (hostname=="
                                +self.parameters["hostname"]+"). Incomplete "
                                "functionality possible. ")
            return
        elif self.parameters['hostname'] in ['_NONE_']:
            self.modules = []
            self.logger.warning("No RedPitaya created (hostname=="
                                + self.parameters["hostname"] + ")."
                                " No hardware modules are available. ")
            return
        # connect to the redpitaya board
        self.start_ssh()
        self.detect_platform()
        # start other stuff
        if self.parameters['reloadfpga']:  # flash fpga
            self.update_fpga()
        if self.parameters['reloadserver']:  # reinstall server app
            self.installserver()
        if self.parameters['autostart']:  # start client
            self.start()
            self._validate_fpga_compatibility()
        self.logger.info('Successfully connected to Redpitaya with hostname '
                         '%s.'%self.ssh.hostname)
        self.parent = self

    def start_ssh(self, attempt=0):
        """
        Extablishes an ssh connection to the RedPitaya board

        returns True if a successful connection has been established
        """
        try:
            # close pre-existing connection if necessary
            self.end_ssh()
        except:
            pass
        if self.parameters['hostname'] == "_FAKE_REDPITAYA_":
            # simulation mode - start without connecting
            self.logger.warning("(Re-)starting client in dummy mode...")
            self.startdummyclient()
            return True
        else:  # normal mode - establish ssh connection and
            try:
                # start ssh connection
                self.ssh = SshShell(hostname=self.parameters['hostname'],
                                    sshport=self.parameters['sshport'],
                                    user=self.parameters['user'],
                                    password=self.parameters['password'],
                                    delay=self.parameters['delay'],
                                    timeout=self.parameters['timeout'])
                # test ssh connection for exceptions
                self.ssh.ask()
            except BaseException as e:  # connection problem
                if attempt < 3:
                    # try to connect up to 3 times
                    return self.start_ssh(attempt=attempt+1)
                else:  # even multiple attempts did not work
                    raise ExpectedPyrplError(
                        "\nCould not connect to the Red Pitaya device with "
                        "the following parameters: \n\n"
                        "\thostname: %s\n"
                        "\tssh port: %s\n"
                        "\tusername: %s\n"
                        "\tpassword: ****\n\n"
                        "Please confirm that the device is reachable by typing "
                        "its hostname/ip address into a web browser and "
                        "checking that a page is displayed. \n\n"
                        "Error message: %s" % (self.parameters["hostname"],
                                               self.parameters["sshport"],
                                               self.parameters["user"],
                                               e))
            else:
                # everything went well, connection is established
                # also establish scp connection
                self.ssh.startscp()
                return True

    def switch_led(self, gpiopin=0, state=False):
        self.ssh.ask("echo " + str(gpiopin) + " > /sys/class/gpio/export")
        sleep(self.parameters['delay'])
        self.ssh.ask(
            "echo out > /sys/class/gpio/gpio" +
            str(gpiopin) +
            "/direction")
        sleep(self.parameters['delay'])
        if state:
            state = "1"
        else:
            state = "0"
        self.ssh.ask("echo " + state + " > /sys/class/gpio/gpio" +
            str(gpiopin) + "/value")
        sleep(self.parameters['delay'])

    @staticmethod
    def _parse_os_version(text):
        """Return the first dotted version, including an optional build."""
        match = re.search(
            r'(?<![\d.])(\d+\.\d+(?:\.\d+)?(?:-\d+)?)(?![\d.])',
            text or '')
        return match.group(1) if match is not None else 'unknown'

    @staticmethod
    def _version_tuple(version):
        if version == 'unknown':
            return ()
        return tuple(int(part) for part in re.findall(r'\d+', version))

    @staticmethod
    def _shell_marker_succeeded(result, success_marker, failure_marker):
        """Parse the last marker from a shell that may echo its command."""
        success_position = result.rfind(success_marker)
        failure_position = result.rfind(failure_marker)
        return success_position >= 0 and success_position > failure_position

    def _wait_for_shell_marker(self, result, success_marker, failure_marker,
                               attempts=40):
        """Collect delayed interactive-shell output to a terminal marker."""
        for _attempt in range(attempts):
            if (self._shell_marker_succeeded(
                    result, success_marker, failure_marker) or
                    self._shell_marker_succeeded(
                        result, failure_marker, success_marker)):
                return result
            sleep(0.25)
            result += self.ssh.ask()
        return result

    def _wait_for_output_marker(self, result, marker, attempts=40):
        """Collect delayed interactive-shell output through a final marker."""
        for _attempt in range(attempts):
            if marker in result:
                return result
            sleep(0.25)
            result += self.ssh.ask()
        return result

    def get_os_version(self):
        """Detect the ecosystem release, preferring version.txt metadata."""
        self.ssh.ask()
        ecosystem_text = self.ssh.ask(
            'cat /opt/redpitaya/version.txt 2>/dev/null')
        root_text = self.ssh.ask('cat /root/.version 2>/dev/null')
        ecosystem_version = self._parse_os_version(ecosystem_text)
        root_version = self._parse_os_version(root_text)
        if ecosystem_version != 'unknown':
            self.os_version = ecosystem_version
            self.os_version_source = '/opt/redpitaya/version.txt'
        else:
            self.os_version = root_version
            self.os_version_source = '/root/.version'
        self.os_version_tuple = self._version_tuple(self.os_version)
        self.logger.info('Detected Red Pitaya OS %s from %s.',
                         self.os_version, self.os_version_source)
        return self.os_version

    def detect_platform(self):
        """Detect OS loader capabilities without changing device state."""
        self.get_os_version()
        capability_result = self.ssh.ask(
            'if [ -x /opt/redpitaya/sbin/overlay.sh ]; then '
            'echo PYRPL_OVERLAY_AVAILABLE; else '
            'echo PYRPL_OVERLAY_MISSING; fi; '
            'if [ -c /dev/xdevcfg ]; then '
            'echo PYRPL_XDEVCFG_AVAILABLE; else '
            'echo PYRPL_XDEVCFG_MISSING; fi; '
            'echo PYRPL_CAPABILITIES_""END')
        capability_result = self._wait_for_output_marker(
            capability_result, 'PYRPL_CAPABILITIES_END')
        self.overlay_available = self._shell_marker_succeeded(
            capability_result, 'PYRPL_OVERLAY_AVAILABLE',
            'PYRPL_OVERLAY_MISSING')
        self.xdevcfg_available = self._shell_marker_succeeded(
            capability_result, 'PYRPL_XDEVCFG_AVAILABLE',
            'PYRPL_XDEVCFG_MISSING')

        version = self.os_version_tuple
        if (len(version) >= 2 and version[0] == 2 and version[1] == 7 and
                self.overlay_available):
            self.fpga_loader = 'overlay'
        elif (version and version[0] <= 1 and
              self.xdevcfg_available and not self.overlay_available):
            self.fpga_loader = 'legacy'
        else:
            self.fpga_loader = 'unsupported'
        self.logger.info('Selected Red Pitaya FPGA loader: %s.',
                         self.fpga_loader)
        return self.fpga_loader

    def _require_supported_loader(self):
        if not hasattr(self, 'fpga_loader'):
            self.detect_platform()
        if self.fpga_loader != 'unsupported':
            return
        if (self.os_version_tuple and self.os_version_tuple[0] == 2 and
                self.os_version_tuple[1:2] != (7,)):
            detail = ('Only the pinned OS 2.07 overlay contract is supported; '
                      'other OS 2 releases use different FPGA loading paths '
                      'or filenames.')
        elif self.os_version_tuple and self.os_version_tuple[0] >= 3:
            detail = 'OS 3 is not part of this pinned OS 2.07 upgrade.'
        else:
            detail = ('Neither a supported overlay.sh installation nor a '
                      'legacy /dev/xdevcfg character device was detected.')
        raise ExpectedPyrplError(
            'Cannot select a safe FPGA loader for Red Pitaya OS %s. %s' %
            (self.os_version, detail))

    def _read_os2_hardware_profile(self):
        command = (
            "printf '\\nPYRPL_PROFILE_ID:'; "
            '/opt/redpitaya/bin/profiles -i 2>/dev/null; '
            "printf '\\nPYRPL_PROFILE_FPGA:'; "
            '/opt/redpitaya/bin/profiles -f 2>/dev/null; '
            "printf '\\nPYRPL_PROFILE_ZYNQ:'; "
            '/opt/redpitaya/bin/profiles -v zynq 2>/dev/null; '
            "printf '\\nPYRPL_PROFILE_\"\"END\\n'")
        result = self.ssh.ask(command)
        result = self._wait_for_output_marker(result, 'PYRPL_PROFILE_END')

        def last_match(pattern):
            matches = re.findall(pattern, result, flags=re.IGNORECASE)
            return matches[-1] if matches else None

        profile = {
            'id': last_match(r'PYRPL_PROFILE_ID:([0-9]+)'),
            'fpga': last_match(
                r'PYRPL_PROFILE_FPGA:([A-Za-z0-9_.-]+)'),
            'zynq': last_match(r'PYRPL_PROFILE_ZYNQ:(Z70(?:10|20))'),
            'raw': result,
        }
        self.hardware_profile = profile
        return profile

    def _validate_os2_z10_profile(self):
        """Require the original-generation STEMlab 125-14 profile."""
        profile = self._read_os2_hardware_profile()
        try:
            profile_id = int(profile['id'])
        except (TypeError, ValueError):
            profile_id = None
        valid = (profile_id in (1, 2) and
                 profile['fpga'] == 'z10_125' and
                 profile['zynq'] == 'Z7010')
        if not valid:
            raise ExpectedPyrplError(
                'Refusing to program the FPGA because the Red Pitaya profile '
                'is not an original-generation STEMlab 125-14 Z7010 '
                '(expected profile id 1 or 2, fpga path z10_125, and Z7010; '
                'detected id=%r, fpga=%r, zynq=%r). This branch does not yet '
                'authorize Gen 2 or Z7020 loading.' %
                (profile['id'], profile['fpga'], profile['zynq']))
        return profile

    def _local_fpga_file(self, filename, description, package_relative=False):
        """Resolve an FPGA asset explicitly or relative to the package."""
        if not filename:
            raise OSError('%s filename is empty.' % description)
        if os.path.isabs(filename):
            candidates = [filename]
        else:
            package_path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), filename)
            candidates = ([package_path, filename] if package_relative else
                          [filename])
        for candidate in candidates:
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
        raise OSError('%s not found. Checked: %s' %
                      (description, ', '.join(candidates)))

    @staticmethod
    def _server_file(directory, filename):
        directory = re.sub('/+', '/', directory.replace('\\', '/')).rstrip('/')
        return directory + '/' + filename.lstrip('/\\')

    @staticmethod
    def _validate_os2_dtbo(source):
        with open(source, 'rb') as source_file:
            data = source_file.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != OS2_Z10_DTBO_SHA256:
            raise OSError(
                'The OS 2 DTBO does not match this fork\'s approved Z7010 '
                'overlay (expected SHA-256 %s, got %s): %s' %
                (OS2_Z10_DTBO_SHA256, digest, source))
        if b'fpga.bit.bin\x00' not in data:
            raise OSError(
                'The OS 2 DTBO does not request firmware fpga.bit.bin: %s' %
                source)
        forbidden = (b'xadc_wiz', b'xlnx,axi-xadc', b'xlnx,xadc-wiz')
        if any(value in data for value in forbidden):
            raise OSError(
                'The OS 2 DTBO describes an AXI XADC that is not present in '
                'this fork bitstream: %s' % source)

    @staticmethod
    def _validate_os2_bitstream(source):
        with open(source, 'rb') as source_file:
            digest = hashlib.sha256(source_file.read()).hexdigest()
        if digest != FORK_BITSTREAM_SHA256:
            raise OSError(
                'The OS 2 bitstream does not match this fork\'s preserved '
                'FPGA image (expected SHA-256 %s, got %s): %s' %
                (FORK_BITSTREAM_SHA256, digest, source))

    def put_file(self, source, destination):
        """Upload a file, retrying only failures that occur before loading."""
        last_error = None
        for _attempt in range(3):
            try:
                self.ssh.scp.put(source, destination)
            except (SCPException, SSHException) as error:
                last_error = error
                self.start_ssh()
                sleep(self.parameters['delay'])
            else:
                return
        raise OSError('Could not upload %r to %r' %
                      (source, destination)) from last_error

    def update_fpga(self, filename=None, dtbo_filename=None):
        """Program the fork image on legacy OS or pinned OS 2.07 safely."""
        self._require_supported_loader()
        bitstream_name = (filename if filename is not None else
                          self.parameters['filename'])
        source = self._local_fpga_file(
            bitstream_name, 'FPGA bitstream',
            package_relative=(
                bitstream_name == defaultparameters['filename']))
        dtbo_source = None
        if self.fpga_loader == 'overlay':
            dtbo_name = (dtbo_filename if dtbo_filename is not None else
                         self.parameters['dtbo_filename'])
            dtbo_source = self._local_fpga_file(
                dtbo_name, 'FPGA device-tree overlay',
                package_relative=(
                    dtbo_name == defaultparameters['dtbo_filename']))
            self._validate_os2_bitstream(source)
            self._validate_os2_dtbo(dtbo_source)
            self._validate_os2_z10_profile()
            server_directory = '/opt/pyrpl/'
            bin_file_path = '/opt/pyrpl/fpga.bit.bin'
            dtbo_file_path = '/opt/pyrpl/fpga.dtbo'
        else:
            server_directory = self.parameters['serverdirname']
            bin_file_path = self._server_file(
                server_directory, self.parameters['serverbinfilename'])
            dtbo_file_path = None

        uploaded_paths = []
        load_error = None
        cleanup_errors = []
        rw_requested = False
        web_services_stopped = False
        diagnostics = {'loader': self.fpga_loader,
                       'os_version': self.os_version}

        try:
            self.end()
            sleep(self.parameters['delay'])
            rw_requested = True
            self.ssh.ask('rw')
            self.ssh.ask('mkdir -p ' + server_directory)
            sleep(self.parameters['delay'])

            self.put_file(source, bin_file_path)
            uploaded_paths.append(bin_file_path)
            if dtbo_source is not None:
                self.put_file(dtbo_source, dtbo_file_path)
                uploaded_paths.append(dtbo_file_path)

            web_services_stopped = True
            self.ssh.ask('killall nginx')
            self.ssh.ask('systemctl stop redpitaya_nginx')
            sleep(3)

            if self.fpga_loader == 'overlay':
                update_cmd = (
                    '/opt/redpitaya/sbin/overlay.sh pyrpl '
                    '/opt/pyrpl/fpga.bit.bin /opt/pyrpl/fpga.dtbo')
                overlay_result = self.ssh.ask(
                    update_cmd +
                    ' && echo PYRPL_OVERLAY_""OK '
                    '|| echo PYRPL_OVERLAY_""FAILED')
                overlay_result = self._wait_for_shell_marker(
                    overlay_result, 'PYRPL_OVERLAY_OK',
                    'PYRPL_OVERLAY_FAILED')
                update_log = self.ssh.ask(
                    'cat /tmp/update_fpga.txt 2>&1')
                loaded_info = self.ssh.ask(
                    'cat /tmp/loaded_fpga.inf 2>&1')
                diagnostics.update(overlay_result=overlay_result,
                                   update_log=update_log,
                                   loaded_info=loaded_info)
                lower_log = update_log.lower()
                if (not self._shell_marker_succeeded(
                        overlay_result, 'PYRPL_OVERLAY_OK',
                        'PYRPL_OVERLAY_FAILED') or
                        any(error in lower_log for error in
                            ('failed', 'cannot stat', 'no such file'))):
                    manager_state = self.ssh.ask(
                        'cat /sys/class/fpga_manager/fpga0/state 2>&1')
                    kernel_log = self.ssh.ask('dmesg | tail -50')
                    raise OSError(
                        'FPGA overlay loading failed:\n%s\n%s\n%s' %
                        (overlay_result, update_log,
                         manager_state + kernel_log))
                manager_state = self.ssh.ask(
                    'cat /sys/class/fpga_manager/fpga0/state 2>&1')
                diagnostics['manager_state'] = manager_state
                if 'operating' not in manager_state.lower():
                    kernel_log = self.ssh.ask('dmesg | tail -50')
                    raise OSError(
                        'FPGA overlay returned successfully, but the FPGA '
                        'manager is not operating:\n%s' %
                        (manager_state + kernel_log))
                if 'pyrpl_' not in loaded_info.lower():
                    raise OSError(
                        'FPGA overlay returned successfully, but '
                        '/tmp/loaded_fpga.inf does not identify the custom '
                        'PyRPL load:\n%s' % loaded_info)
                self.logger.info(
                    'FPGA overlay loaded successfully on Red Pitaya OS %s.',
                    self.os_version)
            else:
                probe = self.ssh.ask(
                    'if [ -c /dev/xdevcfg ]; then '
                    'echo PYRPL_XDEVCFG_""OK; else '
                    'echo PYRPL_XDEVCFG_""MISSING; fi')
                if not self._shell_marker_succeeded(
                        probe, 'PYRPL_XDEVCFG_OK',
                        'PYRPL_XDEVCFG_MISSING'):
                    raise OSError(
                        'Cannot load the FPGA: /dev/xdevcfg is not a '
                        'character device on Red Pitaya OS %s.' %
                        self.os_version)
                result = self.ssh.ask(
                    'cat ' + bin_file_path + ' > /dev/xdevcfg '
                    '&& echo PYRPL_XDEVCFG_LOAD_""OK '
                    '|| echo PYRPL_XDEVCFG_LOAD_""FAILED')
                result = self._wait_for_shell_marker(
                    result, 'PYRPL_XDEVCFG_LOAD_OK',
                    'PYRPL_XDEVCFG_LOAD_FAILED')
                if not self._shell_marker_succeeded(
                        result, 'PYRPL_XDEVCFG_LOAD_OK',
                        'PYRPL_XDEVCFG_LOAD_FAILED'):
                    raise OSError('Legacy FPGA loading failed:\n%s' % result)
                diagnostics['legacy_result'] = result
            sleep(3)
        except Exception as error:
            load_error = error
        finally:
            if load_error is None:
                for uploaded_path in uploaded_paths:
                    try:
                        self.ssh.ask('rm -f ' + uploaded_path)
                    except Exception as error:
                        cleanup_errors.append(error)
            if web_services_stopped:
                for command in ('nginx -p //opt//www//',
                                'systemctl start redpitaya_nginx'):
                    try:
                        self.ssh.ask(command)
                    except Exception as error:
                        cleanup_errors.append(error)
            if rw_requested:
                sleep(self.parameters['delay'])
                try:
                    self.ssh.ask('ro')
                except Exception as error:
                    cleanup_errors.append(error)
            if cleanup_errors:
                if load_error is None:
                    load_error = cleanup_errors[0]
                else:
                    self.logger.warning(
                        'Additional error while restoring the Red Pitaya '
                        'after an FPGA load failure: %s', cleanup_errors[0])
        if load_error is not None:
            raise load_error
        return diagnostics

    def _validate_fpga_compatibility(self):
        """Fail early if the active FPGA does not expose this fork's map."""
        from .hardware_modules.dsp import dsp_addr_base

        checks = OrderedDict([
            ('IQ filter stages', dsp_addr_base('iq0') + 0x230),
            ('IQ filter shift bits', dsp_addr_base('iq0') + 0x234),
            ('IQ filter minimum bandwidth',
             dsp_addr_base('iq0') + 0x238),
            ('PID filter minimum bandwidth',
             dsp_addr_base('pid0') + 0x228),
        ])
        invalid = []
        for label, address in checks.items():
            response = self.client.reads(address, 1)
            if response is None or len(response) == 0:
                invalid.append('%s at %s could not be read' %
                               (label, hex(address)))
                continue
            value = int(response[0])
            if value <= 0:
                invalid.append('%s at %s=%s' %
                               (label, hex(address), value))
        if invalid:
            raise ExpectedPyrplError(
                'The connected Red Pitaya is not running this fork\'s FPGA '
                'memory map (%s). Reconnect with reloadfpga=True using the '
                'packaged fork bitstream and the matching OS 2 Z7010 DTBO. '
                'Detected OS: %s.' %
                (', '.join(invalid), self.os_version))

    def fpgarecentlyflashed(self):
        self.ssh.ask()
        result =self.ssh.ask("echo $(($(date +%s) - $(date +%s -r \""
        + os.path.join(self.parameters['serverdirname'], self.parameters['serverbinfilename']) +"\")))")
        age = None
        for line in result.split('\n'):
            try:
                age = int(line.strip())
            except:
                pass
            else:
                break
        if not age:
            self.logger.debug("Could not retrieve bitfile age from: %s",
                            result)
            return False
        elif age > 10:
            self.logger.debug("Found expired bitfile. Age: %s", age)
            return False
        else:
            self.logger.debug("Found recent bitfile. Age: %s", age)
            return True

    def newtoken(self):
        """ generates, stores internally and returns a new (random) token for client authentification """
        token = str(uid().hex)
        self.parameters['token'] = token
        return token

    def recompileserver(self, targetfile='pyrpl_server'):
        self.endserver()
        sleep(self.parameters['delay'])
        self.ssh.ask('rw')
        sleep(self.parameters['delay'])
        self.ssh.ask('mkdir ' + self.parameters['serverdirname'])
        sleep(self.parameters['delay'])
        self.ssh.ask("cd " + self.parameters['serverdirname'])
        sleep(self.parameters['delay'])
        self.ssh.ask("rm pyrpl_server")
        sleep(self.parameters['delay'])
        for uploadfile in ['pyrpl_server.c']:
            try:
                self.ssh.scp.put(
                    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pyrpl_server', uploadfile),
                    self.parameters['serverdirname'] + uploadfile)
            except (SCPException, SSHException):
                self.logger.exception("Upload error. Try again after rebooting your RedPitaya..")
                raise
        sleep(self.parameters['delay'])
        #print(self.ssh.ask('make'))
        self.ssh.ask('gcc pyrpl_server.c -o '+targetfile)
        sleep(5)  # give the RP filesystem time to locat the new file before downloading it
        self.ssh.ask('ll')
        sleep(self.parameters['delay'])
        self.ssh.scp.get(self.parameters['serverdirname'] + targetfile,
                         os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pyrpl_server', targetfile))

    def installserver(self):
        self.endserver()
        sleep(self.parameters['delay'])
        self.ssh.ask('rw')
        sleep(self.parameters['delay'])
        self.ssh.ask('mkdir ' + self.parameters['serverdirname'])
        sleep(self.parameters['delay'])
        self.ssh.ask("cd " + self.parameters['serverdirname'])
        if self.parameters['recompileserver']:
            self.recompileserver()
        #try both versions
        for serverfile in ['pyrpl_server_0.92','pyrpl_server_0.95']:
            sleep(self.parameters['delay'])
            try:
                self.ssh.scp.put(
                    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pyrpl_server', serverfile),
                    self.parameters['serverdirname'] + self.parameters['monitor_server_name'])
            except (SCPException, SSHException):
                self.logger.exception("Upload error. Try again after rebooting your RedPitaya..")
            sleep(self.parameters['delay'])
            self.ssh.ask('chmod 755 ./'+self.parameters['monitor_server_name'])
            sleep(self.parameters['delay'])
            self.ssh.ask('ro')
            result = self.ssh.ask("./"
                                  +self.parameters['monitor_server_name']
                                  +" "
                                  + str(self.parameters['port'])
                                  + " "
                                  + self.newtoken()
                                  )
            sleep(self.parameters['delay'])
            result += self.ssh.ask()
            if not "sh" in result: 
                self.logger.debug("Server application started on port %d",
                              self.parameters['port'])
                return self.parameters['port'], self.parameters['token']
            else: # means we tried the wrong binary version. make sure server is not running and try again with next file
                self.endserver()
        
        #try once more on a different port
        if self.parameters['port'] == self.parameters['defaultport']:
            self.parameters['port'] = random.randint(self.parameters['defaultport'],50000)
            self.logger.warning("Problems to start the server application. Trying again with a different port number %d",self.parameters['port'])
            return self.installserver()
        
        self.logger.error("Server application could not be started. Try to recompile pyrpl_server on your RedPitaya (see manual). ")
        return None
    
    def startserver(self):
        self.endserver()
        sleep(self.parameters['delay'])
        if self.fpgarecentlyflashed():
            self.logger.info("FPGA is being flashed. Please wait for 2 "
                            "seconds.")
            sleep(2.0)
        result = self.ssh.ask(self.parameters['serverdirname']+"/"+self.parameters['monitor_server_name']
                          +" "+ str(self.parameters['port'])+" "+ self.newtoken())
        if not "sh" in result: # sh in result means we tried the wrong binary version
            self.logger.debug("Server application started on port %d",
                              self.parameters['port'])
            self._serverrunning = True
            return self.parameters['port'], self.parameters['token']
        #something went wrong
        return self.installserver()
    
    def endserver(self):
        try:
            self.ssh.ask('\x03') #exit running server application
        except:
            self.logger.exception("Server not responding...")
        if 'pitaya' in self.ssh.ask():
            self.logger.debug('>') # formerly 'console ready'
        sleep(self.parameters['delay'])
        # make sure no other pyrpl_server blocks the port
        self.ssh.ask('killall ' + self.parameters['monitor_server_name'])
        self._serverrunning = False
        
    def endclient(self):
        del self.client
        self.client = None

    def start(self):
        if self.parameters['leds_off']:
            self.switch_led(gpiopin=0, state=False)
            self.switch_led(gpiopin=7, state=False)
        self.startserver()
        sleep(self.parameters['delay'])
        self.startclient()

    def end(self):
        self.endserver()
        self.endclient()

    def end_ssh(self):
        self.ssh.channel.close()

    def end_all(self):
        self.end()
        self.end_ssh()

    def restart(self):
        self.end()
        self.start()

    # disable restartserver
    restartserver = None
    if False:
        def restartserver(self, port=None):
            """restart the server. usually executed when client encounters an error"""
            if port is not None:
                if port < 0: #code to try a random port
                    self.parameters['port'] = random.randint(2223,50000)
                else:
                    self.parameters['port'] = port
            return self.startserver()

    def license(self):
        self.logger.info("""\r\n    pyrpl  Copyright (C) 2014-2017 Leonhard Neuhaus
    This program comes with ABSOLUTELY NO WARRANTY; for details read the file
    "LICENSE" in the source directory. This is free software, and you are
    welcome to redistribute it under certain conditions; read the file
    "LICENSE" in the source directory for details.\r\n""")

    def startclient(self):
        self.client = pyrpl_client.PyrplClient(
            self.parameters['hostname'],
            self.parameters['port'],
            self.parameters['token'],
            restartserver=self.restartserver)
        self.makemodules()
        self.logger.debug("Client started successfully. ")

    def startdummyclient(self):
        self.client = pyrpl_client.DummyClient()
        self.makemodules()

    def makemodule(self, name, cls):
        module = cls(self, name)
        setattr(self, name, module)
        self.modules[name] = module

    def makemodules(self):
        """
        Automatically generates modules from the list RedPitaya.cls_modules
        """
        names = get_unique_name_list_from_class_list(self.cls_modules)
        for cls, name in zip(self.cls_modules, names):
            self.makemodule(name, cls)

    def make_a_slave(self, port=None, monitor_server_name=None, gui=False):
        if port is None:
            port = self.parameters['port'] + len(self._slaves)*10 + 1
        if monitor_server_name is None:
            monitor_server_name = self.parameters['monitor_server_name'] + str(port)
        slaveparameters = dict(self.parameters)
        slaveparameters.update(dict(
                         port=port,
                         autostart=True,
                         reloadfpga=False,
                         reloadserver=False,
                         monitor_server_name=monitor_server_name,
                         silence_env=True))
        r = RedPitaya(**slaveparameters) #gui=gui)
        r._master = self
        self._slaves.append(r)
        return r
