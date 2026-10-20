import json
from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'virtualmin-ftps/rotation-ui-lib.pl'
PERL=r'''
use utf8;use JSON::PP;
our($session_id,$remote_user);$session_id='test-session';$remote_user='root';
our $admin=1;
sub ftps_load_virtualmin {}
sub virtual_server::master_admin {return $admin;}
require $ARGV[0];
my $r=decode_json(do {local $/;<STDIN>});
$admin=$r->{admin};
my $ok=eval {
    my $token=ftps_rotation_token();
    $token='invalid' if $r->{invalid};
    $session_id='other-session' if $r->{other_session};
    ftps_rotation_post($r->{method},$token);1;
};
print encode_json({ok=>$ok?1:0,error=>"$@"});
'''
class RotationAccess(unittest.TestCase):
    def check(self,**kw):
        p=subprocess.run(['perl','-e',PERL,str(HELPER)],input=json.dumps(dict(admin=1,method='POST',**kw)) if 'admin' not in kw and 'method' not in kw else json.dumps(dict({'admin':1,'method':'POST'},**kw)),capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);return json.loads(p.stdout)
    def test_valid_admin_post(self):self.assertEqual(self.check()['ok'],1)
    def test_customer_denied(self):self.assertEqual(self.check(admin=0)['ok'],0)
    def test_get_save_denied(self):self.assertEqual(self.check(method='GET')['ok'],0)
    def test_bad_token_denied(self):self.assertEqual(self.check(invalid=True)['ok'],0)
    def test_token_bound_to_session(self):self.assertEqual(self.check(other_session=True)['ok'],0)
    def test_menu_label_emits_valid_utf8(self):
        program=r'''
use utf8;use Encode ();
sub ftps_load_virtualmin {}
sub virtual_server::master_admin {return 1;}
my $s=do{local $/;open(my $f,'<:utf8',$ARGV[0])or die $!;<$f>};
$s=~/(sub feature_links\b.*?)(?=sub feature_webmin)/s or die 'missing';
eval $1;die $@ if $@;
my @links=feature_links({id=>'1','virtualmin-ftps'=>1});
print $links[0]->{desc};
'''
        p=subprocess.run(['perl','-e',program,str(ROOT/'virtualmin-ftps/virtual_feature.pl')],capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(p.stdout.decode('utf-8'),'FTPS prüfen')
