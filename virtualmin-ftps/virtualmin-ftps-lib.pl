BEGIN { push(@INC, '..'); }
use WebminCore;
use JSON::PP;
use IPC::Open3;
use Symbol qw(gensym);
use IO::Select;
use Cwd qw(abs_path);
&init_config();
my $report_file = &module_root_directory('virtualmin-ftps').'/report-lib.pl';
require $report_file;

sub ftps_check_active_root
{
open(my $fh, '<', '/etc/webmin/miniserv.conf') || die "Cannot read active Webmin root\n";
my @roots;
while (my $line = <$fh>) {
    push(@roots, $1) if ($line =~ /^root=(.+?)\s*$/);
}
close($fh);
my $module = &module_root_directory('virtualmin-ftps');
die "FTPS module is not under the active Webmin root; freeze and review after upgrade\n"
    if (@roots != 1 || !abs_path($roots[0]) ||
        abs_path($roots[0]) ne abs_path("$module/.."));
}

sub ftps_load_virtualmin
{
&ftps_check_active_root();
my %info = &get_module_info('virtual-server');
die "FTPS requires the audited Virtualmin GPL 8.3.0; freeze and review after an upgrade\n"
    if (($info{'version'} || '') ne '8.3.0.gpl');
&foreign_require('virtual-server', 'virtual-server-lib.pl');
}

sub ftps_descriptor
{
my ($d) = @_;
&ftps_load_virtualmin();
die "FTPS supports real domains with a home directory and website SSL only\n"
    if ($d->{'alias'} || !$d->{'dir'} || !$d->{'home'} || !&virtual_server::domain_has_ssl($d));
my %r = map { $_ => $d->{$_} // '' } qw(id dom ip ip6 group);
$r{'home'} = $d->{'home'};
$r{'cert'} = &virtual_server::get_website_ssl_file($d, 'cert');
$r{'key'} = &virtual_server::get_website_ssl_file($d, 'key');
$r{'ca'} = &virtual_server::get_website_ssl_file($d, 'ca') || '';
# Virtualmin 8.3 serializes disabled feature names with commas (funcs.pl:9828).
$r{'suspended'} = scalar(grep { $_ eq 'virtualmin-ftps' }
                        split(/,/, $d->{'disabled'} || '')) ? 1 : 0;
return \%r;
}

sub ftps_engine
{
my ($request, $apply) = @_;
&ftps_load_virtualmin();
if ($apply) {
    &foreign_require('proftpd', 'proftpd-lib.pl');
    &proftpd::lock_proftpd_files();
}
my ($out, $err);
eval { $out = &ftps_backend($request, $apply); };
$err = $@;
if ($apply) {
    &proftpd::unlock_proftpd_files();
    undef(@proftpd::get_config_cache);
}
die $err if ($err);
return $out;
}

sub ftps_backend
{
my ($request, $apply) = @_;
my $root = &module_root_directory('virtualmin-ftps');
my @argv = ('/usr/bin/python3', "$root/engine.py");
push(@argv, '--apply') if ($apply);
my ($writer, $reader);
my $errors = gensym();
my $pid = open3($writer, $reader, $errors, @argv);
binmode($writer, ':raw');
print $writer JSON::PP->new->utf8->canonical->encode($request);
close($writer);
# Drain both pipes together to avoid stderr/stdout deadlocks.
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
my $status = $?;
die "FTPS operation failed: $out\n" if ($status);
return $out;
}

sub ftps_apply_domain
{
my ($d, $suspended, $defer) = @_;
my $desc = &ftps_descriptor($d);
$desc->{'suspended'} = $suspended if (defined($suspended));
my $out = &ftps_engine({ operation => 'upsert', domains => [ $desc ],
                       defer_certificate => $defer ? 1 : 0 }, 1);
my $reply = JSON::PP->new->decode($out);
if ($reply->{'pending'} && $reply->{'pending'}->{$d->{'id'}}) {
    my $printer = $virtual_server::second_print;
    &$printer('FTPS wartet auf ein gueltiges Zertifikat; der Timer versucht es erneut')
        if (ref($printer) eq 'CODE');
}
return 1;
}

sub ftps_delete_domain
{
my ($d) = @_;
&ftps_engine({ operation => 'delete', id => "$d->{'id'}" }, 1);
return 1;
}

sub ftps_inspection_page
{
my ($id) = @_;
die "Ungueltige Domain-ID\n" if (!defined($id) || $id !~ /^\d{1,40}$/);
my $d = &virtual_server::get_domain($id);
die "Domain nicht gefunden\n" if (!$d || !$d->{'id'});
my $result = &ftps_engine({ operation => 'inspect', domains => [ &ftps_descriptor($d) ] }, 0);
my $report = JSON::PP->new->decode($result);
die "Unerwartete Domain im Pruefbericht\n"
    if (($report->{'scope'}->{'id'} || '') ne $id);
return &ftps_report_html($report);
}

sub ftps_refresh_menu
{
&ftps_load_virtualmin();
&virtual_server::clear_links_cache();
return "Virtualmin-Menuecache erneuert. Bitte die Browserseite vollstaendig neu laden. Keine ProFTPD-Aenderung.\n";
}

1;
