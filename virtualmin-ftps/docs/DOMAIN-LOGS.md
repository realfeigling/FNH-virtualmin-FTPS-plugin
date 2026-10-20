# Domainbezogene FTP-Logs — 0.1.10 Beta

Jeder vom Plugin verwaltete VirtualHost erhält die Logpfade aus dem von Virtualmin gelieferten Domain-Home-Verzeichnis (`dir`), nicht aus einem fest codierten Benutzerpfad.

Beispiel für das Home-Verzeichnis /data/www/pages/u607101601:

```apache
ExtendedLog /data/www/pages/u607101601/logs/ftp.log ALL
TransferLog /data/www/pages/u607101601/logs/xferlog
```

ExtendedLog protokolliert alle ProFTPD-Befehlsklassen im Standardformat; TransferLog schreibt das Transferprotokoll. Jeder Host verwendet sein eigenes Home-Verzeichnis. Zwei aktivierte Domains mit identischem Home und damit identischen Logpfaden werden bei Anwendung abgewiesen.

## Anlage und Erhalt

Beim angewendeten Abgleich werden ein fehlendes logs-Verzeichnis und fehlende Logdateien angelegt. Neue Verzeichnisse erhalten root:Domain-Gruppe und 0750, neue Dateien root:Domain-Gruppe und 0640. Die Dateien werden niemals geleert. Bestehende Besitzer und Rechte werden nicht automatisch geändert: unsichere bestehende Logdateien werden abgewiesen und müssen administrativ geprüft werden.

Symlinks in Home-/Logpfaden, nicht reguläre Logdateien, Mehrfach-Hardlinks, weltweit beschreibbare Verzeichnisse und bestehende Logdateien mit Schreibrechten für Gruppe/Andere werden abgewiesen. Dateiöffnungen erfolgen relativ zu Verzeichnisdeskriptoren und ohne Symlink-Verfolgung.

Die Domain-Home-Verzeichnisse müssen bereits existieren. Die bestehenden ProFTPD-Schutzregeln für Logpfade müssen aktiv bleiben. Ein Besitzer eines übergeordneten Domainverzeichnisses kann dessen Pfad weiterhin umbenennen; die gesamte Verzeichnisstruktur wird hier nicht auf root-Eigentum umgestellt.

Logs bleiben bei Deaktivierung, Domain-Entfernung und Rollback erhalten. Auch nach fehlgeschlagener Syntaxprüfung oder fehlgeschlagenem Reload können bereits neu angelegte leere Logdateien zurückbleiben. Bestehende Konfiguration und Zustand werden bei Reload-Fehler weiterhin zurückgesetzt. Die Aufbewahrung und Rotation der Logdateien wird mit dieser Version nicht eingerichtet.

## Bestehende Hosts umstellen

Nach Installation von 0.1.10 Beta führt der reguläre vollständige Timer-Abgleich die Home-Verzeichnisse für bestehende Hosts nach. Für eine ausdrückliche Vorschau den bereits vorhandenen vollständigen Abgleich verwenden:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
```

Den Pfad an die tatsächliche aktive Webmin-Installation anpassen. Erst der Aufruf mit `--apply` erzeugt die Dateien und übernimmt die Konfiguration einschließlich Syntaxprüfung und Reload. Eine Vorschau erstellt keine Logdateien. Exakt bekannte alte Plugin-Dateien werden akzeptiert, fremde Konfigurationsänderungen weiterhin abgewiesen.

Ein bereits aktiver Timer kann die Änderung nach dem Modulupdate automatisch anwenden. Beim Paketbau wurden keine Live-Serverdateien angelegt und kein Live-Dienst neu geladen.
