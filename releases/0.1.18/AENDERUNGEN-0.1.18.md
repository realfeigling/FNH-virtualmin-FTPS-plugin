# 0.1.18 — Beta

- Neue Standardablage: /var/log/virtualmin-ftps-logs/DOMAIN-ID. Alte automatische log_root-Werte werden umgestellt; individuelle andere Pfade bleiben erhalten.
- Originale bleiben root-eigen (Dateien 0640, Domain-Gruppe lesbar). FTP-Ansicht logs/ftps bleibt schreibgeschützt; Logs and Reports bleibt erhalten.
- Pfadwechsel löst die bisherigen eigenen Bind-Mounts und bindet die neue Quelle ein; Vorschau prüft die bisherige Ansicht. Wiederherstellung bei fehlgeschlagenem Anwenden bleibt enthalten.
- /var/log darf root gehören und von root, syslog oder adm gruppenschreibbar sein, sofern alle Gruppenmitglieder Systemkonten mit UID unter 1000 sind. Andere gruppenschreibbare Eltern, Symlinks und Welt-Schreibrechte werden abgewiesen. Keine Änderung der /var/log-Rechte.
- Vorhandene Logs werden bei fehlendem Ziel als begrenzter Schnappschuss übernommen; alte Dateien bleiben erhalten. Kein automatisches Verschieben oder Löschen.

Vor Installation den Plugin-Timer bei Bedarf anhalten, damit die Anwendung kontrolliert erfolgt. Für eine vollständige Übernahme während eines Wartungsfensters bestehende FTP-Sitzungen beenden bzw. Zugriffe unterbrechen. Noch offene Sitzungen können bis zu ihrem Ende in die alten Dateien schreiben; diese deshalb behalten und erst nach Prüfung manuell archivieren. Keine gleichnamigen Zieldateien blind überschreiben.

Nach Installation:

```sh
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
```

Ein zuvor angehaltener virtualmin-ftps.timer muss anschließend wieder gestartet werden. Kein Live-Server wurde beim Paketbau verändert.
