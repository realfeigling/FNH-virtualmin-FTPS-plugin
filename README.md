# FNH Virtualmin FTPS Plugin — 0.1.17 Beta

[Installationspaket](releases/0.1.17/virtualmin-ftps-0.1.17.wbm.gz) · [SHA-256](releases/0.1.17/virtualmin-ftps-0.1.17.wbm.gz.sha256) · [Änderungen](releases/0.1.17/AENDERUNGEN-0.1.17.md)

Geschützte root-eigene Originale unter /var/lib/virtualmin-ftps-logs/DOMAIN-ID; /var/log bleibt unverändert. Direkte schreibgeschützte FTP-Ansicht unter Domain-Home/logs/ftps sowie FTP-Log und FTP-Transfer-Log unter Logs and Reports. Keine kundenseitige Funktion zum Löschen oder Leeren. AllowOverride on und AllowOverwrite on bleiben für Kundendateien enthalten.

[Installation, Vorschau, Anwendung und Mount-Voraussetzungen](virtualmin-ftps/docs/DOMAIN-LOGS.md) · [Plugin-Dokumentation](virtualmin-ftps/README.md) · [Prüfbericht](virtualmin-ftps/docs/TESTS.md) · [Verlauf](docs/VERLAUF.md) · [Lizenz](virtualmin-ftps/LICENSE)

Nach Installation kann ein aktiver Timer abgleichen. Nach Neustarts stellt derselbe angewendete Abgleich die FTP-Ansichten wieder her; ohne aktiven Timer ist er manuell nötig. Paketbau und CI verändern keine Live-Serverdateien.
