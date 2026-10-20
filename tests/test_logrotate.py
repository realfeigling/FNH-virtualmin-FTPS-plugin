import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch
from test_domain_logs import ProtectedLogs

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ftps_manage_tests',ROOT/'virtualmin-ftps/manage.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LogRotation(unittest.TestCase):
    setUp=ProtectedLogs.setUp
    prepare=ProtectedLogs.prepare

    def config(self):
        self.prepare()
        conf=self.root/'rotation.conf';conf.write_bytes(m.logrotate_config(self.c))
        return conf

    def rotate(self,conf):
        result=subprocess.run(['/usr/sbin/logrotate','--force','--state',str(self.root/'rotation.state'),str(conf)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_real_rotation_keeps_open_writer_inode_owner_and_archives(self):
        conf=self.config();p=self.path/'ftp.log';p.write_text('first event\n')
        other=self.path/'xferlog';other.write_text('transfer event\n')
        before=p.stat();writer=p.open('a')
        try:
            self.rotate(conf)
            self.assertEqual(p.stat().st_ino,before.st_ino)
            self.assertEqual(p.read_text(),'')
            self.assertEqual((self.path/'ftp.log.1').read_text(),'first event\n')
            self.assertEqual((self.path/'xferlog.1').read_text(),'transfer event\n')
            writer.write('after rotation\n');writer.flush()
            self.assertEqual(p.read_text(),'after rotation\n')
            self.rotate(conf)
            self.assertEqual(__import__('gzip').open(self.path/'ftp.log.2.gz','rt').read(),'first event\n')
            for f in self.path.iterdir():
                st=f.stat();self.assertEqual((st.st_uid,st.st_gid,st.st_mode&0o777),(0,self.user.pw_gid,0o640))
        finally:writer.close()

    def test_preview_installs_nothing_and_does_not_rotate(self):
        self.prepare();p=self.path/'ftp.log';p.write_text('keep')
        destination=self.root/'logrotate.d/plugin';destination.parent.mkdir()
        with patch.object(m,'get_config',return_value=self.c),patch.object(m,'LOGROTATE_FILE',destination),contextlib.redirect_stdout(io.StringIO()):
            m.configure_logrotate(False)
        self.assertFalse(destination.exists());self.assertEqual(p.read_text(),'keep')

    def test_install_idempotent_and_foreign_file_preserved(self):
        self.prepare();destination=self.root/'logrotate.d/plugin';destination.parent.mkdir()
        with patch.object(m,'get_config',return_value=self.c),patch.object(m,'LOGROTATE_FILE',destination),contextlib.redirect_stdout(io.StringIO()):
            m.configure_logrotate(True);first=destination.read_bytes();m.configure_logrotate(True)
            self.assertEqual(first,destination.read_bytes());self.assertEqual(destination.stat().st_mode&0o777,0o644)
            destination.write_text('# foreign settings\n')
            with self.assertRaises(ValueError):m.configure_logrotate(True)
            self.assertEqual(destination.read_text(),'# foreign settings\n')

    def test_no_reloads_and_no_customer_home_paths(self):
        data=self.config().read_text()
        self.assertNotIn(str(self.home),data)
        self.assertNotIn('postrotate',data);self.assertNotIn('systemctl',data)
        self.assertIn('copytruncate',data);self.assertIn('rotate 14',data)
        self.assertIn('daily',data);self.assertIn('maxsize 100M',data)

    def test_customer_owned_rotation_root_refused(self):
        self.prepare();os.chown(self.path.parent,self.user.pw_uid,self.user.pw_gid)
        with self.assertRaises(ValueError):m.logrotate_config(self.c)

del ProtectedLogs
