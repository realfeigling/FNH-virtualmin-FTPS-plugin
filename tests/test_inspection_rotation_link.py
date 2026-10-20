import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from test_rotation_page import STUB
ROOT=Path(__file__).resolve().parents[1]

class InspectionRotationLink(unittest.TestCase):
    def page(self, domain=''):
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp,'engine.json');config.write_text('{}')
            source=(ROOT/'virtualmin-ftps/index.cgi').read_text().replace('/etc/webmin/virtualmin-ftps/engine.json',str(config))
            Path(tmp,'index.cgi').write_text(source)
            helper=str(ROOT/'virtualmin-ftps/rotation-ui-lib.pl')
            library=STUB.replace('__HELPER__',helper)+'''\nsub get_module_acl {return ();}\nsub foreign_available {return 1;}\nsub ftps_inspection_page {return '<p>Inspection</p>';}\n1;\n'''
            Path(tmp,'virtualmin-ftps-lib.pl').write_text(library)
            p=subprocess.run(['perl','index.cgi'],cwd=tmp,input=json.dumps({'dom':domain}).encode(),capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr.decode());return p.stdout.decode('utf-8')
    def test_inspection_link_keeps_selected_domain(self):
        html=self.page('1792423871587556')
        self.assertIn('href="rotation.cgi?dom=1792423871587556"',html)
        self.assertIn('Logrotation für diese Domain einstellen',html)
        self.assertNotIn('href="rotation.cgi"',html)
    def test_module_without_selected_domain_keeps_global_entry(self):
        html=self.page()
        self.assertIn('href="rotation.cgi"',html)
