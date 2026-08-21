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

import logging
import os
import random
import re
import socket
import tempfile
from time import sleep
import numpy as np

from paramiko import SSHException
from scp import SCPClient, SCPException
from collections import OrderedDict
from uuid import uuid1 as uid

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
    recompileserver=False,  # recompile the server source on the redpitaya when the server is re-installed?
    serverbinfilename='fpga.bin',  # name of the binfile on the server
    dtbo_filename='fpga/red_pitaya.dtbo',  # matching device-tree overlay
    serverdtbofilename='fpga.dtbo',  # overlay filename on the server
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
            filename='fpga/red_pitaya.bin',  # name of the bitfile for the fpga
            dtbo_filename='fpga/red_pitaya.dtbo',  # device-tree overlay
            serverbinfilename='fpga.bin',  # name of the binfile on the server
            serverdtbofilename='fpga.dtbo',  # overlay filename on the server
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
        self.get_os_version()
        self._configure_os_compatibility()
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

    def get_os_version(self):
        """Read and parse the Red Pitaya OS version over SSH."""
        self.ssh.ask()  # clear the interactive shell buffer
        result = self.ssh.ask('cat /root/.version')
        self.logger.debug('cat /root/.version: %s', result)
        match = re.search(r'(?<![\d.])(\d+(?:\.\d+)+)(?![\d.])', result)
        if match is None:
            self.os_version = 'unknown'
            self.logger.warning('Could not parse Red Pitaya OS version from: %s',
                                result)
        else:
            self.os_version = match.group(1)
        self.logger.info('Detected Red Pitaya OS %s.', self.os_version)
        return self.os_version

    def _configure_os_compatibility(self):
        """Apply fixed FPGA filenames required by OS 2 and OS 3."""
        if self.os_version.startswith('3.'):
            required_binfilename = 'fpga.bin'
        elif self.os_version.startswith('2.'):
            # OS 2 overlay.sh ignores the supplied image name and asks the
            # firmware loader for this exact filename in /opt/pyrpl.
            required_binfilename = 'fpga.bit.bin'
        else:
            return

        required_settings = {
            'serverdirname': '/opt/pyrpl/',
            'serverbinfilename': required_binfilename,
            'serverdtbofilename': 'fpga.dtbo',
        }
        if not self.parameters.get('dtbo_filename'):
            required_settings['dtbo_filename'] = 'fpga/red_pitaya.dtbo'
        changed = {key: (self.parameters.get(key), value)
                   for key, value in required_settings.items()
                   if self.parameters.get(key) != value}
        if changed:
            self.logger.info(
                'Red Pitaya OS %s requires fixed overlay paths; overriding '
                'saved settings: %s.', self.os_version, changed)
            self.parameters.update(required_settings)
            self.c['redpitaya'] = self.parameters

    def _local_fpga_file(self, filename, description, required=True):
        """Resolve a configured FPGA asset relative to the package."""
        if not filename:
            if required:
                raise OSError('%s filename is empty.' % description)
            return None
        source = filename
        if not os.path.isabs(source):
            source = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                  source)
        if not os.path.isfile(source):
            if required:
                raise OSError(
                    '%s not found at %s. Pass an existing %s path.' %
                    (description, source, description.lower()))
            self.logger.warning('%s not found at %s; continuing without it.',
                                description, source)
            return None
        return source

    def _server_file(self, filename):
        """Build a POSIX path even when the client runs on Windows."""
        directory = self.parameters['serverdirname'].replace('\\', '/')
        directory = re.sub('/+', '/', directory).rstrip('/')
        return directory + '/' + filename.lstrip('/\\')

    @staticmethod
    def _shell_marker_succeeded(result, success_marker, failure_marker):
        """Parse a marker from an interactive shell that echoes commands."""
        success_position = result.rfind(success_marker)
        failure_position = result.rfind(failure_marker)
        return success_position >= 0 and success_position > failure_position

    def _wait_for_shell_marker(self, result, success_marker, failure_marker,
                               attempts=40):
        """Collect delayed shell output until a terminal marker arrives."""
        for _attempt in range(attempts):
            if success_marker in result or failure_marker in result:
                return result
            sleep(0.25)
            result += self.ssh.ask()
        return result

    def put_file(self, source, destination):
        """Upload a file, reconnecting and retrying transient SCP failures."""
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
        """Program the FPGA using the mechanism supported by the board OS."""
        source = self._local_fpga_file(
            filename if filename is not None else self.parameters['filename'],
            'FPGA bitstream')
        modern_os = (self.os_version.startswith('2.') or
                     self.os_version.startswith('3.'))
        dtbo_source = self._local_fpga_file(
            dtbo_filename if dtbo_filename is not None else
            self.parameters['dtbo_filename'],
            'FPGA device-tree overlay', required=modern_os)
        bin_file_path = self._server_file(
            self.parameters['serverbinfilename'])
        dtbo_file_path = self._server_file(
            self.parameters['serverdtbofilename'])
        uploaded_paths = []
        load_error = None
        cleanup_errors = []
        rw_requested = False
        web_services_stopped = False

        try:
            # A running pyrpl_server occupies the interactive SSH channel, so
            # stop it before issuing any shell command, including preflights.
            self.end()
            sleep(self.parameters['delay'])

            rw_requested = True
            self.ssh.ask('rw')
            self.ssh.ask('mkdir -p ' + self.parameters['serverdirname'])
            sleep(self.parameters['delay'])

            self.put_file(source, bin_file_path)
            uploaded_paths.append(bin_file_path)
            update_cmd = ('/opt/redpitaya/sbin/overlay.sh pyrpl ' +
                          bin_file_path)

            if modern_os and dtbo_source is not None:
                dtbo_to_upload = dtbo_source
                temporary_dtbo = None
                if self.os_version.startswith('3.'):
                    # OS 3 stages fpga.bin instead of the fixed OS 2 name
                    # embedded in the distributed overlay.
                    old_name = b'fpga.bit.bin\x00'
                    new_name = (b'fpga.bin\x00' +
                                b'\x00' * (len(old_name) -
                                           len(b'fpga.bin\x00')))
                    with open(dtbo_source, 'rb') as source_file:
                        dtbo_data = source_file.read()
                    if old_name not in dtbo_data:
                        raise OSError(
                            'OS 3 DTBO conversion failed: firmware-name '
                            'fpga.bit.bin was not found in %s' % dtbo_source)
                    temporary_dtbo = tempfile.NamedTemporaryFile(
                        suffix='.dtbo', delete=False)
                    try:
                        temporary_dtbo.write(
                            dtbo_data.replace(old_name, new_name, 1))
                    finally:
                        temporary_dtbo.close()
                    dtbo_to_upload = temporary_dtbo.name
                try:
                    self.put_file(dtbo_to_upload, dtbo_file_path)
                finally:
                    if temporary_dtbo is not None:
                        os.unlink(temporary_dtbo.name)
                uploaded_paths.append(dtbo_file_path)
                update_cmd += ' ' + dtbo_file_path

            # Prevent other processes from accessing registers while the
            # programmable logic is being replaced.
            web_services_stopped = True
            self.ssh.ask('killall nginx')
            self.ssh.ask('systemctl stop redpitaya_nginx')
            sleep(3)

            if modern_os:
                overlay_result = self.ssh.ask(
                    update_cmd +
                    ' && echo PYRPL_OVERLAY_""OK '
                    '|| echo PYRPL_OVERLAY_""FAILED')
                overlay_result = self._wait_for_shell_marker(
                    overlay_result, 'PYRPL_OVERLAY_OK',
                    'PYRPL_OVERLAY_FAILED')
                update_log = self.ssh.ask('cat /tmp/update_fpga.txt')
                lower_log = update_log.lower()
                if (not self._shell_marker_succeeded(
                        overlay_result, 'PYRPL_OVERLAY_OK',
                        'PYRPL_OVERLAY_FAILED') or
                        'failed' in lower_log or
                        'cannot stat' in lower_log or
                        'no such file' in lower_log):
                    diagnostics = self.ssh.ask(
                        'cat /sys/class/fpga_manager/fpga0/state 2>&1')
                    diagnostics += self.ssh.ask('dmesg | tail -50')
                    raise OSError(
                        'FPGA overlay loading failed:\n%s\n'
                        'FPGA manager and kernel diagnostics:\n%s' %
                        (overlay_result + update_log, diagnostics))
                manager_state = self.ssh.ask(
                    'cat /sys/class/fpga_manager/fpga0/state 2>&1')
                if 'operating' not in manager_state.lower():
                    diagnostics = manager_state
                    diagnostics += self.ssh.ask('dmesg | tail -50')
                    raise OSError(
                        'FPGA overlay command returned without an error, but '
                        'the FPGA manager is not operating:\n%s' % diagnostics)
                self.logger.info('FPGA overlay loaded successfully on OS %s.',
                                 self.os_version)
            else:
                # Redirecting to a missing path creates a regular file under
                # /dev and falsely looks successful. Never do that.
                probe = self.ssh.ask(
                    'if [ -c /dev/xdevcfg ]; then echo PYRPL_XDEVCFG_""OK; '
                    'else echo PYRPL_XDEVCFG_""MISSING; fi')
                probe = self._wait_for_shell_marker(
                    probe, 'PYRPL_XDEVCFG_OK',
                    'PYRPL_XDEVCFG_MISSING', attempts=8)
                if not self._shell_marker_succeeded(
                        probe, 'PYRPL_XDEVCFG_OK',
                        'PYRPL_XDEVCFG_MISSING'):
                    raise OSError(
                        'Cannot load the FPGA: Red Pitaya OS %s has no '
                        '/dev/xdevcfg character device. Check /root/.version '
                        'and use the OS 2/3 overlay loader.' % self.os_version)
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
                self.logger.info('FPGA loaded via /dev/xdevcfg on legacy OS %s.',
                                 self.os_version)
            sleep(3)
        except Exception as error:
            load_error = error
        finally:
            # Retain failed inputs on the board for manual diagnostics.
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

    def _validate_fpga_compatibility(self):
        """Fail early when the running FPGA image has the wrong memory map."""
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
                invalid.append('%s at %s=%s' % (label, hex(address), value))
        if invalid:
            raise ExpectedPyrplError(
                'The connected Red Pitaya is not running a compatible PyRPL '
                'FPGA image (%s). The image was not programmed or its memory '
                'map does not match this checkout. Reconnect with '
                'reloadfpga=True and the correct filename/dtbo_filename for '
                'this board. Detected OS: %s.' %
                (', '.join(invalid), getattr(self, 'os_version', 'unknown')))

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
        ssh = getattr(self, 'ssh', None)
        if ssh is None:
            self._serverrunning = False
            return
        try:
            ssh.ask('\x03')  # exit running server application
            if 'pitaya' in ssh.ask():
                self.logger.debug('>')  # formerly 'console ready'
            sleep(self.parameters['delay'])
            # make sure no other pyrpl_server blocks the port
            ssh.ask('killall ' + self.parameters['monitor_server_name'])
        except Exception:
            self.logger.exception("Server not responding...")
        finally:
            self._serverrunning = False
        
    def endclient(self):
        if not hasattr(self, 'client'):
            return
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
        ssh = getattr(self, 'ssh', None)
        channel = getattr(ssh, 'channel', None)
        if channel is not None:
            channel.close()

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
