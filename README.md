# FNH Virtualmin FTPS Plugin — Beta

Version **0.1.13 Beta** für Virtualmin/Webmin und ProFTPD.

## Download

- [Installierbares Webmin-Paket](releases/0.1.13/virtualmin-ftps-0.1.13.wbm.gz)
- [SHA-256-Prüfsumme](releases/0.1.13/virtualmin-ftps-0.1.13.wbm.gz.sha256)
- [Änderungsübersicht](releases/0.1.13/AENDERUNGEN-0.1.13.md)

Das .wbm.gz-Paket über Webmin installieren. Ein bereits aktiver Abgleich-Timer kann nach Installation die neue ServerIdent-Begrüßung übernehmen. Keine erneute Einrichtung oder Aktivierung ohne Prüfung der bestehenden Installation.

## Domainbezogene Logs

Jeder Host erhält ExtendedLog und TransferLog unter seinem Domain-Home. Fehlende Dateien werden beim Anwenden angelegt, vorhandene Einträge bleiben erhalten. [Details](virtualmin-ftps/docs/DOMAIN-LOGS.md).

## Überschreiben vorhandener Dateien

AllowOverwrite on ist für jeden verwalteten Host gesetzt. Die bisherigen Unix-Dateirechte bleiben maßgeblich. [Details](virtualmin-ftps/docs/OVERWRITE.md).

## Migration einer bereits geänderten Begrüßung

Die ausdrückliche Migration akzeptiert eine exakt bekannte Datei mit lokalem Server-FQDN auch dann, wenn dieser im alten Zustand noch fehlt. [Anleitung](virtualmin-ftps/docs/GREETING-MIGRATION.md).

## Korrektur der Home-Pfade

Der tatsächliche Home-Pfad kommt aus Virtualmins home-Feld. Das dir-Feld ist ausschließlich ein Aktivierungsmerkmal. [Updatehinweise](virtualmin-ftps/docs/HOME-MAPPING.md).

## Dokumentation

- [Arbeitsverlauf und Quellenlage](docs/VERLAUF.md)
- [Installations- und Plugin-Dokumentation](virtualmin-ftps/README.md)
- [Server-FQDN und Migration](virtualmin-ftps/docs/SERVER-IDENT.md)
- [Prüfbericht und Grenzen](virtualmin-ftps/docs/TESTS.md)
- [Versionsverlauf](virtualmin-ftps/docs/CHANGES.md)

Beta: lokale Prüfungen bestanden; eine vollständige Live-Abnahme von Webmin/ProFTPD und FTPS steht aus. Beim Paketbau wurde keine Live-Serverkonfiguration geändert.

Lizenz: siehe [LICENSE](virtualmin-ftps/LICENSE).
