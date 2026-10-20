# 0.1.23 — Beta

Behebt die Meldung „Speichern erfordert ein Formular mit POST“ bei der Webmin-Logrotation, wenn die CGI-Umgebung beim Laden weiterer Module bereinigt wird. Die ursprüngliche HTTP-Methode wird vor der Initialisierung gesichert und sowohl beim Einlesen als auch bei der Formularprüfung verwendet.

Gültige POST-Anfragen funktionieren auch nach einer Umgebungsbereinigung. GET-Schreibzugriffe, fehlende oder falsche Sitzungstoken und fehlende Administratorrechte bleiben abgewiesen. Nach einem Formularfehler wird die Einstellungsmaske mit den gespeicherten Werten erneut angeboten, sofern die Leseabfrage gelingt.

Nach dem Modul-Update FTP-Logrotation frisch öffnen und „Nur prüfen“ beziehungsweise „Speichern und anwenden“ verwenden. Kein manueller Eingriff in engine.json nötig. Bestehende Konfiguration, Archive und Schutzrechte bleiben erhalten. Keine Live-Serveränderung beim Paketbau.

Neue Regressionstests führen die tatsächliche CGI-Datei aus, löschen während der Administratorprüfung REQUEST_METHOD aus der Umgebung und prüfen erfolgreichen POST, Vorschau ohne Speichern sowie fortbestehende GET-/Token-Abweisung. Die vorherigen Prüfungen laufen weiter.
