import hashlib
import logging
import os
import sys
import sysctl
import time

from fenced.disks import Disk, Disks

logger = logging.getLogger(__name__)
LICENSE_FILE = '/data/license'


class Fence(object):

    def __init__(self, interval, force):
        self._interval = interval
        self._force = force
        self._disks = Disks(self)
        self.hostid = None

    def get_hostid(self):
        hostid = sysctl.filter('kern.hostid')[0].value | 1 << 31
        hostid &= 0xffffffff
        # Certain Supermicro systems does not supply hostid. Workaround by using a
        # blacklist and derive the value from the license.
        if hostid == 0xfe4ac89c and os.path.exists(LICENSE_FILE):
            with open(LICENSE_FILE, 'rb') as f:
                license = hashlib.md5(f.read()).hexdigest()[:8]
                if license[0] == '0':
                    license = f'8{license[-7:]}'
                hostid = int(license, 16)
        return hostid

    def load_disks(self):
        logger.debug('Loading disks')
        self._disks.clear()
        unsupported = []
        remote_keys = set()

        # TODO: blacklist disks used by dumpdev
        for i in sysctl.filter('kern.disks')[0].value.split():
            if not i.startswith('da'):
                continue
            try:
                disk = Disk(self, i)
                remote_keys.union(disk.get_keys()[1])
            except (OSError, RuntimeError):
                logger.debug('Disk %s does not support reservations.', disk)
                unsupported.append(i)
                continue
            self._disks.add(disk)

        if unsupported:
            logger.info('Disks does not support SCSI-3 PR: %s.', ' '.join(unsupported))

        return remote_keys

    def init(self):
        self.hostid = self.get_hostid()
        logger.info('Host ID: 0x%x.', self.hostid)

        remote_keys = self.load_disks()
        if not self._disks:
            logger.error('No disks available, exiting.')
            sys.exit(1)

        if not self._force:
            wait_interval = 2 * self._interval + 1
            logger.info('Waiting %d seconds to verify remote keys.', wait_interval)
            time.sleep(wait_interval)
            new_remote_keys = self._disks.get_keys()[1]
            if not new_remote_keys.issubset(remote_keys):
                logger.error('Remote keys have changed, exiting.')
                sys.exit(1)
            else:
                logger.info('Remote keys unchanged.')

        newkey = int(time.time()) & 0xffffffff
        failed_disks = self._disks.reset_keys(newkey)
        if failed_disks:
            rate = int((len(failed_disks) / len(self._disks)) * 100)
            if rate > 10:
                logger.error('%d% of the disks failed to reset SCSI reervations, exiting.', rate)
                sys.exit(1)
            for disk in failed_disks:
                self._disks.remove(disk)

        failed_disks = self._disks.reserve_key()
        if failed_disks:
            logger.error(
                'Failed to set SCSI reservation on %s',
                ' '.join([d.name for d in failed_disks]),
            )
            sys.exit(1)
        logger.info('SCSI reservation set on %d disks.', len(self._disks))

        return newkey

    def loop(self, key):
        firstkey = key
        while True:
            oldkey = key
            if key > 0xffffffff:
                key = 2
            else:
                key += 1

            logger.log(
                logging.INFO if oldkey == firstkey or key % 10 == 0 else logging.DEBUG,
                'Setting new key: 0x%x',
                key,
            )
            failed_disks = self._disks.set_keys(key)
            if failed_disks:
                if len(failed_disks) / len(self._disks) > 0.1:
                    sys.exit(1)
                for d in failed_disks:
                    self._disks.remove(d)

            time.sleep(self._interval)
