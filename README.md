# FNH Virtualmin FTPS Plugin — 0.1.16 Beta

FTPS-VirtualHosts für Virtualmin/Webmin und ProFTPD mit Website-Zertifikaten, validiertem Server-FQDN, AllowOverride on und AllowOverwrite on.

## Download

- [Installationspaket](releases/0.1.16/virtualmin-ftps-0.1.16.wbm.gz)
- [SHA-256](releases/0.1.16/virtualmin-ftps-0.1.16.wbm.gz.sha256)
- [Änderungen](releases/0.1.16/AENDERUNGEN-0.1.16.md)

## Root-Logs mit Löschschutz

Aktive Logs liegen unter `/var/log/virtualmin-ftps/DOMAIN-ID/`. Dateien und Verzeichnisse gehören root; die jeweilige Domain-Gruppe hat Leserechte. Kunden können die aktiven Logs weder löschen, umbenennen noch überschreiben. Alle Vorfahren des Zielbereichs müssen root kontrollieren und dürfen für Gruppe/Andere nicht beschreibbar sein.

Die bisherigen Home-Logs werden beim ersten Anlegen der geschützten Zieldateien als Schnappschuss übernommen. Quellen bleiben unverändert. Alte FTP-Sitzungen können noch in alte geöffnete Dateien schreiben; neue Verbindungen nutzen nach erfolgreicher Umstellung die geschützten Logs. [Migration, Rücknahme und Rotation](virtualmin-ftps/docs/DOMAIN-LOGS.md).

## Installation und Prüfung

Das .wbm.gz über Webmin installieren. Ein bereits aktiver Timer kann danach automatisch abgleichen. [Vorschau und Anwendung](virtualmin-ftps/docs/OWNERSHIP-UPDATE.md). Der Paketbau verändert keine Live-Serverdateien.

- [Plugin-Dokumentation](virtualmin-ftps/README.md)
- [Arbeitsverlauf](docs/VERLAUF.md)
- [Prüfbericht](virtualmin-ftps/docs/TESTS.md)
- [Versionsverlauf](virtualmin-ftps/docs/CHANGES.md)

Beta: automatisierte Datei-/Migrationsprüfungen ersetzen keinen echten Webmin-/ProFTPD-/FTPS-Livetest. Lizenz: [LICENSE](virtualmin-ftps/LICENSE).
