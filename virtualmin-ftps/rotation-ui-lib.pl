use utf8;
use Digest::SHA qw(hmac_sha256_hex);

sub ftps_rotation_admin
{
&ftps_load_virtualmin();
die "Nur Hauptadministratoren dürfen die Logrotation einstellen.\n"
    if (!&virtual_server::master_admin());
}

sub ftps_rotation_token
{
die "Bitte für diese Einstellung mit einer Webmin-Sitzung anmelden.\n"
    if (!$main::session_id);
return hmac_sha256_hex('virtualmin-ftps/logrotation',
                      $main::session_id."\0".($main::remote_user || ''));
}

sub ftps_rotation_post
{
my ($method, $token) = @_;
&ftps_rotation_admin();
die "Speichern erfordert ein Formular mit POST.\n" if ($method ne 'POST');
my $expected = &ftps_rotation_token();
die "Ungültiges Formular. Bitte die Seite neu laden.\n"
    if (!defined($token) || length($token) != length($expected) ||
        (($token ^ $expected) =~ /[^\0]/));
}

sub ftps_rotation_backend
{
my ($request) = @_;
&ftps_rotation_admin();
my $root = &module_root_directory('virtualmin-ftps');
my ($writer, $reader);
my $errors = gensym();
my $pid = open3($writer, $reader, $errors,
                '/usr/bin/python3', "$root/manage.py", 'logrotate-api');
binmode($writer, ':raw');
print $writer JSON::PP->new->utf8->canonical->encode($request);
close($writer);
my $select = IO::Select->new($reader, $errors);
my $out = '';
while (my @ready = $select->can_read()) {
    foreach my $fh (@ready) {
        my $n = sysread($fh, my $chunk, 8192);
        if ($n) { $out .= $chunk; }
        else { $select->remove($fh); close($fh); }
    }
}
waitpid($pid, 0);
die "Logrotation konnte nicht verarbeitet werden: $out\n" if ($?);
return JSON::PP->new->utf8->decode($out);
}

sub ftps_rotation_policy
{
my ($reply, $scope) = @_;
my $r = $reply->{'rotation'} || {};
my %p = (interval => 'weekly', rotate => 52, maxsize => undef);
foreach my $key (keys %p) { $p{$key} = $r->{$key} if (exists($r->{$key})); }
my $override = ($r->{'domains'} || {})->{$scope};
if ($scope && $override) {
    foreach my $key (keys %p) { $p{$key} = $override->{$key} if (exists($override->{$key})); }
}
return (\%p, $scope && !$override ? 1 : 0);
}

sub ftps_rotation_input
{
my ($input, $scope) = @_;
return undef if ($scope && $input->{'inherit'});
die "Bitte eine gültige Archivanzahl eingeben.\n"
    if (!defined($input->{'rotate'}) || $input->{'rotate'} !~ /^[0-9]{1,4}$/);
return { interval => $input->{'interval'} || '', rotate => 0+$input->{'rotate'},
         maxsize => length($input->{'maxsize'} || '') ? $input->{'maxsize'} : undef };
}
1;
