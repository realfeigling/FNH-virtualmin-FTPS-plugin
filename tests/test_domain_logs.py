import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import grp

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ftps_engine', ROOT / 'virtualmin-ftps/engine.py')
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class DomainLogs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / 'domain'
        self.home.mkdir()
        self.group = grp.getgrgid(os.getgid()).gr_name
        self.d = dict(id='1', dom='one.example', ip='192.0.2.1',
                      group=self.group, home=str(self.home), cert='/cert', key='/key',
                      suspended=False, kind='RSA', fingerprint='same', has_ca=False,
                      certificate_source='website')
        self.c = dict(state_dir=str(self.root), managed_file=str(self.root / 'managed'),
                      proftpd_conf='/unused', mode='live', passive_ports=[49152, 65534])
        self.engine = e.Engine(self.c)

    def state(self, legacy=False):
        d = dict(self.d)
        if legacy:
            d.pop('home')
        state = dict(domains={'1': d}, pending={}, server_fqdn='server.example')
        (self.root / 'state.json').write_text(json.dumps(state))
        self.engine.managed.write_bytes(e.render_state(state, self.c))
        return state

    def execute(self, apply=False, operation='reconcile'):
        request = dict(operation=operation, domains=[{
            k: v for k, v in self.d.items()
            if k not in ('kind', 'fingerprint', 'has_ca', 'certificate_source')}])
        with patch.object(e, 'scan', return_value=(
                'Port 0\nDefaultServer off\n', [], [], [], 1)), \
             patch.object(e, 'certificate', return_value=('RSA', 'same', False)), \
             patch.object(e, 'server_fqdn', return_value='server.example'), \
             patch.object(self.engine, 'validate_config'), \
             patch.object(self.engine, 'reload'):
            return self.engine._execute(request, apply)

    def test_render_two_domains(self):
        second = dict(self.d, id='2', dom='two.example', home=str(self.root / 'two'))
        data = e.render({'1': self.d, '2': second}, self.c, identity='server.example').decode()
        for d in (self.d, second):
            block = data.split('<VirtualHost ')[1 if d['id'] == '1' else 2]
            self.assertIn('ExtendedLog ' + d['home'] + '/logs/ftp.log ALL\n', block)
            self.assertIn('TransferLog ' + d['home'] + '/logs/xferlog\n', block)
        self.assertEqual(data.count('ServerIdent on "server.example"'), 2)
        self.assertEqual(data.count('AllowOverwrite on\n'), 2)
        self.assertIn('ServerName "one.example"', data)

    def test_invalid_home(self):
        for home in ('', '/', 'relative', '/a/../b', '/a//b', '/a/', '/a\nInjected', '/a b'):
            with self.subTest(home=home), self.assertRaises(ValueError):
                e.validate_home(home)

    def test_missing_home_descriptor(self):
        d = dict(self.d)
        for k in ('home', 'kind', 'fingerprint', 'has_ca', 'certificate_source'):
            d.pop(k)
        with self.assertRaises(ValueError):
            e.normalize(d)

    def test_create_and_preserve(self):
        e.prepare_logs({'1': self.d})
        for name in ('ftp.log', 'xferlog'):
            p = self.home / 'logs' / name
            self.assertTrue(p.is_file())
            self.assertEqual(p.stat().st_mode & 0o777, 0o640)
            self.assertEqual(p.stat().st_uid, 0)
            p.write_text('existing records\n')
        e.prepare_logs({'1': self.d})
        self.assertEqual((self.home / 'logs/ftp.log').read_text(), 'existing records\n')

    def test_log_symlink_rejected(self):
        (self.home / 'logs').mkdir()
        target = self.root / 'target'
        target.write_text('preserve')
        (self.home / 'logs/ftp.log').symlink_to(target)
        with self.assertRaises(OSError):
            e.prepare_logs({'1': self.d})
        self.assertEqual(target.read_text(), 'preserve')

    def test_directory_symlink_rejected(self):
        target = self.root / 'target'
        target.mkdir()
        (self.home / 'logs').symlink_to(target)
        with self.assertRaises(OSError):
            e.prepare_logs({'1': self.d})
        self.assertEqual(list(target.iterdir()), [])

    def test_home_symlink_rejected(self):
        link = self.root / 'link'
        link.symlink_to(self.home)
        with self.assertRaises(OSError):
            e.prepare_logs({'1': dict(self.d, home=str(link))})

    def test_hardlink_rejected(self):
        (self.home / 'logs').mkdir()
        target = self.root / 'target'
        target.write_text('preserve')
        os.link(target, self.home / 'logs/ftp.log')
        with self.assertRaises(ValueError):
            e.prepare_logs({'1': self.d})
        self.assertEqual(target.read_text(), 'preserve')

    def test_world_writable_logs_rejected(self):
        (self.home / 'logs').mkdir()
        (self.home / 'logs').chmod(0o777)
        with self.assertRaises(ValueError):
            e.prepare_logs({'1': self.d})

    def test_group_writable_file_rejected(self):
        e.prepare_logs({'1': self.d})
        (self.home / 'logs/ftp.log').chmod(0o660)
        with self.assertRaises(ValueError):
            e.prepare_logs({'1': self.d})

    def test_duplicate_home_rejected(self):
        with self.assertRaises(ValueError):
            e.prepare_logs({'1': self.d, '2': dict(self.d, id='2')})

    def test_legacy_render_unchanged(self):
        state = self.state(legacy=True)
        self.assertNotIn(b'ExtendedLog', e.render_state(state, self.c))
        self.assertNotIn(b'TransferLog', e.render_state(state, self.c))

    def test_preview_no_files_no_state_change(self):
        self.state(legacy=True)
        before = self.engine.managed.read_bytes()
        state_before = (self.root / 'state.json').read_bytes()
        result = self.execute(False)
        self.assertTrue(result['changed'])
        self.assertFalse(result['applied'])
        self.assertFalse((self.home / 'logs').exists())
        self.assertEqual(self.engine.managed.read_bytes(), before)
        self.assertEqual((self.root / 'state.json').read_bytes(), state_before)

    def test_migration_idempotence_delete_retains_logs(self):
        self.state(legacy=True)
        self.assertTrue(self.execute(True)['applied'])
        first = self.engine.managed.read_bytes()
        self.assertIn(b'ExtendedLog', first)
        self.assertEqual(e.load_json(self.root / 'state.json')['domains']['1']['home'], str(self.home))
        (self.home / 'logs/ftp.log').write_text('records')
        self.assertFalse(self.execute(True)['changed'])
        request = {'operation': 'delete', 'id': '1'}
        with patch.object(e, 'scan', return_value=('Port 0\nDefaultServer off\n', [], [], [], 1)), \
             patch.object(self.engine, 'validate_config'), patch.object(self.engine, 'reload'):
            self.engine._execute(request, True)
        self.assertEqual((self.home / 'logs/ftp.log').read_text(), 'records')

    def test_foreign_changes_refused_before_log_creation(self):
        self.state(legacy=True)
        self.engine.managed.write_bytes(self.engine.managed.read_bytes() + b'# foreign\n')
        with self.assertRaisesRegex(ValueError, 'drift'):
            self.execute(True)
        self.assertFalse((self.home / 'logs').exists())

    def test_overwrite_migration_preserves_logs_and_permissions(self):
        self.state()  # 0.1.10: logs exist, overwrite flag absent.
        e.prepare_logs({'1': self.d})
        log = self.home / 'logs/ftp.log'
        log.write_text('keep records')
        before_mode = log.stat().st_mode
        before = self.engine.managed.read_bytes()
        self.assertNotIn(b'AllowOverwrite', before)
        self.assertTrue(self.execute(False)['changed'])
        self.assertEqual(self.engine.managed.read_bytes(), before)
        self.assertTrue(self.execute(True)['applied'])
        self.assertIn(b'AllowOverwrite on\n', self.engine.managed.read_bytes())
        self.assertTrue(e.load_json(self.root / 'state.json')['allow_overwrite'])
        self.assertEqual(log.read_text(), 'keep records')
        self.assertEqual(log.stat().st_mode, before_mode)
        self.assertFalse(self.execute(True)['changed'])

    def greeting_only_legacy_state(self, identity='server.example'):
        state = self.state(legacy=True)
        state.pop('server_fqdn')
        (self.root / 'state.json').write_text(json.dumps(state))
        self.engine.managed.write_bytes(e.render(
            state['domains'], self.c, identity=identity, allow_overwrite=False))
        return state

    def test_legacy_server_greeting_without_state_migrates(self):
        self.greeting_only_legacy_state()
        before = self.engine.managed.read_bytes()
        state_before = (self.root / 'state.json').read_bytes()
        result = self.execute(False, operation='use-website-certificates')
        self.assertTrue(result['changed'])
        self.assertFalse(result['applied'])
        self.assertEqual(self.engine.managed.read_bytes(), before)
        self.assertEqual((self.root / 'state.json').read_bytes(), state_before)
        self.assertFalse((self.home / 'logs').exists())
        self.assertTrue(self.execute(True, operation='use-website-certificates')['applied'])
        state = e.load_json(self.root / 'state.json')
        self.assertEqual(state['server_fqdn'], 'server.example')
        self.assertTrue(state['allow_overwrite'])
        self.assertEqual(state['domains']['1']['home'], str(self.home))
        self.assertIn(b'ExtendedLog', self.engine.managed.read_bytes())
        self.assertIn(b'AllowOverwrite on', self.engine.managed.read_bytes())
        self.assertFalse(self.execute(True, operation='use-website-certificates')['changed'])

    def test_legacy_greeting_migration_rejects_other_changes(self):
        self.greeting_only_legacy_state()
        before = self.engine.managed.read_bytes().replace(
            b'PassivePorts 49152 65534', b'PassivePorts 50000 50100')
        self.engine.managed.write_bytes(before)
        with self.assertRaisesRegex(ValueError, 'drift'):
            self.execute(True, operation='use-website-certificates')
        self.assertEqual(self.engine.managed.read_bytes(), before)
        self.assertFalse((self.home / 'logs').exists())

    def test_legacy_greeting_migration_rejects_other_hostname(self):
        self.greeting_only_legacy_state(identity='other.example')
        before = self.engine.managed.read_bytes()
        with self.assertRaisesRegex(ValueError, 'drift'):
            self.execute(False, operation='use-website-certificates')
        self.assertEqual(self.engine.managed.read_bytes(), before)

    def test_reload_failure_restores_config_and_state(self):
        old = self.state(legacy=True)
        before = self.engine.managed.read_bytes()
        new = dict(old, domains={'1': self.d})
        with patch.object(self.engine, 'validate_config'), \
             patch.object(self.engine, 'reload', side_effect=[ValueError('reload failed'), None]), \
             self.assertRaisesRegex(ValueError, 'reload failed'):
            self.engine.commit(new, e.render_state(new, self.c))
        self.assertEqual(self.engine.managed.read_bytes(), before)
        self.assertEqual(e.load_json(self.root / 'state.json'), old)
        self.assertTrue((self.home / 'logs/ftp.log').exists())


if __name__ == '__main__':
    unittest.main()
