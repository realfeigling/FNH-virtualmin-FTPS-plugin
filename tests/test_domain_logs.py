import importlib.util
import json
import os
from pathlib import Path
import pwd
import grp
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('engine', ROOT / 'virtualmin-ftps/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)

class ProtectedLogs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='ftps-protected-', dir='/run')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o755)
        self.user = pwd.getpwnam('nobody')
        self.group = grp.getgrgid(self.user.pw_gid).gr_name
        self.home = self.root / 'customer-home'
        self.home.mkdir()
        os.chown(self.home, self.user.pw_uid, self.user.pw_gid)
        self.c = dict(state_dir=str(self.root), managed_file=str(self.root/'managed'),
                      proftpd_conf='/unused', mode='live', passive_ports=[49152,65534],
                      log_root=str(self.root/'protected'))
        self.d = dict(id='1', dom='one.example', ip='192.0.2.1', user=self.user.pw_name,
                      group=self.group, home=str(self.home), cert='/cert', key='/key',
                      suspended=False, kind='RSA', fingerprint='same', has_ca=False,
                      certificate_source='website')
        self.protected = dict(self.d, log_dir=e.protected_log_dir('1', self.c))
        self.path = Path(self.protected['log_dir'])
        self.engine = e.Engine(self.c)

    def prepare(self, apply=True, old=None):
        e.prepare_logs({'1':self.protected}, self.c, apply=apply, old_domains=old)

    def old_logs(self, owner=None):
        logs=self.home/'logs'; logs.mkdir(exist_ok=True)
        os.chown(logs,self.user.pw_uid,self.user.pw_gid)
        for name in ('ftp.log','xferlog'):
            f=logs/name; f.write_text(name+' historical records\n')
            os.chown(f, self.user.pw_uid if owner is None else owner, self.user.pw_gid)
            f.chmod(0o644)
        return logs

    def state(self, old_greeting=False):
        state=dict(domains={'1':dict(self.d)},pending={},allow_overwrite=True,
                   allow_override=True,server_fqdn='server.example')
        if old_greeting: state.pop('server_fqdn')
        (self.root/'state.json').write_text(json.dumps(state))
        data=e.render_state(state,self.c)
        if old_greeting:
            data=e.render(state['domains'],self.c,identity='server.example')
        self.engine.managed.write_bytes(data)
        return state

    def execute(self, apply=False):
        request=dict(operation='use-website-certificates',domains=[{k:v for k,v in self.d.items()
                     if k not in ('kind','fingerprint','has_ca','certificate_source')}])
        with patch.object(e,'scan',return_value=('Port 0\nDefaultServer off\n',[],[],[],1)), \
             patch.object(e,'certificate',return_value=('RSA','same',False)), \
             patch.object(e,'server_fqdn',return_value='server.example'), \
             patch.object(self.engine,'validate_config'),patch.object(self.engine,'reload'):
            return self.engine._execute(request,apply)

    def test_new_logs_root_owned_group_readable(self):
        self.prepare()
        for name in ('ftp.log','xferlog'):
            st=(self.path/name).stat()
            self.assertEqual((st.st_uid,st.st_gid,st.st_mode&0o777),(0,self.user.pw_gid,0o640))
        self.assertEqual((self.path.stat().st_uid,self.path.stat().st_mode&0o777),(0,0o750))
        self.assertFalse((self.home/'logs').exists())

    def test_customer_cannot_delete_rename_or_write(self):
        self.prepare()
        script='''import os,sys
from pathlib import Path
p=Path(sys.argv[1]); root=p.parent
for action in (lambda:p.unlink(), lambda:p.rename(p.with_name('removed.log')),
               lambda:p.write_text('overwrite'),lambda:root.rename(root.with_name('removed-dir'))):
    try: action()
    except PermissionError: pass
    else: raise SystemExit('customer operation unexpectedly succeeded')
assert p.read_text()==''
'''
        def become_customer():
            os.setgroups([self.user.pw_gid]); os.setgid(self.user.pw_gid); os.setuid(self.user.pw_uid)
        result=subprocess.run([sys.executable,'-c',script,str(self.path/'ftp.log')],
                              capture_output=True,text=True,preexec_fn=become_customer,cwd='/')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_copy_customer_history_without_touching_source(self):
        logs=self.old_logs(); before={f:f.read_bytes() for f in logs.iterdir()}
        self.prepare(old={'1':self.d})
        for f,data in before.items():
            self.assertEqual(f.read_bytes(),data)
            self.assertEqual(f.stat().st_uid,self.user.pw_uid)
            self.assertEqual((self.path/f.name).read_bytes(),data)

    def test_copy_root_root_history(self):
        logs=self.old_logs(owner=0)
        for f in logs.iterdir():os.chown(f,0,0)
        self.prepare(old={'1':self.d})
        self.assertEqual((self.path/'ftp.log').read_text(),'ftp.log historical records\n')
        self.assertEqual((logs/'ftp.log').stat().st_gid,0)

    def test_existing_destination_never_truncated_or_duplicated(self):
        logs=self.old_logs(); self.prepare(old={'1':self.d})
        (logs/'ftp.log').write_text('different old records')
        self.prepare(old={'1':self.d})
        self.assertEqual((self.path/'ftp.log').read_text(),'ftp.log historical records\n')

    def test_preview_creates_nothing(self):
        self.old_logs(); self.prepare(False,{'1':self.d})
        self.assertFalse(Path(self.c['log_root']).exists())

    def test_preview_preserves_source_owner(self):
        logs=self.old_logs(); self.prepare(False,{'1':self.d})
        self.assertEqual((logs/'ftp.log').stat().st_uid,self.user.pw_uid)

    def test_historical_symlink_refused(self):
        logs=self.old_logs(); (logs/'ftp.log').unlink();(logs/'ftp.log').symlink_to('/etc/passwd')
        with self.assertRaises(OSError):self.prepare(False,{'1':self.d})

    def test_historical_hardlink_refused(self):
        logs=self.old_logs();os.link(logs/'ftp.log',logs/'second-link')
        with self.assertRaises(ValueError):self.prepare(False,{'1':self.d})

    def test_target_symlink_refused(self):
        self.prepare(); f=self.path/'ftp.log';f.unlink();f.symlink_to('/etc/passwd')
        with self.assertRaises(OSError):self.prepare()

    def test_target_hardlink_refused(self):
        self.prepare();os.link(self.path/'ftp.log',self.path/'second-link')
        with self.assertRaises(ValueError):self.prepare()

    def test_target_customer_owner_refused(self):
        self.prepare();os.chown(self.path/'ftp.log',self.user.pw_uid,self.user.pw_gid)
        with self.assertRaisesRegex(ValueError,'protected FTPS log'):self.prepare(False)

    def test_target_group_write_refused(self):
        self.prepare();(self.path/'ftp.log').chmod(0o660)
        with self.assertRaises(ValueError):self.prepare(False)

    def test_customer_owned_parent_refused(self):
        other=self.root/'customer-root';other.mkdir();os.chown(other,self.user.pw_uid,self.user.pw_gid)
        c=dict(self.c,log_root=str(other/'protected'))
        with self.assertRaisesRegex(ValueError,'root-controlled'):
            e.prepare_logs({'1':dict(self.d,log_dir=e.protected_log_dir('1',c))},c)

    def test_group_writable_root_refused(self):
        self.prepare();Path(self.c['log_root']).chmod(0o770)
        with self.assertRaises(ValueError):self.prepare(False)

    def test_invalid_root_path_refused(self):
        for root in ('relative','/','/var/log/../tmp'):
            with self.subTest(root=root),self.assertRaises(ValueError):e.protected_log_dir('1',{'log_root':root})

    def test_legacy_renderer_preserved(self):
        state=self.state();data=e.render_state(state,self.c)
        self.assertIn(str(self.home/'logs/ftp.log').encode(),data)
        self.assertNotIn(str(self.path).encode(),data)

    def test_render_protected_paths_and_customer_rules(self):
        data=e.render({'1':self.protected},self.c,identity='server.example')
        self.assertIn(f'ExtendedLog {self.path}/ftp.log ALL'.encode(),data)
        self.assertIn(b'AllowOverride on',data);self.assertIn(b'AllowOverwrite on',data)

    def test_migration_preview_then_apply(self):
        self.state();logs=self.old_logs();before=self.engine.managed.read_bytes()
        state_before=(self.root/'state.json').read_bytes()
        self.assertTrue(self.execute(False)['changed'])
        self.assertEqual(self.engine.managed.read_bytes(),before)
        self.assertEqual((self.root/'state.json').read_bytes(),state_before)
        self.assertFalse(self.path.exists())
        self.assertTrue(self.execute(True)['applied'])
        self.assertIn(str(self.path).encode(),self.engine.managed.read_bytes())
        self.assertEqual((self.path/'ftp.log').read_bytes(),(logs/'ftp.log').read_bytes())
        self.assertFalse(self.execute(True)['changed'])

    def test_missing_target_recreated_on_unchanged_apply(self):
        self.state();self.execute(True);(self.path/'ftp.log').unlink()
        self.assertFalse(self.execute(True)['changed'])
        self.assertTrue((self.path/'ftp.log').exists())

    def test_foreign_configuration_refused(self):
        self.state();self.engine.managed.write_bytes(self.engine.managed.read_bytes()+b'# foreign\n')
        with self.assertRaisesRegex(ValueError,'drift'):self.execute(True)
        self.assertFalse(self.path.exists())

    def test_old_greeting_migration_still_supported(self):
        self.state(old_greeting=True);self.assertTrue(self.execute(True)['applied'])
        self.assertEqual(e.load_json(self.root/'state.json')['server_fqdn'],'server.example')

    def test_reload_failure_restores_configuration_and_state(self):
        old=self.state();before=self.engine.managed.read_bytes()
        new=dict(old,domains={'1':self.protected})
        with patch.object(self.engine,'validate_config'), \
             patch.object(self.engine,'reload',side_effect=[ValueError('reload failed'),None]), \
             self.assertRaisesRegex(ValueError,'reload failed'):
            self.engine.commit(new,e.render_state(new,self.c))
        self.assertEqual(self.engine.managed.read_bytes(),before)
        self.assertEqual(e.load_json(self.root/'state.json'),old)
        self.assertTrue((self.path/'ftp.log').exists())

if __name__=='__main__':unittest.main()
