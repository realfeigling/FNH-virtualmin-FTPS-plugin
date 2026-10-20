# Root-Logs mit Löschschutz — 0.1.16 Beta

Auf ausdrücklichen Wunsch gehören aktive FTP-Logs wieder root. Der Schutz erstreckt sich auch auf die Elternverzeichnisse: Aktive Logs werden nach /var/log/virtualmin-ftps/DOMAIN-ID verlegt. Root-Dateien allein im beschreibbaren Kunden-Home würden das Löschen oder Umbenennen nicht zuverlässig verhindern.

Die Domain-Gruppe erhält Leserechte, aber keine Schreibrechte. Vorhandene Home-Logs bleiben unverändert und werden beim erstmaligen Anlegen der geschützten Zieldateien als Schnappschuss kopiert. Details und Grenzen zu alten FTP-Sitzungen, Rücknahme und Rotation stehen in DOMAIN-LOGS.md.

## Installation und Anwendung

0.1.16 Beta über Webmin installieren. Danach zuerst die Vorschau:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
```

Nach erfolgreicher Vorschau anwenden:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply &&
proftpd -t -c /etc/proftpd/proftpd.conf &&
systemctl is-active proftpd
```

Den Modulpfad gegebenenfalls anpassen. Ein aktiver Timer kann nach der Installation automatisch abgleichen. Die bisherige genaue Driftprüfung bleibt erhalten; die bekannten alten Home-Pfade werden aus dem gespeicherten Zustand rekonstruiert. Nach erfolgreicher Anwendung mit einer neuen FTP-Verbindung testen.

AllowOverride on und AllowOverwrite on bleiben aktiv. Das Überschreiben normaler Kundendateien ist weiterhin gemäß den Unix-Rechten möglich. Die geschützten Protokolldateien sind davon durch ihre eigenen Rechte und Verzeichnisse ausgenommen.

Beim Paketbau wurden keine Live-Serverdateien oder Live-Konfigurationen geändert.
