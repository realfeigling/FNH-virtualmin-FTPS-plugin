import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
PERL=r"""
use utf8;
use JSON::PP;
our $admin=0;
sub ftps_load_virtualmin {}
sub virtual_server::master_admin {return $admin;}
my $src;{local $/;open(my $fh,'<:utf8',$ARGV[0]) or die $!;$src=<$fh>;}
$src=~/(sub feature_links\b.*?)(?=sub feature_always_links)/s or die 'links not found';
eval $1;die $@ if $@;
my $in;{local $/;$in=decode_json(<STDIN>);}
$admin=$in->{admin};
my $d={id=>'1','virtualmin-ftps'=>1};
my @links=feature_links($d);
my @acl=feature_webmin($d,[{id=>'2','virtualmin-ftps'=>1},{id=>'3','virtualmin-ftps'=>0}]);
print encode_json({links=>\@links,acl=>\@acl});
"""
class LogMenu(unittest.TestCase):
    def result(self,admin=0):
        p=subprocess.run(['perl','-e',PERL,str(ROOT/'virtualmin-ftps/virtual_feature.pl')],
                         input=json.dumps({'admin':admin}),text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);return json.loads(p.stdout)
    def test_customer_menu_has_two_readonly_log_links(self):
        r=self.result();self.assertEqual(len(r['links']),2)
        self.assertEqual({l['cat'] for l in r['links']},{'logs'})
        self.assertEqual({l['page'] for l in r['links']},
                         {'logs.cgi?dom=1&log=ftp','logs.cgi?dom=1&log=transfer'})
    def test_admin_keeps_inspection_link(self):
        self.assertEqual(len(self.result(1)['links']),3)
    def test_grants_only_active_domain_ids(self):
        r=self.result()['acl'][0]
        self.assertEqual(r[0],'virtualmin-ftps')
        self.assertEqual(r[1],{'logs':1,'doms':'1 2','noconfig':1})
    def test_refresh_updates_only_ftps_module_for_actual_owners(self):
        program=r"""
use JSON::PP;
our (@added,%saved,$cleared);
sub ftps_load_virtualmin {}
sub virtual_server::require_acl {}
sub acl::list_users { return ({name=>'ownerA'},{name=>'ownerB'}); }
our %domains=(
  1=>{id=>'1',user=>'ownerA',webmin=>1,'virtualmin-ftps'=>1},
  2=>{id=>'2',user=>'ownerA',parent=>'1','virtualmin-ftps'=>1},
  3=>{id=>'3',user=>'ownerB',webmin=>1,'virtualmin-ftps'=>1},
  4=>{id=>'4',user=>'ownerB',webmin=>1,'virtualmin-ftps'=>0});
sub virtual_server::list_domains {return values %domains;}
sub virtual_server::get_domain {return $domains{$_[0]};}
sub virtual_server::add_user_module_acl {push(@added, [@_]);}
sub virtual_server::clear_links_cache {$cleared++;}
sub save_module_acl {my($acl,$user,$mod)=@_;$saved{$user}={mod=>$mod,acl=>$acl};}
my $src;{local $/;open(my $fh,'<',$ARGV[0]) or die $!;$src=<$fh>;}
$src=~/(sub ftps_refresh_log_access\b.*?)(?=sub ftps_refresh_menu)/s or die 'refresh missing';
eval $1;die $@ if $@;
ftps_refresh_log_access();
print encode_json({added=>\@added,saved=>\%saved,cleared=>$cleared});
"""
        p=subprocess.run(['perl','-e',program,str(ROOT/'virtualmin-ftps/virtualmin-ftps-lib.pl')],
                         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);r=json.loads(p.stdout)
        self.assertEqual(r['saved']['ownerA']['acl']['doms'],'1 2')
        self.assertEqual(r['saved']['ownerB']['acl']['doms'],'3')
        self.assertEqual({x[1] for x in r['added']},{'virtualmin-ftps'})
        self.assertEqual(r['cleared'],1)

    def test_plugin_library_syntax_with_webmin_import_stub(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            Path(temp,'WebminCore.pm').write_text('package WebminCore; sub import {} 1;')
            p=subprocess.run(['perl','-I'+temp,'-c',
                              str(ROOT/'virtualmin-ftps/virtualmin-ftps-lib.pl')],
                             capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)

if __name__=='__main__':unittest.main()
