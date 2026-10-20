import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('descriptor_engine', ROOT / 'virtualmin-ftps/engine.py')
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

PERL = r"""
use strict;
use warnings;
use JSON::PP;
sub ftps_load_virtualmin {}
sub virtual_server::domain_has_ssl { return 1; }
sub virtual_server::get_website_ssl_file {
    my ($d, $kind) = @_;
    return $kind eq 'ca' ? '' : '/'.$kind;
}
my $source;
{ local $/; open(my $fh, '<', $ARGV[0]) or die $!; $source = <$fh>; }
$source =~ /(sub ftps_descriptor\b.*?)(?=\nsub ftps_engine\b)/s
    or die "Descriptor not found";
eval $1;
die $@ if $@;
my $input;
{ local $/; $input = <STDIN>; }
my $result = ftps_descriptor(decode_json($input));
print encode_json($result);
"""


class VirtualminDescriptor(unittest.TestCase):
    def domain(self):
        return dict(id='1', dom='one.example', ip='192.0.2.1',
                    group='domain', dir=1, home='/data/www/pages/u607101601')

    def descriptor(self, domain):
        return subprocess.run(
            ['perl', '-e', PERL, str(ROOT / 'virtualmin-ftps/virtualmin-ftps-lib.pl')],
            input=json.dumps(domain), text=True, capture_output=True, check=False)

    def test_dir_feature_flag_and_real_home_reach_backend(self):
        for home in ('/data/www/pages/u607101601',
                     '/data/www/pages/u607101601/domains/sub.example'):
            with self.subTest(home=home):
                d = self.domain()
                d['home'] = home
                result = self.descriptor(d)
                self.assertEqual(result.returncode, 0, result.stderr)
                desc = json.loads(result.stdout)
                self.assertEqual(desc['home'], home)
                normalized = engine.normalize(desc)
                self.assertEqual(engine.log_paths(normalized),
                                 (home + '/logs/ftp.log', home + '/logs/xferlog'))

    def test_missing_home_refused_at_descriptor(self):
        d = self.domain()
        del d['home']
        result = self.descriptor(d)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('home directory', result.stderr)

    def test_disabled_directory_feature_refused(self):
        d = self.domain()
        d['dir'] = 0
        result = self.descriptor(d)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('home directory', result.stderr)


if __name__ == '__main__':
    unittest.main()
