use utf8;

sub ftps_log_reply
{
my ($id, $kind) = @_;
die "Invalid domain ID\n" if (!defined($id) || $id !~ /^\d{1,40}$/);
die "Invalid log selector\n" if (!defined($kind) || $kind !~ /^(ftp|transfer)$/);
&ftps_load_virtualmin();
my $d = &virtual_server::get_domain($id);
die "Domain not available\n" if (!$d || !$d->{'id'} || !$d->{'virtualmin-ftps'});
die "Access denied for domain\n" if (!&virtual_server::can_edit_domain($d));
if (!&virtual_server::master_admin()) {
    my %acl = &get_module_acl(undef, 'virtualmin-ftps');
    my %ids = map { $_ => 1 } split(/\s+/, $acl{'doms'} || '');
    die "Log access denied\n" if (!$acl{'logs'} || !$ids{$id});
}
my $raw = &ftps_engine({ operation => 'read-log', id => "$id", log => $kind }, 0);
my $r = JSON::PP->new->decode($raw);
die "Unexpected log response\n" if (($r->{'scope'}->{'id'} || '') ne $id ||
                                     ($r->{'log'} || '') ne $kind);
return $r;
}

sub ftps_log_html
{
my ($r) = @_;
return '<h2>'.&html_escape($r->{'scope'}->{'domain'} || '').'</h2>'.
       '<p>Nur lesend. Keine Funktion zum Leeren, Bearbeiten oder L&ouml;schen.</p>'.
       ($r->{'truncated'} ? '<p>Anzeige auf die letzten 200 Zeilen / 64 KiB begrenzt.</p>' : '').
       '<pre style="white-space:pre-wrap;overflow-wrap:anywhere">'.
       &html_escape($r->{'text'} || '').'</pre>';
}
1;
