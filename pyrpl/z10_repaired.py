"""Explicit Gen1 repaired-image selection; original images remain unchanged."""

import hashlib
from pathlib import Path
import re
import shlex
import sys

from .errors import ExpectedPyrplError


Z10_REPAIRED_BITSTREAM_FILENAME = 'fpga/red_pitaya_z10_gen1_repaired.bin'
Z10_REPAIRED_BITSTREAM_SHA256 = (
    '922edd86645057fbf59b421b7854b0d96ed77745fa94019261cfeb7a6c9cd966')
REPAIRED_RTL_COMMIT = 'e7479166c03c15bdd244e2153e974b4596815041'


def is_repaired_selection(filename):
    """Recognize the candidate by explicit basename or exact file contents."""
    if not filename:
        return False
    path = Path(filename)
    return (path.name == Path(Z10_REPAIRED_BITSTREAM_FILENAME).name or
            (path.is_file() and
             hashlib.sha256(path.read_bytes()).hexdigest() == Z10_REPAIRED_BITSTREAM_SHA256))


def repaired_file(filename=None):
    """Resolve and hash-check the explicit repaired candidate, without fallback."""
    name = str(filename or Z10_REPAIRED_BITSTREAM_FILENAME)
    path = (Path(__file__).resolve().parent / name
            if name == Z10_REPAIRED_BITSTREAM_FILENAME else Path(name))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != Z10_REPAIRED_BITSTREAM_SHA256:
        raise OSError('Not the approved Gen1 repaired image: %s (SHA-256 %s)' %
                      (path, digest))
    return path.resolve()


def legacy_preflight(device, filename=None):
    """Read EEPROM identity, ecosystem version and loader type; never upload."""
    path = repaired_file(filename)
    command = (
        "printf 'PYRPL_OS:'; cat /opt/redpitaya/version.txt || exit 1; "
        "printf '\\nPYRPL_HW:'; fw_printenv -n hw_rev || exit 1; "
        "printf '\\nPYRPL_CHAR:'; test -c /dev/xdevcfg || exit 1; "
        "printf 'yes\\n'")
    status, output, error = device.ssh.execute(command)
    os_text = output.partition('PYRPL_OS:')[2].partition('PYRPL_HW:')[0]
    os_match = re.search(r'(?<![\d.])(\d+\.\d+(?:\.\d+)?(?:-\d+)?)(?![\d.])', os_text)
    hw_match = re.search(r'PYRPL_HW:([^\r\n]+)', output)
    hw = hw_match.group(1).strip() if hw_match else None
    # Exact original 125-14 EEPROM families, including the vendor's legacy alias.
    # Never substitute the vendor API's default profile for unknown EEPROM data.
    allowed = {'stem_125-14_v1.0', 'stem_125-14_v1.1', 'stem_14_b_v1.0'}
    if (status or error.strip() or not os_match or int(os_match.group(1).split('.')[0]) != 1
            or not hw or hw.lower() not in allowed
            or 'PYRPL_CHAR:yes' not in output):
        raise ExpectedPyrplError(
            'Repaired Gen1 legacy load requires OS 1, an original 125-14 '
            'Z7010 EEPROM identity and a character /dev/xdevcfg. '
            'Detected hw_rev=%r, version=%r, status=%s. %s' %
            (hw, os_match.group(1) if os_match else None, status, error.strip()))
    return dict(read_only=True, loader='legacy', os_version=os_match.group(1),
                hardware_revision=hw, local_bitstream=str(path),
                local_bitstream_sha256=Z10_REPAIRED_BITSTREAM_SHA256,
                bitstream_lineage='common-pid-repaired',
                repaired_rtl_commit=REPAIRED_RTL_COMMIT,
                remote_bitstream='/opt/pyrpl/red_pitaya_z10_gen1_repaired.bin',
                local_dtbo=None, timing_closed=False)


def legacy_program(device, filename=None):
    """Program only the separately approved repaired image after fresh checks."""
    report = legacy_preflight(device, filename)

    def checked(command):
        status, output, error = device.ssh.execute(command)
        if status:
            raise ExpectedPyrplError('Legacy programming command failed (%s): %s\n%s' %
                                     (status, command, error or output))
        return output

    # All identity and file checks precede the first device mutation.
    remote = shlex.quote(report['remote_bitstream'])
    device.end()
    try:
        checked('rw && mkdir -p /opt/pyrpl')
        device.ssh.scp.put(report['local_bitstream'], report['remote_bitstream'])
        # Keep the staged file for diagnosis; verify transfer before programming.
        checked('test "$(sha256sum %s | cut -d " " -f 1)" = %s' %
                (remote, Z10_REPAIRED_BITSTREAM_SHA256))
        checked('killall nginx 2>/dev/null || true; '
                'systemctl stop redpitaya_nginx 2>/dev/null || true')
        checked('test -c /dev/xdevcfg && cat %s > /dev/xdevcfg' % remote)
        checked('nginx -p /opt/www/ 2>/dev/null || true; '
                'systemctl start redpitaya_nginx 2>/dev/null || true')
    finally:
        active_error = sys.exception()
        try:
            checked('ro')
        except Exception as restore_error:
            if active_error is None:
                raise
            active_error.add_note('Also failed to restore read-only mount: %s' % restore_error)
    report.update(read_only=False, programmed=True)
    return report
