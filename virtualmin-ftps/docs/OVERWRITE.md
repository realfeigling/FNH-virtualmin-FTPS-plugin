# Überschreiben vorhandener Dateien — 0.1.11 Beta

Die Meldung `550 index.html: Overwrite permission denied` entsteht bei ProFTPD, wenn für eine bereits vorhandene Zieldatei das Überschreiben nicht erlaubt ist.

Ab 0.1.11 erzeugt das Plugin in jedem verwalteten VirtualHost:

```apache
AllowOverwrite on
```

Die Regel erlaubt einem bereits berechtigten FTP-Benutzer das Überschreiben vorhandener Dateien. Sie ändert weder Dateibesitzer noch Dateirechte, Gruppenrechte, Chroot, TLS-Pflicht oder die Zugangsbeschränkung des Hosts. Spezifischere Directory-Regeln können weiterhin eingreifen. Bleibt nach der Umstellung ein anderer Zugriffsfehler bestehen, müssen Eigentümer und Schreibrechte der konkreten Datei unter dem angemeldeten Unix-Benutzer geprüft werden.

## Update bestehender Hosts

Version 0.1.11 Beta über Webmin installieren. Ein bereits aktiver vollständiger Timer-Abgleich kann die neue Regel automatisch übernehmen. Die Vorschau lässt sich mit dem vorhandenen vollständigen Abgleich ausführen:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
```

Den Modulpfad an die aktive Webmin-Installation anpassen. Erst mit `--apply` wird die Konfiguration nach Syntaxprüfung übernommen und ProFTPD neu geladen. Die genaue bekannte Vorgängerkonfiguration ohne AllowOverwrite wird akzeptiert; fremde Änderungen bleiben gesperrt. Domain-Logs und ihre bisherigen Einträge bleiben erhalten.

Nach erfolgreicher Anwendung mit einer neuen FTP-Verbindung das Überschreiben einer geeigneten Testdatei prüfen. Der Paketbau und die automatisierten Tests haben keine Live-Serverdatei überschrieben und keinen Live-Dienst neu geladen.

Referenz: [ProFTPD mod_xfer / AllowOverwrite](https://github.com/proftpd/proftpd/blob/master/doc/modules/mod_xfer.html).
