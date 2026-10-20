#!/usr/bin/perl
use utf8;
require './virtualmin-ftps-lib.pl';
&ReadParse();
my ($result, $error);
eval { $result = &ftps_log_reply($in{'dom'} || '', $in{'log'} || 'ftp'); };
$error = $@;
$main::force_charset = 'UTF-8';
&ui_print_header(undef, 'FTP-Logs (Beta)', '', undef, 1, 1);
my $html = $error ? '<p>'.&html_escape($error).'</p>' : &ftps_log_html($result);
utf8::encode($html) if (utf8::is_utf8($html));
print $html;
&ui_print_footer('/', 'Virtualmin');
