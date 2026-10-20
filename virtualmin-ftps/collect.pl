#!/usr/bin/perl
use strict;
use warnings;
use FindBin;
our ($module_name, $module_root_directory, $module_config_directory, $no_acl_check, %config);
die "Must run as root\n" if ($< != 0);
$main::no_acl_check++;
$ENV{'WEBMIN_CONFIG'} ||= '/etc/webmin';
$ENV{'WEBMIN_VAR'} ||= '/var/webmin';
chdir($FindBin::Bin) || die "chdir: $!";
$0 = "$FindBin::Bin/collect.pl";
unshift(@INC, $FindBin::Bin, "$FindBin::Bin/..");
require './virtualmin-ftps-lib.pl';
&ftps_load_virtualmin();
my ($apply, $one, $candidate, $export, $json, $refresh, $repair, $website) = (0, '', 0, 0, 0, 0, 0, 0);
while (@ARGV) {
    my $a = shift(@ARGV);
    if ($a eq '--apply') { $apply = 1; }
    elsif ($a eq '--domain') { $one = shift(@ARGV) // die "Domain ID missing\n"; }
    elsif ($a eq '--candidate') { $candidate = 1; }
    elsif ($a eq '--export') { $export = 1; }
    elsif ($a eq '--json') { $json = 1; }
    elsif ($a eq '--use-website-certificates') { $website = 1; }
    elsif ($a eq '--repair-login-order') { $repair = 1; }
    elsif ($a eq '--refresh-menu') { $refresh = 1; }
    else { die "Unknown option: $a\n"; }
}
if ($refresh) {
    die "--refresh-menu cannot be combined with domain or backend operations\n"
        if ($apply || $one || $candidate || $export || $json || $repair || $website);
    print &ftps_refresh_menu();
    exit;
}
if ($repair) {
    die "--repair-login-order cannot be combined with domain/export options\n"
        if ($one || $candidate || $export || $json || $website);
    my $raw = &ftps_engine({ operation => 'repair-login-order' }, $apply);
    my $r = JSON::PP->new->decode($raw);
    print $r->{'changed'} ? ($r->{'applied'} ? "Loginregel korrigiert; Syntaxprüfung und Reload erfolgreich.\n" :
          "Korrektur vorbereitet und Syntax geprüft. Zum Anwenden --apply ergänzen.\n") :
          "Loginregel ist bereits korrigiert; keine Änderung.\n";
    exit;
}
die "Candidate requires one domain ID and cannot apply\n"
    if ($candidate && (!$one || $apply));
die "--use-website-certificates cannot be combined with domain/export options\n"
    if ($website && ($one || $candidate || $export));
my @domains;
if ($one) {
    die "Invalid domain ID\n" if ($one !~ /^\d{1,40}$/);
    my $d = &virtual_server::get_domain($one);
    die "Domain not found\n" if (!$d || !$d->{'id'});
    @domains = ($d);
} else {
    @domains = &virtual_server::list_domains();
}
my @descriptors;
foreach my $d (@domains) {
    next if (!$candidate && !$d->{'virtualmin-ftps'});
    push(@descriptors, &ftps_descriptor($d));
}
my $request = { operation => $website ? 'use-website-certificates' : $one && !$apply ? 'inspect' : $one ? 'upsert' : 'reconcile', domains => \@descriptors };
if ($export) {
    die "--export cannot apply\n" if ($apply);
    print JSON::PP->new->utf8->canonical->encode($request), "\n";
} else {
    my $out = &ftps_engine($request, $apply);
    if ($website && !$json) {
        my $r = JSON::PP->new->decode($out);
        if ($r->{'deferred'}) {
            $out = "Eine Domain wurde gerade gespeichert. Bitte nach zwei Minuten erneut ausführen. Noch nichts umgestellt.\n";
        } else {
            $out = $r->{'applied'} ? "Website-Zertifikate direkt eingebunden; Syntaxprüfung und Reload erfolgreich.\n" :
                   $r->{'changed'} ? "Umstellung geprüft. Zum Anwenden --apply ergänzen.\n" :
                   "Website-Zertifikate bereits direkt eingebunden; keine Änderung.\n";
            $out .= "Ausstehende Domains: ".scalar(keys %{$r->{'pending'} || {}})."\n";
        }
    }
    if ($one && !$apply && !$json) {
        $out = &ftps_report_text(JSON::PP->new->decode($out));
        utf8::encode($out) if (utf8::is_utf8($out));
    }
    print $out;
}
