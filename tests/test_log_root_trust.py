import stat
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from test_domain_logs import e

class LogRootTrust(unittest.TestCase):
    def check(self, uid=104, group='syslog', mode=0o775, log_path=True):
        def metadata(p):
            return NS(st_mode=stat.S_IFDIR | (mode if str(p)=='/var/log' else 0o755),
                      st_uid=0,st_gid=110)
        with patch.object(Path,'lstat',metadata),patch('grp.getgrgid',return_value=NS(gr_name=group,gr_mem=['logger'])),patch('pwd.getpwall',return_value=[NS(pw_name='logger',pw_uid=uid,pw_gid=110)]):
            e.trusted('/var/log/virtualmin-ftps-logs',log_path=log_path)

    def test_system_logging_group_allowed(self): self.check()
    def test_customer_member_denied(self):
        with self.assertRaises(ValueError): self.check(uid=1002)
    def test_unknown_writable_group_denied(self):
        with self.assertRaises(ValueError): self.check(group='customers')
    def test_world_write_denied(self):
        with self.assertRaises(ValueError): self.check(mode=0o777)
    def test_general_trust_not_relaxed(self):
        with self.assertRaises(ValueError): self.check(log_path=False)
