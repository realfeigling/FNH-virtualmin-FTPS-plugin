#!/usr/bin/perl
require './virtualmin-ftps-lib.pl';
&ReadParse();
&ftps_load_virtualmin();
# Webmin module ACL alone is insufficient. Consult Virtualmin's own ACL directly.
my %va = &get_module_acl(undef, 'virtual-server');
&error('Nur Virtualmin-Hauptadministratoren dürfen diesen Prüfbericht lesen')
    if ($va{'noconfig'} || !&foreign_available('virtual-server'));
&ui_print_header(undef, 'FTPS prüfen (Beta)', '', undef, 1, 1);
if (!-r '/etc/webmin/virtualmin-ftps/engine.json') {
    my $root = &module_root_directory('virtualmin-ftps');
    print '<p>Das Modul ist installiert. Den Prüfmodus einmalig als root einrichten; dabei erfolgen keine ProFTPD-Änderungen oder Reloads:</p><pre>'.
          &html_escape("python3 $root/manage.py setup").'</pre>';
    &ui_print_footer('/', 'Webmin');
    exit;
}
my $id = $in{'dom'} || '';
if ($id eq '') {
    print '<p>Bitte zuerst in Virtualmin die gewünschte Domain auswählen und dort unter '.
          '&bdquo;Virtuellen Server verwalten&ldquo; den Eintrag &bdquo;FTPS prüfen&ldquo; öffnen. '.
          'Es wird ausschließlich diese ausgewählte Domain geprüft.</p>';
    &ui_print_footer('/', 'Webmin');
    exit;
}
my $result;
eval {
    $result = &ftps_inspection_page($id);
};
if ($@) {
    $result = '<h2>Prüfung konnte nicht abgeschlossen werden</h2>'.
              '<p>Es wurde nichts geändert. Die ausgewählte Domain und ihre Voraussetzungen prüfen.</p>'.
              '<details><summary>Technische Fehlerdetails</summary><pre>'.&html_escape($@).'</pre></details>';
}
utf8::encode($result) if (utf8::is_utf8($result));
print $result;
&ui_print_footer('/', 'Webmin');
