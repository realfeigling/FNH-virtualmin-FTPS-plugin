# Migration einer bereits geänderten Server-Begrüßung — 0.1.12 Beta

Befund: Der gespeicherte Zustand enthält noch keinen server_fqdn, die verwaltete Datei verwendet aber bereits in allen Hosts den Server-FQDN. Frühere Paketversionen vergleichen in diesem Fall mit den früheren Domain-Begrüßungen und melden Managed configuration drift.

Die ausdrückliche Migration über collect.pl --use-website-certificates akzeptiert ab 0.1.12 zusätzlich genau die aus dem alten Zustand erzeugte Datei mit dem aktuell lokal ermittelten und validierten Server-FQDN als ServerIdent. Die bekannte alte und korrigierte LOGIN-Reihenfolge werden berücksichtigt. Passive Ports, TLS, Zertifikatspfade, Gruppen, Hostnamen, weitere Direktiven, Kommentare und sonstiger Dateiinhalt müssen bytegenau dem erwarteten Renderer entsprechen. Ein beliebiger anderer Begrüßungsname wird nicht akzeptiert. Ein bereits gespeicherter Server-FQDN wird durch diese Ausnahme nicht übergangen.

## Vorgehen

1. Modul 0.1.12 Beta über Webmin installieren.
2. Vorschau ausführen, Modulpfad gegebenenfalls an die aktive Webmin-Installation anpassen:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
```

3. Wenn die Vorschau erfolgreich ist, anwenden:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
```

Die Migration trägt Server-FQDN und AllowOverwrite in den neuen Zustand ein und ergänzt die Domain-Logs aus den tatsächlichen Home-Verzeichnissen. Vorhandene Logeinträge bleiben erhalten. Vorschau verändert weder Konfiguration noch Zustand und legt keine Logdateien an. Anwendung prüft Syntax und führt den bestehenden transaktionalen Reload aus; Rücknahme bleibt verfügbar.

Eine neue Fehlermeldung zu einem Logpfad oder Dateirechten ist getrennt von dieser exakt abgegrenzten Zustandsabweichung zu behandeln. Beim Paketbau wurden keine Live-Serveränderungen vorgenommen.
