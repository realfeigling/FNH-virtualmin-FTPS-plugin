# Website-Zertifikate direkt verwenden – 0.1.7

Das Plugin verwendet die von Virtualmins `get_website_ssl_file` gemeldeten vorhandenen Website-Dateien direkt in `TLSRSACertificateFile`/`TLSECCertificateFile`, der jeweiligen Schlüsseldirektive und `TLSCertificateChainFile`. Es beantragt oder erzeugt keine Zertifikate und legt keine Zertifikats-/Schlüsselkopien an, auch keine temporären PEM-Dateien für die Prüfung. Der Zertifikatsinhalt wird für die Prüfung in Arbeitsspeicher gelesen. Website-Dateien, Rechte und Symlinks werden nicht verändert.

Beispiel (die tatsächlichen Pfade kommen aus Virtualmin):

```apache
TLSRSACertificateFile /etc/ssl/virtualmin/DOMAIN-ID/ssl.cert
TLSRSACertificateKeyFile /etc/ssl/virtualmin/DOMAIN-ID/ssl.key
TLSCertificateChainFile /etc/ssl/virtualmin/DOMAIN-ID/ssl.ca
```

`TLSCertificateChainFile` dient der Server-Zertifikatskette. Das Plugin setzt dadurch keine zusätzliche Liste vertrauenswürdiger Client-Zertifizierer. Enthält die Website-Zertifikatsdatei die Chain bereits und gibt es keine separate CA-Datei, bleibt der vorhandene Website-Zertifikatspfad erhalten.

## Bestehende Live-Installation umstellen

1. Modul 0.1.7 über Webmin installieren. Kein erneutes setup/install/activate, kein manuelles Ändern der verwalteten Datei. Der aktive Timer kann gültige Domains beim nächsten regulären Abgleich bereits auf direkte Pfade umstellen.
2. Vor der expliziten Vollsynchronisierung alle Virtualmin-Speichervorgänge abschließen. Bei einem sehr kürzlich ausgeführten Lifecycle-Vorgang wartet der Abgleich zunächst die bestehende Schutzfrist ab; nach zwei Minuten erneut ausführen.
3. Vorschau:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
```

4. Nach erfolgreicher Vorschau anwenden:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
cat /etc/proftpd/virtualmin-ftps.conf
```

Der Aufruf gleicht alle ausdrücklich für das Plugin aktivierten Domains mit Virtualmin ab. Er akzeptiert die exakt bekannte bisherige Plugin-Datei mit alter oder korrigierter Login-Reihenfolge. Eine fremde Dateiabänderung wird abgewiesen. Die Umstellung enthält die Login-Korrektur aus 0.1.6 (`Order allow,deny`); der gesonderte Login-Reparaturaufruf ist dafür nicht nötig.

Nach erfolgreichem Abgleich stehen die Website-Pfade anstelle von `/var/lib/virtualmin-ftps/certs/...` in allen aktiven Plugin-Hosts. Standardhost-Auswahl und Domain-Gruppen bleiben erhalten. Zertifikatsfehler bei aktiven Hosts brechen den Vorgang ab. Neue Hosts ohne gültiges Erstzertifikat können weiterhin ausstehend bleiben. Die vollständige ProFTPD-Konfiguration wird vor dem Schreiben geprüft und nach erfolgreicher Umstellung neu geladen. Bei Reload-Fehler wird die vorherige Konfiguration wiederhergestellt.

Bereits vorhandene Kopien aus älteren Versionen werden weder erneut kopiert noch automatisch gelöscht. Sie bleiben zunächst für die Rücknahme der vorherigen Konfiguration erhalten. Nach der Umstellung werden sie vom neuen Domainzustand nicht mehr verwendet. Diese alten Dateien erst nach abgeschlossener Abnahme und entsprechend der Backup-Aufbewahrung bereinigen.

## Erneuerung und Rücknahme

Der Timer prüft weiterhin Zertifikat/Schlüssel, Hostname, Gültigkeit und Vertrauenskette. Inhaltshashes erkennen erneuerte Dateien auch bei unveränderten Pfaden. Bei gültiger Änderung erfolgt Syntaxprüfung und Reload; RSA-/EC-Wechsel ändern die passende Direktive. Während der Prüfung wird ein Dateiaustausch erkannt und der Lauf abgebrochen.

Die direkte Einbindung bedeutet: Website-Verantwortliche und externe Prozesse können die referenzierten Dateien nach der Prüfung verändern. Eine atomare Transaktion über mehrere Zertifikatsdateien und den ProFTPD-Reload ist damit nicht garantiert. Das Plugin kann nach externem Überschreiben keine vorherigen Zertifikatsinhalte wiederherstellen. Auch ein anderer Reload/Neustart kann veränderte Website-Dateien laden. Fehlerhafte Erneuerungen müssen an der Website-Zertifikatsverwaltung behoben werden.

`manage.py rollback` stoppt den Timer, schaltet in den Prüfmodus und stellt die vorherige Plugin-Konfiguration samt Zustand wieder her. Bei der ersten Migration können das noch die alten Snapshot-Verweise sein. Bei späteren Transaktionen sind es nur die früheren Website-Pfade und Inhaltsfingerprints; die Website-Dateien selbst werden nicht zurückgesetzt. Der Resume nach Rollback bleibt ein eigener Wartungsschritt.

Delete/Disable/Enable/IP-Change funktionieren weiter über die Domain-Hooks. Eine neue Domain und ein neues Website-Zertifikat werden durch diesen Umstellungsaufruf nicht angelegt. Pfade müssen absolute, unterstützte ASCII-Dateipfade sein; Leerzeichen und Konfigurations-Steuerzeichen werden abgewiesen.

## Prüfung

Lokale Tests verwenden echte OpenSSL-Testzertifikate und simulieren ProFTPD/systemd. Nach der Umstellung neue FTPS-Verbindung aufbauen und Zertifikatsauswahl, Login sowie passiven Upload/Download praktisch prüfen. Die reine Konfigurationsprüfung ersetzt diesen Live-Test nicht.
