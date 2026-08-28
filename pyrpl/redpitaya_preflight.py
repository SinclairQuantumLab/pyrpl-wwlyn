"""Read-only Red Pitaya OS 2.07+ FPGA-update preflight.

This command opens SSH and reads version, loader, board-profile, uptime, and
FPGA-manager information. It does not upload files, remount filesystems, stop
services, start the monitor server, or program the FPGA.
"""

import argparse
from getpass import getpass
import json
import logging

from .errors import ExpectedPyrplError
from .redpitaya import RedPitaya


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('hostname', help='Red Pitaya hostname or IP address')
    parser.add_argument('--user', default='root', help='SSH user (default: root)')
    parser.add_argument('--ssh-port', type=int, default=22,
                        help='SSH port (default: 22)')
    parser.add_argument('--timeout', type=float, default=3,
                        help='SSH timeout in seconds (default: 3)')
    return parser.parse_args()


def main():
    args = parse_args()
    password = getpass('SSH password: ')
    if password == '':
        raise SystemExit('SSH password cannot be empty.')

    logging.basicConfig(level=logging.INFO)
    device = None
    try:
        device = RedPitaya(
            config=None,
            hostname=args.hostname,
            sshport=args.ssh_port,
            user=args.user,
            password=password,
            timeout=args.timeout,
            gui=False,
            autostart=False,
            reloadserver=False,
            reloadfpga=False,
        )
        report = device.preflight_fpga_update()
        if report['loader'] != 'overlay':
            raise ExpectedPyrplError(
                'This command validates only the OS 2.07+ overlay path; '
                'detected loader %r.' % report['loader'])
        print(json.dumps(report, indent=2, sort_keys=True))
    finally:
        if device is not None:
            device.end_ssh()


if __name__ == '__main__':
    main()
