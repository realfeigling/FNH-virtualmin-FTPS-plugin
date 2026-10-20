# Login-Korrektur 0.1.6

Die Plugin-Versionen bis einschließlich 0.1.5 erzeugten `Order deny,allow` zusammen mit `DenyAll` und `AllowGroup`. Unter ProFTPD verweigert diese Reihenfolge die Anmeldung vor der Gruppenfreigabe. Das war ein Fehler im Plugin. Ab 0.1.6 wird `Order allow,deny` verwendet: Gruppenmitglieder werden zugelassen, übrige Anmeldungen durch DenyAll abgewiesen. Für gesperrte Domains bleibt nur DenyAll bestehen.

Offizielle ProFTPD-1.3.8-Dokumentation, Abschnitt Order:
https://github.com/proftpd/proftpd/blob/v1.3.8/doc/modules/mod_core.html

## Update bei vorhandenen Live-Hosts

1. Modul 0.1.6 über Webmin installieren. Vorhandene Konfiguration und Zertifikate bleiben erhalten.
2. Reparatur zunächst ohne aktive Änderung prüfen:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --repair-login-order
```

3. Nach erfolgreicher Vorschau anwenden:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --repair-login-order --apply
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
```

Die Reparatur akzeptiert ausschließlich die exakt aus dem gespeicherten Plugin-Zustand erzeugte alte oder bereits korrigierte Konfiguration. Fremde manuelle Änderungen führen zum Abbruch. Die Auswahl des Standardhosts, Gruppen, Zertifikate, IP-Adressen und Domainzustände bleiben unverändert. Für die vollständige verwaltete Datei erfolgt eine Syntaxprüfung vor dem Schreiben; danach ein Reload. Native ProFTPD-Sperren und Plugin-Sperre schützen den Vorgang. Bei Reload-Fehler wird die vorherige Datei wiederhergestellt; schlägt auch die Wiederherstellung fehl, bleibt das Transaktionsjournal für die Fehlerbehebung erhalten. Wiederholte Reparatur bei bereits korrigierter Datei ist ohne Änderung möglich.

Alle Plugin-Hosts werden gemeinsam korrigiert. Bestehende fremde VirtualHosts werden nicht geändert. Bis zur Reparatur können Timer-/Lifecycle-Aufrufe die alte Datei als Abweichung ablehnen; sie wird nicht automatisch überschrieben. Nicht mit `freeze` beginnen: die explizite Reparatur benötigt den bereits aktiven Live-Modus.

4. Eine neue Client-Verbindung mit `web4test.beck-mann.de`, explizitem FTP über TLS und dem berechtigten Benutzer herstellen. Nach der Anmeldung Verzeichnisanzeige und Dateiübertragung testen. Erfolg ist erst anhand dieses Live-Tests nachgewiesen. Bleibt `530` bestehen, neue Logzeilen und das vom Client angezeigte Zertifikat prüfen; SNI-/HOST-Auswahl und weitere geerbte Regeln können zusätzliche Ursachen sein.

## Rücknahme

`python3 /opt/webmin-2.670/virtualmin-ftps/manage.py rollback` stoppt den Timer, setzt den Prüfmodus und stellt die vorherige Transaktion wieder her. Direkt nach der Reparatur ist das die alte Loginregel, die Anmeldungen wieder verweigert. Eine Wiederaufnahme nach Rollback bleibt ein eigener Wartungsschritt. Die Moduldateien zurückzustufen ersetzt keine Transaktionsrücknahme.

## Grenzen des Testnachweises

ProFTPD-/systemd-Aufrufe sind lokal simuliert. Die Regelreihenfolge wurde an der offiziellen 1.3.8-Dokumentation überprüft; ein echter Dienst und ein erfolgreicher Benutzerlogin wurden lokal nicht getestet. Zertifikatsprüfungen verwenden weiterhin echte OpenSSL-Testzertifikate.
