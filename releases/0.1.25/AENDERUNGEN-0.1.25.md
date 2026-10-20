# 0.1.25 — Beta

## Logrotation aus der Domain-Prüfung

Der Link unter „FTPS prüfen“ übernimmt jetzt die ausgewählte Virtualmin-Domain. Die aufgerufene Logrotation zeigt ausschließlich deren Einstellungen, ohne globale Host-Auswahlliste. Eigene Werte und „Gemeinsame Vorgaben übernehmen“ bleiben verfügbar. Der allgemeine Einstieg ohne Domain bietet weiterhin gemeinsame Vorgaben und eine Host-Auswahl.

Ein einziges POST-Formular, Administratorprüfung, Sitzungsschutz, Prüfung vor Anwendung und Erhalt fremder Einstellungen bleiben erhalten. Bestehende Rotationswerte werden nicht geändert.

## Beispiel mit 53 Wochenarchiven

Eine Domain-Regel mit rotate 53 vor der Standardregel mit rotate 52 ist korrekt: Diese Domain erhält bis zu 53 Archive; die übrigen behalten 52. ignoreduplicates verhindert, dass die nachfolgende Wildcard dieselben Dateien erneut verarbeitet. /data/log ist bei /var/log -> /data/log der geprüfte tatsächliche Zielpfad. Literal vorhandene HTML-Entities oder Backslashes vor dem Stern gehören nicht in die Logrotate-Datei; in Chat-Kopien können solche Zeichen Darstellungsartefakte sein. Ein rein lesender Syntaxcheck erfolgt mit logrotate --debug /etc/logrotate.d/virtualmin-ftps.

Nach Modul-Update die gewünschte Domain in Virtualmin auswählen, „FTPS prüfen“ und dort „Logrotation für diese Domain einstellen“ öffnen. Keine Live-Serveränderung beim Paketbau.
