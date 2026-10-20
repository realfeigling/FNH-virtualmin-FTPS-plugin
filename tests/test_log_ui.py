import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
PERL=r"""
use strict;
use warnings;
use JSON::PP;
our (%acl,$allowed,$master,$called,$bad_reply);
sub ftps_load_virtualmin {}
sub get_module_acl {return %acl;}
sub virtual_server::get_domain {return {id=>$_[0],dom=>'one.example','virtualmin-ftps'=>1};}
sub virtual_server::can_edit_domain {return $allowed;}
sub virtual_server::master_admin {return $master;}
sub html_escape {my $s=$_[0];$s=~s/&/&amp;/g;$s=~s/</&lt;/g;$s=~s/>/&gt;/g;return $s;}
sub ftps_engine {
    my($req,$apply)=@_;
    die 'unexpected write' if $apply;
    $called++;
    return encode_json({scope=>{id=>$bad_reply?'2':$req->{id},domain=>'one.example'},
                        log=>$req->{log},text=>'<script>bad</script>'});
}
my $q;{local $/;$q=decode_json(<STDIN>);}
%acl=(logs=>$q->{logs},doms=>$q->{doms});
$allowed=$q->{allowed};$master=$q->{master};$bad_reply=$q->{bad_reply};$called=0;
require $ARGV[0];
my($html,$err);eval{$html=ftps_log_html(ftps_log_reply($q->{id},$q->{kind}));};$err=$@;
print encode_json({html=>$html||'',error=>$err||'',called=>$called});
"""

class LogUI(unittest.TestCase):
    def call(self,**kw):
        q=dict(logs=1,doms='1',allowed=1,master=0,id='1',kind='ftp',bad_reply=0);q.update(kw)
        r=subprocess.run(['perl','-e',PERL,str(ROOT/'virtualmin-ftps/log-ui-lib.pl')],
                         input=json.dumps(q),capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        return json.loads(r.stdout)
    def test_authorized_domain_and_html_escaping(self):
        r=self.call();self.assertEqual(r['error'],'');self.assertEqual(r['called'],1)
        self.assertIn('&lt;script&gt;',r['html']);self.assertNotIn('<script>',r['html'])
    def test_foreign_virtualmin_domain_denied_before_backend(self):
        r=self.call(allowed=0,doms='1 2');self.assertTrue(r['error']);self.assertEqual(r['called'],0)
    def test_module_acl_domain_denied_before_backend(self):
        r=self.call(id='2');self.assertTrue(r['error']);self.assertEqual(r['called'],0)
    def test_module_log_permission_required(self):
        r=self.call(logs=0);self.assertTrue(r['error']);self.assertEqual(r['called'],0)
    def test_invalid_selectors_denied(self):
        for q in ({'id':'../1'},{'kind':'../../etc/passwd'}):
            r=self.call(**q);self.assertTrue(r['error']);self.assertEqual(r['called'],0)
    def test_wrong_backend_domain_rejected(self):
        self.assertTrue(self.call(bad_reply=1)['error'])

if __name__=='__main__':unittest.main()
