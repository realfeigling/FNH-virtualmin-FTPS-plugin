import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from test_domain_logs import ProtectedLogs
import test_logrotate as rotation_tests
m = rotation_tests.m

class RotationAPI(unittest.TestCase):
    setUp=ProtectedLogs.setUp
    prepare=ProtectedLogs.prepare

    def call(self, request):
        config=self.root/'engine.json'
        if not config.exists(): config.write_text(json.dumps(self.c))
        rule=self.root/'logrotate.d/plugin';rule.parent.mkdir(exist_ok=True)
        with patch.object(m,'CONFIG',config),patch.object(m,'LOGROTATE_FILE',rule),patch.object(m,'get_config',return_value=self.c):
            return m.rotation_api(request)

    def fixture(self):
        self.prepare()
        (self.root/'state.json').write_text(json.dumps({'domains':{'1':self.protected}}))
        return self.call({'operation':'read'})

    def request(self, op, scope='', policy=None):
        return dict(operation=op,scope=scope,policy=policy,
                    revision=m.rotation_revision(self.c))

    def test_read_exposes_no_server_configuration(self):
        r=self.fixture()
        self.assertNotIn('managed_file',r);self.assertNotIn('state_dir',r)
        self.assertEqual(r['domains']['1']['domain'],'one.example')

    def test_preview_writes_neither_rule_nor_configuration(self):
        self.fixture();before=(self.root/'engine.json').read_bytes()
        r=self.call(self.request('preview',policy={'interval':'weekly','rotate':52}))
        self.assertFalse(r['saved']);self.assertEqual((self.root/'engine.json').read_bytes(),before)
        self.assertFalse((self.root/'logrotate.d/plugin').exists())

    def test_save_preserves_unrelated_fields_and_domain_override(self):
        self.fixture();self.c['logrotate']={'domains':{'1':{'rotate':12}}}
        self.call(self.request('save',policy={'interval':'weekly','rotate':52,'maxsize':None}))
        new=json.loads((self.root/'engine.json').read_text())
        self.assertEqual(new['managed_file'],self.c['managed_file'])
        self.assertEqual(new['logrotate']['domains']['1'],{'rotate':12})
        self.assertIn('rotate 12',(self.root/'logrotate.d/plugin').read_text())

    def test_domain_save_and_return_to_inheritance(self):
        self.fixture()
        self.call(self.request('save','1',{'interval':'daily','rotate':365,'maxsize':None}))
        self.c=json.loads((self.root/'engine.json').read_text())
        self.assertEqual(self.c['logrotate']['domains']['1']['rotate'],365)
        self.call(self.request('save','1',None))
        new=json.loads((self.root/'engine.json').read_text())
        self.assertNotIn('1',new['logrotate']['domains'])

    def test_stale_revision_and_unknown_host_rejected(self):
        self.fixture()
        for changes in ({'revision':'stale'},{'scope':'../../etc/passwd'},{'scope':'2'}):
            request=self.request('save',policy={'rotate':52});request.update(changes)
            with self.assertRaises(ValueError):self.call(request)
        self.assertFalse((self.root/'logrotate.d/plugin').exists())

    def test_config_write_failure_restores_both_files(self):
        self.fixture();rule=self.root/'logrotate.d/plugin';rule.write_text(m.LOGROTATE_MARKER+'# previous rule\n')
        before_config=(self.root/'engine.json').read_bytes();before_rule=rule.read_bytes()
        real=m.engine.atomic;failed=False
        def fail_once(path,data,mode=0o600):
            nonlocal failed
            if Path(path)==self.root/'engine.json' and not failed:
                failed=True;raise OSError('simulated disk error')
            return real(path,data,mode)
        with patch.object(m.engine,'atomic',side_effect=fail_once),self.assertRaises(OSError):
            self.call(self.request('save',policy={'rotate':52}))
        self.assertEqual((self.root/'engine.json').read_bytes(),before_config)
        self.assertEqual(rule.read_bytes(),before_rule)

    def test_unknown_fields_and_actions_rejected(self):
        self.fixture()
        for request in ({'operation':'read','path':'/etc/shadow'}, {'operation':'run'},
                        self.request('save',policy={'postrotate':'command'})):
            with self.assertRaises(ValueError):self.call(request)

del ProtectedLogs
