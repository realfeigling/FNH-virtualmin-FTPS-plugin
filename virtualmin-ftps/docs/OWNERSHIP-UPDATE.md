# Log-Eigentümer und Kundenregeln — 0.1.14 Beta

Die root-Eigentümerforderung der Versionen 0.1.10 bis 0.1.13 war mit den gewünschten Domain-Logs unvereinbar. Neue und bestehende Logs verwenden jetzt Domain-Benutzer und Domain-Gruppe. Ein vorhandenes Paar mit UID 1015, GID 1018 und 0644 wird akzeptiert, wenn es zu den von Virtualmin gemeldeten Benutzer-/Gruppennamen gehört. Ein manuelles chown root ist nicht nötig.

Außerdem werden je Host AllowOverride on und AllowOverwrite on gesetzt. AllowOverride aktiviert die Verarbeitung von .ftpaccess-Dateien; AllowOverwrite erlaubt das Überschreiben vorhandener Dateien für Benutzer mit den nötigen Unix-Rechten. Chroot, TLS und die bestehende LOGIN-Gruppenbegrenzung bleiben im erzeugten Host erhalten. .ftpaccess-Dateien können die dort von ProFTPD unterstützten Verzeichnisregeln anpassen.

## Installation und Anwendung

0.1.14 Beta über Webmin installieren. Danach zuerst die Vorschau:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
```

Nach erfolgreicher Vorschau anwenden:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply &&
proftpd -t -c /etc/proftpd/proftpd.conf &&
systemctl is-active proftpd
```

Den Modulpfad an die aktive Webmin-Installation anpassen. Die Migration der bekannten alten Server-Begrüßung bleibt enthalten. Domain-Benutzer werden bei der vollständigen Sammlung im gespeicherten Zustand ergänzt; die alte Konfiguration mit AllowOverride off wird dabei exakt geprüft. Fremde Konfigurationsänderungen bleiben gesperrt.

Anschließend mit einer neuen FTP-Verbindung das Überschreiben einer geeigneten Testdatei prüfen. Konfiguration und Logpfade lassen sich lesen mit:

```bash
grep -nE 'ServerName|AllowOverride|AllowOverwrite|ExtendedLog|TransferLog' /etc/proftpd/virtualmin-ftps.conf
```

Beim Paketbau wurden keine Live-Serverkonfigurationen oder Live-Dateieigentümer geändert. Bei Anwendung können passende root-eigene Altlogs auf den Domain-Benutzer übertragen werden; siehe DOMAIN-LOGS.md für Erhalt und Rücknahmegrenzen.

Quellen: [ProFTPD AllowOverride](https://github.com/proftpd/proftpd/blob/master/doc/modules/mod_core.html) und [AllowOverwrite](https://github.com/proftpd/proftpd/blob/master/doc/modules/mod_xfer.html).
