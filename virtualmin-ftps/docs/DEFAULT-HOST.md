# FTPS-Standardhost ab 0.1.5

Der Hauptserver bleibt mit `Port 0` und `DefaultServer off` abgeschaltet. Genau ein ausdrücklich benannter, vom Plugin verwalteter Domain-VirtualHost kann `DefaultServer on` erhalten. Er verwendet sein Domain-Zertifikat, TLS-Pflicht und dieselbe Gruppenbeschränkung wie andere Plugin-Hosts. Es werden weder ein Virtualmin-Webserver noch ein Zertifikat automatisch angelegt.

## Ersteinrichtung auf web4

Das neue Modul über Webmin installieren. Vorhandene engine.json und Zustandsdaten bleiben erhalten. Diese Schritte setzen den bisher bestätigten Prüfmodus ohne verwaltete Hosts voraus.

1. In Virtualmin muss `web4.de.fnh.co` als eigener virtueller Server mit Home-Verzeichnis, Unix-Gruppe und gültigem Website-Zertifikat vorhanden sein. Die FTPS-Checkbox zunächst ausgeschaltet lassen.
2. Root-Konfiguration sichern: `cp -a /etc/proftpd/proftpd.conf /etc/proftpd/proftpd.conf.vor-ftps-standardhost`. Eine vorhandene Sicherung nicht überschreiben.
3. Im Hauptserver vorhandene Einstellungen auf `Port 0` und `DefaultServer off` ändern. Alle bestehenden Alt-VirtualHosts behalten ausdrücklich `Port 21`. Noch keinen separaten Reload ausführen.
4. Nur die spätere Standardhost-Auswahl speichern (kein Reload, keine ProFTPD-Änderung):

```bash
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py set-default-host --domain web4.de.fnh.co
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py check
proftpd -t -c /etc/proftpd/proftpd.conf
```

Die Prüfung muss `default_domain: web4.de.fnh.co`, `issues: []` und eine gültige Syntax melden.

5. Live-Aktivierung (ändert den Include, prüft die Gesamtkonfiguration, führt einen Reload aus und startet den Timer):

```bash
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py activate --webmin-root /opt/webmin-2.670
```

6. In Virtualmin ausschließlich für `web4.de.fnh.co` die Funktion „FTPS VirtualHost“ einschalten und speichern. Anschließend „FTPS prüfen“ öffnen. Ein ausstehendes Zertifikat bedeutet noch keinen aktiven Host.
7. Kontrolle:

```bash
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
cat /etc/proftpd/virtualmin-ftps.conf
```

Nur im Block von `web4.de.fnh.co` darf `DefaultServer on` stehen. Dort müssen `TLSEngine on`, `TLSRequired on` und der passende Servername vorhanden sein.

8. Von einem getrennten Client mit erreichbarer Server-IP prüfen:

```bash
openssl s_client -connect 178.250.232.64:21 -starttls ftp -servername web4.de.fnh.co -verify_hostname web4.de.fnh.co -verify_return_error </dev/null
```

Danach ohne SNI (`-noservername` statt `-servername web4.de.fnh.co`) prüfen und die tatsächliche Zertifikats-/Begrüßungsauswahl dokumentieren. Anmeldung sowie passiven Upload und Download zusätzlich mit einem berechtigten Testkonto testen. Die Prüfseite führt diese Verbindungstests nicht selbst aus.

## Genaue Bedeutung und Grenzen

ProFTPD `DefaultServer on` ist ein Fallback für Verbindungen, für die keine passende IP-VirtualHost-Konfiguration gefunden wird. Es erzwingt nicht, dass jede Verbindung ohne SNI/HOST diesen Host auswählt. Schon passende Alt-VirtualHosts derselben IP können den ersten Kontext bestimmen. Das Plugin schreibt den Standardhost innerhalb seiner eigenen Datei zuerst, verschiebt aber keine fremden Einträge oder Includes. Eine einheitliche Erstbegrüßung über web4 ist bei den vorhandenen Alt-Hosts daher erst nach praktischer Prüfung und gegebenenfalls geplanter Migration/Umordnung zugesichert.

Quelle für ProFTPD 1.3.8: https://github.com/proftpd/proftpd/blob/v1.3.8/doc/modules/mod_core.html (Abschnitt DefaultServer).

Die Standardhost-Auswahl ist ein Domainname, keine zusätzliche Feature-Checkbox. Sie lässt sich mit `set-default-host` nur vor der ersten Aktivierung bei leerem Zustand ändern. Ohne Auswahl bleibt das bisherige Verhalten erhalten. Manuelle Änderungen an engine.json während des Live-Betriebs werden nicht als Migration unterstützt.

Bei Sperrung bleibt der Host Standardhost, verweigert aber Anmeldungen. Bei Entfernen der FTPS-Funktion, Domain-Löschung oder Umbenennung entfällt seine Standardhost-Rolle; kein anderer Host wird automatisch zum Standardhost. Bei fehlendem/ungültigem Erstzertifikat bleibt er ausstehend. Ab 0.1.7 werden Website-Zertifikate direkt referenziert; eine fehlgeschlagene Erneuerungsprüfung löst keinen geplanten Reload aus, schützt aber nicht vor extern ersetzten Dateiinhalten. IP-Wechsel werden über den Domain-Lifecycle verarbeitet. Einen vollständigen Ausfall aller anderen Hosts darf die Standardhost-Auswahl nicht voraussetzen.

## Rücknahme

`manage.py freeze` stoppt den Timer und weitere Plugin-Änderungen; aktive Hosts bleiben bestehen. `manage.py rollback` stellt die vorherige Plugin-Transaktion wieder her und lässt den Timer gestoppt. `manage.py deactivate` entfernt den verwalteten Include nach Syntaxprüfung/Reload; die zuvor manuell gesetzten Hauptserver-Werte werden dadurch nicht zurückgesetzt.

Soll der frühere Hauptserver wieder laufen, seine Werte gezielt auf den gesicherten Stand zurücksetzen, die Gesamtkonfiguration prüfen und erst dann ProFTPD neu laden. Keine gesamte alte Sicherung über zwischenzeitliche fremde Änderungen kopieren. Eine Wiederaufnahme nach Freeze/Rollback ist weiterhin kein automatischer Resume.

## Prüfnachweis

Lokale Tests simulieren ProFTPD und systemd und prüfen echte Testzertifikate mit OpenSSL. Ein realer ProFTPD-1.3.8-Dienst und die Webmin-Theme-Darstellung sind in dieser Umgebung nicht verfügbar. Live-Verbindung, Fallback-Auswahl und Datenkanal auf web4 sind noch nicht abgenommen.
