#!/usr/bin/perl
use utf8;
require './virtualmin-ftps-lib.pl';
&ReadParse();
&ftps_rotation_admin();
my $scope = $in{'dom'} || '';
my $action = $in{'save'} ? 'save' : $in{'preview'} ? 'preview' : ''; 
my ($message, $failure, $reply);
eval {
    if ($action) {
        &ftps_rotation_post($ENV{'REQUEST_METHOD'} || '', $in{'token'});
        die "Ungültige Formularaktion.\n" if ($action !~ /^(preview|save)$/);
        my $r = &ftps_rotation_backend({ operation => $action, scope => $scope,
                     policy => &ftps_rotation_input(\%in, $scope),
                     revision => $in{'revision'} || '' });
        $message = $r->{'saved'} ? 'Einstellungen gespeichert und Logrotation eingerichtet.' :
                                   'Einstellungen sind gültig. Es wurde nichts gespeichert.';
    }
    $reply = &ftps_rotation_backend({ operation => 'read' });
    die "FTP-Host nicht gefunden.\n" if ($scope && !$reply->{'domains'}->{$scope});
};
$failure = $@;
$main::force_charset = 'UTF-8';
&ui_print_header(undef, 'FTP-Logrotation (Beta)', '', undef, 1, 1);
my $html = '<div style="max-width:960px"><p>Gemeinsame Vorgaben oder einen einzelnen FTP-Host auswählen.</p>';
if ($failure) {
    $html .= '<p role="alert">'.&html_escape($failure).'</p>';
}
else {
    $html .= '<p role="status">'.&html_escape($message).'</p>' if ($message);
    $html .= &ui_form_start('rotation.cgi', 'get');
    my @choices = (['', 'Gemeinsame Vorgaben für alle FTP-Hosts']);
    foreach my $id (sort { $reply->{'domains'}->{$a}->{'domain'} cmp
                          $reply->{'domains'}->{$b}->{'domain'} } keys %{$reply->{'domains'}}) {
        push(@choices, [$id, $reply->{'domains'}->{$id}->{'domain'}]);
    }
    $html .= &ui_select('dom', $scope, \@choices).
             &ui_submit('Anzeigen').&ui_form_end();
    my ($policy, $inherit) = &ftps_rotation_policy($reply, $scope);
    if ($action && $action eq 'preview') {
        $inherit = $scope && $in{'inherit'} ? 1 : 0;
        $policy = &ftps_rotation_input(\%in, $scope) if (!$inherit);
    }
    my $title = $scope ? 'Zeitplan für '.$reply->{'domains'}->{$scope}->{'domain'} : 'Gemeinsamer Zeitplan';
    $html .= '<h2>'.&html_escape($title).'</h2>';
    $html .= '<p>Die Rotation ist noch nicht eingerichtet. Mit „Speichern und anwenden“ wird sie aktiviert.</p>'
        if (!$reply->{'installed'});
    $html .= &ui_form_start('rotation.cgi', 'post').
             &ui_hidden('dom', $scope).&ui_hidden('token', &ftps_rotation_token()).
             &ui_hidden('revision', $reply->{'revision'}).
             &ui_table_start('Aufbewahrung der FTP-Logs', undef, 2);
    if ($scope) {
        $html .= &ui_table_row('Gemeinsame Vorgaben',
                    &ui_checkbox('inherit', 1, 'Für diesen FTP-Host übernehmen', $inherit));
    }
    $html .= &ui_table_row('Rotation', &ui_select('interval', $policy->{'interval'},
               [['daily', 'Täglich'], ['weekly', 'Wöchentlich'], ['monthly', 'Monatlich']])).
             &ui_table_row('Archive je Logdatei', &ui_textbox('rotate', $policy->{'rotate'}, 8)).
             &ui_table_row('Zusätzliche Größenrotation',
               &ui_textbox('maxsize', $policy->{'maxsize'} || '', 12).
               ' <span>Leer lassen für keine Größengrenze; z. B. 100M oder 1G.</span>').
             &ui_table_end().
             '<p>Wöchentlich mit 52 Archiven entspricht ungefähr einem Jahr. Zusätzliche Größenrotationen verkürzen diesen Zeitraum. Bei aktivierter Übernahme werden eigene Eingaben ignoriert.</p>'.
             &ui_form_end([['preview', 'Nur prüfen'],
                            ['save', 'Speichern und anwenden']]).
             '<p>Root-Eigentum und lesbarer Kundenzugriff bleiben erhalten. Kein FTP-Neustart nötig. Beim Kopieren und Kürzen können einzelne gleichzeitig geschriebene Zeilen verloren gehen.</p>';
}
$html .= '</div>';
utf8::encode($html) if (utf8::is_utf8($html));
print $html;
&ui_print_footer('/', 'Webmin');
