# Noch ausstehende Praxistests

Diese Schritte sind nicht auf dem laufenden Nutzer-Server ausgeführt worden. Sie sind ein Abnahmeplan, kein erfolgreicher Testnachweis. Zuerst Prüfmodus und Konfliktbericht verwenden. Änderungen an einem Produktivsystem erfordern ein bewusst gewähltes Wartungsfenster und funktionierende Wiederherstellung.

## Stufe 1: ohne aktive Änderungen

1. `manage.py check --webmin-root /opt/webmin-2.670` ausführen. Versionen und fremde VirtualHosts nachvollziehen.
2. Bestehende Konfiguration lokal mit `proftpd -t -c /etc/proftpd/proftpd.conf` prüfen. Parsermeldungen lokal lesen; nicht ungeschwärzt Zugangsdaten veröffentlichen.
3. Falls gewünscht das Plugin inert installieren und global in Virtualmin verfügbar machen, standardmäßig aus. Menü für Hauptadministrator und Domain-Checkbox prüfen. Die Checkbox darf im Prüfmodus keine aktive Änderung vornehmen.
4. `collect.pl --domain DOMAIN_ID --candidate` ausführen. Bei den vorhandenen Alt-VirtualHosts muss ein Konflikt entstehen; keine automatische Übernahme.

## Stufe 2: kontrollierter Live-Test

Nur nach Behebung der dokumentierten Voraussetzungen, mit geeigneter Domain ohne alten FTP-VirtualHost und vorhandener Wiederherstellung:

1. Aktuellen Konfigurations-/Dienstzustand sichern. Abschaltung des Hauptservers mit `Port 0`/`DefaultServer off` und explizite Ports benötigter Alt-Hosts abgestimmt prüfen. Keine pauschale globale TLS-Aktivierung. Dann Plugin aktivieren, Domain-Checkbox einschalten. Eigene Datei, Syntaxprüfung, Dienststatus und Protokoll prüfen.
2. Für zwei Domains derselben IP prüfen, dass jeweils das eigene Zertifikat ausgegeben wird. Beispiel von einem separaten Client:

```bash
openssl s_client -connect SERVER_IP:21 -starttls ftp -servername DOMAINNAME -verify_hostname DOMAINNAME -verify_return_error -showcerts
```

`SERVER_IP` und `DOMAINNAME` ersetzen. Zusätzlich ausdrücklich ohne SNI und mit einem FTP-Client mit HOST-Unterstützung testen. Negative Ergebnisse ohne Namensauswahl sind bei Shared-IP-Hosts zu erwarten und zu dokumentieren. Ein Zertifikatscheck allein prüft weder Anmeldung noch Datenkanal. Erstbegrüßung, Begrüßung nach HOST und Servername nach Namensauswahl getrennt protokollieren; eine falsche Erstbegrüßung vor Namensauswahl wird nicht als durch SNI nachträglich behoben dargestellt.

3. Mit einem freigegebenen Testkonto anmelden, passiven Upload/Download prüfen. Fremdes Domainkonto muss bei aktivierter Gruppenbeschränkung abgewiesen werden. Anonymous-Anmeldung darf über den Plugin-Host nicht freigegeben sein. Host-/Globalregeln auf unerwartete Vererbung prüfen.
4. Domain deaktivieren/aktivieren und Checkbox entfernen/wieder einschalten. Vorhandene Sitzungen gesondert beobachten; ein Reload beendet nicht zwingend bestehende Sessions.
5. Zertifikatserneuerung einschließlich Chain und RSA-/EC-Wechsel mit einem dafür geeigneten Ablauf testen. Nach der Timerverzögerung muss eine neue Verbindung den neuen Fingerprint zeigen. Einen ungültigen Schlüssel nicht absichtlich auf einer produktiven Domain einsetzen; entsprechende Fehler sind lokal simuliert getestet.
6. IP-Wechsel, IPv6 und Domain-Löschung nur an dafür geeigneten Domains testen. Keine IP eines aktiven Produktivhosts für diesen Test entfernen.
7. `manage.py rollback`: Timer bleibt gestoppt, vorheriger Plugin-Zustand wird wiederhergestellt. Dann `manage.py deactivate`: eigener Include entfernt, Alt-VirtualHosts und fremde Änderungen erhalten, Dienst weiterhin aktiv. Domain-Flags separat nachvollziehen.

## Ergebnisprotokoll

Für jeden Schritt Datum, Virtualmin-/Webmin-/ProFTPD-Version, Prüfbefehl, erwartetes und tatsächliches Ergebnis sowie nötige Rücknahme festhalten. Keine privaten Schlüssel oder Passwörter protokollieren. Erst nach dieser Abnahme lässt sich der Aufbau als im Zielsystem laufzeitgeprüft bezeichnen.
