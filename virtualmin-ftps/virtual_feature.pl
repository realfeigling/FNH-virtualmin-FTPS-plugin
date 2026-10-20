use utf8;
require 'virtualmin-ftps-lib.pl';

sub feature_name { return 'FTPS VirtualHosts'; }
sub feature_label { return 'FTPS VirtualHost'; }
sub feature_losing { return 'Den vom FTPS-Plugin verwalteten VirtualHost entfernen'; }
sub feature_disname { return 'FTPS-Anmeldungen für diese Domain sperren'; }
sub feature_check
{
return 'Python 3 oder OpenSSL fehlt' if (!-x '/usr/bin/python3' || !-x '/usr/bin/openssl');
return 'FTPS-Prüfmodus muss zuerst mit manage.py setup (Upload) oder install (Gesamtpaket) eingerichtet werden'
    if (!-r '/etc/webmin/virtualmin-ftps/engine.json');
return undef;
}
sub feature_depends
{
my ($d) = @_;
&ftps_load_virtualmin();
return 'FTPS benoetigt ein Home-Verzeichnis, eine Unix-Gruppe und Website-SSL'
    if (!$d->{'dir'} || !$d->{'group'} || !&virtual_server::domain_has_ssl($d));
return 'Domain-Aliase werden nicht als eigenstaendige FTPS-Hosts unterstuetzt'
    if ($d->{'alias'});
return undef;
}
sub feature_suitable
{
my ($parent, $alias, $subdomain) = @_;
return $alias ? 0 : 1;
}
sub feature_setup { return &ftps_apply_domain($_[0], undef, 1); }
sub feature_modify { return &ftps_apply_domain($_[0]); }
sub feature_delete { return &ftps_delete_domain($_[0]); }
sub feature_disable { return &ftps_apply_domain($_[0], 1); }
sub feature_enable { return &ftps_apply_domain($_[0], 0); }
sub feature_reset { return &ftps_apply_domain($_[0]); }
sub feature_validate
{
my ($d) = @_;
my $ok = eval {
    my $raw = &ftps_engine({ operation => 'inspect', domains => [ &ftps_descriptor($d) ] }, 0);
    my $report = JSON::PP->new->decode($raw);
    my @errors = map { $_->{'detail'} } grep { $_->{'status'} eq 'error' } @{$report->{'checks'} || []};
    die join('; ', @errors) if (@errors);
    1;
};
return $ok ? undef : "$@";
}
sub feature_links
{
my ($d) = @_;
return ({ mod => 'virtualmin-ftps', cat => 'server',
          desc => 'FTPS prüfen', page => 'index.cgi?dom='.$d->{'id'} });
}
sub feature_always_links
{
my ($d) = @_;
return $d->{'virtualmin-ftps'} ? () : &feature_links($d);
}
1;
