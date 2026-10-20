use utf8;
# Read-only report presentation. All domain and error values are HTML-escaped.
sub ftps_report_html
{
my ($report) = @_;
my %status = (ok => 'In Ordnung', warning => 'Vor Aktivierung klären',
              error => 'Nicht erfüllt', info => 'Information');
my $domain = $report->{'scope'}->{'domain'} || '';
my $mode = $report->{'mode'} eq 'dry-run' ? 'Prüfmodus' : 'Live-Modus; diese Prüfung ist nur lesend';
my %icons = (ok => '&#10003;', warning => '&#9888;', error => '&#10007;', info => '&#8505;');
my @all = (@{$report->{'checks'} || []}, @{$report->{'requirements'} || []});
my $errors = scalar grep { $_->{'status'} eq 'error' } @all;
my $warnings = scalar grep { $_->{'status'} eq 'warning' } @all;
my $passed = scalar grep { $_->{'status'} eq 'ok' } @all;
my $overall = $errors ? 'error' : $warnings ? 'warning' : 'ok';
my $summary = $errors ? 'Prüfung mit Fehlern' : $warnings ? 'Voraussetzungen noch offen' : 'Alle ausgeführten Prüfungen erfolgreich';
my $html = '<style>
.ftps-report{max-width:1100px;margin:12px auto;font-size:14px;line-height:1.6}
.ftps-report .ftps-banner{padding:16px 20px;border:1px solid #cbd5e1;border-radius:10px;margin:16px 0}
.ftps-report .ftps-ok{color:#166534;background:#f0fdf4;border-color:#86efac}
.ftps-report .ftps-warning{color:#854d0e;background:#fefce8;border-color:#fde047}
.ftps-report .ftps-error{color:#991b1b;background:#fef2f2;border-color:#fca5a5}
.ftps-report .ftps-info{color:#1e40af;background:#eff6ff;border-color:#93c5fd}
.ftps-report .ftps-badge{display:inline-block;padding:3px 10px;border-radius:6px;font-weight:600;white-space:nowrap}
.ftps-report .ftps-meta{display:grid;grid-template-columns:minmax(140px,1fr) 2fr;gap:8px 16px;padding:16px;border:1px solid #cbd5e1;border-radius:10px}
.ftps-report .ftps-meta dt{font-weight:600}.ftps-report .ftps-meta dd{margin:0;overflow-wrap:anywhere}
.ftps-report .ftps-table{width:100%;border-collapse:collapse}.ftps-report .ftps-table th,.ftps-report .ftps-table td{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #cbd5e1}
.ftps-report .ftps-table-wrap{overflow-x:auto}.ftps-report h3{margin-top:26px}.ftps-report .ftps-note{padding:12px 16px;border-left:3px solid #94a3b8}
</style><div class="ftps-report"><h2>FTPS-Prüfung: '.&html_escape($domain).'</h2>'.
           '<p><strong>'.&html_escape($mode).'</strong></p>'.
           '<p>'.&html_escape($report->{'notice'} || '').'</p>';
$html .= '<div class="ftps-banner ftps-'.$overall.'"><strong>'.$icons{$overall}.' '.
         &html_escape($summary).'</strong><br>'.&html_escape("$passed erfolgreich · $warnings offen · $errors fehlerhaft").
         '<br>Informationen sind keine abgeschlossenen Tests. Anmeldung und Dateiübertragung wurden hier nicht getestet.</div>';
my $d = $report->{'domain'} || {};
$html .= '<dl class="ftps-meta"><dt>IPv4-Adresse</dt><dd>'.&html_escape($d->{'ip'} || 'Keine').'</dd>'.
         '<dt>IPv6-Adresse</dt><dd>'.&html_escape($d->{'ip6'} || 'Keine').'</dd>'.
         '<dt>Unix-Gruppe</dt><dd>'.&html_escape($d->{'group'} || '').'</dd>'.
         '<dt>Name des ausgewählten FTPS-Hosts</dt><dd>'.&html_escape($d->{'greeting'} || $domain).'</dd></dl>';
foreach my $section ([ 'Ergebnis für diese Domain', 'checks' ],
                     [ 'Gemeinsame Voraussetzungen (nur gelesen)', 'requirements' ]) {
    $html .= '<h3>'.$section->[0].'</h3><div class="ftps-table-wrap"><table class="ftps-table"><thead><tr>'.
             '<th>Prüfung</th><th>Ergebnis</th><th>Erläuterung</th></tr></thead><tbody>';
    foreach my $check (@{$report->{$section->[1]} || []}) {
        my $state = exists $status{$check->{'status'} || ''} ? $check->{'status'} : 'info';
        my $label = $status{$state};
        $html .= '<tr><td>'.&html_escape($check->{'label'} || '').'</td><td><span class="ftps-badge ftps-'.$state.'">'.$icons{$state}.' '.
                 &html_escape($label).'</span></td><td>'.&html_escape($check->{'detail'} || '');
        if ($check->{'technical'}) {
            $html .= '<details><summary>Technische Fehlerdetails</summary><pre>'.
                     &html_escape($check->{'technical'}).'</pre></details>';
        }
        $html .= '</td></tr>';
    }
    $html .= '</tbody></table></div>';
}
$html .= '<p class="ftps-note">'.&html_escape($report->{'name_selection'} || '').'</p></div>';
return $html;
}
1;

sub ftps_report_text
{
my ($r) = @_;
my %status = (ok => 'In Ordnung', warning => 'Vor Aktivierung klären', error => 'Nicht erfüllt', info => 'Information');
my $text = 'FTPS-Prüfung: '.($r->{'scope'}->{'domain'} || '')."\n".
           ($r->{'notice'} || '')."\n";
foreach my $section ('checks', 'requirements') {
    foreach my $check (@{$r->{$section} || []}) {
        $text .= ($check->{'label'} || '').': '.($status{$check->{'status'}} || 'Information').
                 "\n  ".($check->{'detail'} || '')."\n";
    }
}
return $text.($r->{'name_selection'} || '')."\n";
}
1;
