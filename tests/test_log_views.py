import sys
import importlib.util
import os
import errno
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'virtualmin-ftps'))
from log_views import prepare_views, unmount_view, mount_entry
from test_domain_logs import ProtectedLogs, e

class BindViews(unittest.TestCase):
    setUp = ProtectedLogs.setUp
    prepare = ProtectedLogs.prepare
    old_logs = ProtectedLogs.old_logs

    def view(self):
        return dict(self.protected, log_view=str(self.home / 'logs/ftps'))

    def test_real_readonly_bind_visible_inside_ftp_chroot(self):
        self.prepare()
        f = self.path / 'ftp.log'
        f.write_text('protected log record')
        d = self.view()
        prepare_views({'1':d})
        self.addCleanup(lambda: unmount_view(d))
        with f.open('a') as writer:
            writer.write(' live FTP event')
        entry = mount_entry(d['log_view'])
        self.assertTrue({'ro','nosuid','nodev','noexec'} <= entry)
        script = '''import os,sys
from pathlib import Path
os.chroot(sys.argv[1]); os.chdir('/')
os.setgroups([int(sys.argv[3])]);os.setgid(int(sys.argv[3]));os.setuid(int(sys.argv[2]))
p=Path('/logs/ftps/ftp.log')
assert p.read_text()=='protected log record live FTP event'
for op in (lambda:p.unlink(),lambda:p.rename(p.with_name('gone')),
           lambda:p.write_text('overwrite')):
    try:op()
    except OSError as err:
        assert err.errno in (1,13,30), str(err)
    else:raise SystemExit('write/delete succeeded')
'''
        result=subprocess.run([sys.executable,'-c',script,str(self.home),
                               str(self.user.pw_uid),str(self.user.pw_gid)],
                              capture_output=True,text=True,cwd='/')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(f.read_text(),'protected log record live FTP event')
        self.assertEqual(prepare_views({'1':d}),[])

    def test_unmount_preserves_protected_originals(self):
        self.prepare()
        d=self.view()
        (self.path/'ftp.log').write_text('preserve')
        prepare_views({'1':d})
        self.addCleanup(lambda:unmount_view(d))
        unmount_view(d)
        self.assertIsNone(mount_entry(d['log_view']))
        self.assertEqual((self.path/'ftp.log').read_text(),'preserve')

    def test_relocated_view_is_safely_unmounted(self):
        self.prepare()
        d=self.view();prepare_views({'1':d})
        self.addCleanup(lambda:unmount_view(d))
        moved=self.home/'renamed-logs'
        (self.home/'logs').rename(moved)
        self.assertIsNotNone(mount_entry(str(moved/'ftps')))
        unmount_view(d)
        self.assertIsNone(mount_entry(str(moved/'ftps')))
        self.assertTrue((self.path/'ftp.log').exists())

    def test_preview_does_not_create_customer_view(self):
        self.prepare()
        self.assertEqual(prepare_views({'1':self.view()},apply=False),[])
        self.assertFalse((self.home/'logs').exists())

    def test_mountpoint_symlink_refused(self):
        self.prepare();logs=self.home/'logs';logs.mkdir()
        (logs/'ftps').symlink_to(self.path)
        with self.assertRaises(OSError):prepare_views({'1':self.view()},apply=False)

    def test_nonempty_customer_directory_not_hidden(self):
        self.prepare();p=self.home/'logs/ftps';p.mkdir(parents=True)
        (p/'customer-file').write_text('preserve')
        with self.assertRaises(ValueError):prepare_views({'1':self.view()},apply=False)
        self.assertEqual((p/'customer-file').read_text(),'preserve')

    def test_foreign_bind_not_unmounted(self):
        self.prepare();d=self.view();p=Path(d['log_view']);p.mkdir(parents=True)
        with patch('log_views.mount_entry',return_value={'ro'}),self.assertRaises(ValueError):
            unmount_view(d)

    def test_old_var_log_default_is_migrated_without_touching_var_log(self):
        c=dict(self.c,log_root='/var/log/virtualmin-ftps')
        self.assertEqual(e.effective_log_root(c),
                         str(Path(self.c['state_dir']).parent /
                             (Path(self.c['state_dir']).name+'-logs')))
        self.assertNotIn('/var/log',e.protected_log_dir('1',c))


class LogReader(unittest.TestCase):
    setUp = ProtectedLogs.setUp
    prepare = ProtectedLogs.prepare

    def setup_log(self,text):
        self.prepare()
        (self.path/'ftp.log').write_text(text)
        state={'domains':{'1':self.protected},'pending':{}}
        (self.root/'state.json').write_text(__import__('json').dumps(state))

    def test_bounded_read_only_log_response(self):
        self.setup_log('\n'.join(str(i) for i in range(500)))
        before=(self.path/'ftp.log').read_bytes()
        r=self.engine.execute({'operation':'read-log','id':'1','log':'ftp'})
        self.assertEqual(r['scope']['id'],'1')
        self.assertEqual(len(r['text'].splitlines()),200)
        self.assertTrue(r['truncated'])
        self.assertEqual((self.path/'ftp.log').read_bytes(),before)

    def test_no_path_or_unknown_log_allowed(self):
        for req in ({'operation':'read-log','id':'1','log':'../../etc/passwd'},
                    {'operation':'read-log','id':'1','log':'ftp','path':'/etc/passwd'},
                    {'operation':'read-log','id':'../2','log':'ftp'}):
            with self.assertRaises(ValueError):self.engine.execute(req)

    def test_apply_flag_denied_for_log_view(self):
        with self.assertRaises(ValueError):
            self.engine.execute({'operation':'read-log','id':'1','log':'ftp'},apply=True)

    def test_other_domain_not_read(self):
        self.setup_log('private')
        with self.assertRaises(ValueError):
            self.engine.execute({'operation':'read-log','id':'2','log':'ftp'})

del ProtectedLogs
if __name__=='__main__':unittest.main()
