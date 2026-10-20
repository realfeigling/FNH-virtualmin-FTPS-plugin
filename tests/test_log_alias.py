import os
from pathlib import Path
import stat
from types import SimpleNamespace as NS
from unittest.mock import patch
import unittest
from test_domain_logs import ProtectedLogs, e
from log_views import resolve_log_source, readonly_bind, unmount_view

class LogAlias(unittest.TestCase):
    setUp=ProtectedLogs.setUp
    prepare=ProtectedLogs.prepare

    def alias(self, uid=0):
        self.prepare()
        original_lstat=Path.lstat
        original_islink=Path.is_symlink
        original_readlink=os.readlink
        patches=[patch.object(Path,'lstat',lambda p,*a,**k: NS(st_mode=stat.S_IFLNK|0o777,st_uid=uid) if str(p)=='/var/log' else original_lstat(p,*a,**k)),
                 patch.object(Path,'is_symlink',lambda p: str(p)=='/var/log' or original_islink(p)),
                 patch('os.readlink',lambda p,*a,**k: str(self.path.parent) if str(p)=='/var/log' else original_readlink(p,*a,**k))]
        for p in patches:p.start();self.addCleanup(p.stop)

    def test_root_alias_resolves(self):
        self.alias()
        self.assertEqual(resolve_log_source('/var/log/1'),str(self.path))
        e.trusted('/var/log',log_path=True)

    def test_general_trust_rejects_alias(self):
        self.alias()
        with self.assertRaises(ValueError):e.trusted('/var/log')

    def test_customer_owned_alias_refused(self):
        self.alias(uid=self.user.pw_uid)
        with self.assertRaises(ValueError):resolve_log_source('/var/log/1')

    def test_customer_writable_target_refused(self):
        self.alias();self.path.parent.chmod(0o777)
        with self.assertRaises(ValueError):resolve_log_source('/var/log/1')

    def test_nested_target_symlink_refused(self):
        self.alias();dest=self.root/'other';dest.mkdir();link=self.root/'link';link.symlink_to(dest)
        with patch('os.readlink',return_value=str(link)),self.assertRaises(ValueError):
            resolve_log_source('/var/log/1')

    def test_real_readonly_mount_from_alias(self):
        self.alias();target=self.root/'view';target.mkdir();fd=os.open(target,os.O_RDONLY|os.O_DIRECTORY)
        try:readonly_bind('/var/log/1',fd,str(target))
        finally:os.close(fd)
        self.addCleanup(lambda: __import__('log_views').unmount_fd(os.open(target,os.O_PATH|os.O_DIRECTORY)))
        self.assertEqual(target.stat().st_ino,self.path.stat().st_ino)
        self.assertTrue({'ro','nosuid','nodev','noexec'} <= __import__('log_views').mount_entry(str(target)))

    def test_historical_source_uses_alias(self):
        self.alias();(self.path/'ftp.log').write_text('history')
        fd=e.source_log('/var/log/1/ftp.log',self.d,self.user.pw_gid)
        try:self.assertEqual(os.read(fd,100),b'history')
        finally:os.close(fd)

del ProtectedLogs
