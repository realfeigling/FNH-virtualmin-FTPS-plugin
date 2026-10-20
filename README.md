# FNH Virtualmin FTPS Plugin — 0.1.21 Beta

[Installationspaket](releases/0.1.21/virtualmin-ftps-0.1.21.wbm.gz) · [SHA-256](releases/0.1.21/virtualmin-ftps-0.1.21.wbm.gz.sha256) · [Änderungen](releases/0.1.21/AENDERUNGEN-0.1.21.md)

Geschützte root-eigene Originale unter /var/log/virtualmin-ftps-logs/DOMAIN-ID; die Rechte von /var/log bleiben unverändert. Direkte schreibgeschützte FTP-Ansicht unter Domain-Home/logs/ftps sowie FTP-Log und FTP-Transfer-Log unter Logs and Reports. Keine kundenseitige Funktion zum Löschen oder Leeren. AllowOverride on und AllowOverwrite on bleiben für Kundendateien enthalten.

[Installation, Vorschau, Anwendung und Mount-Voraussetzungen](virtualmin-ftps/docs/DOMAIN-LOGS.md) · [Plugin-Dokumentation](virtualmin-ftps/README.md) · [Prüfbericht](virtualmin-ftps/docs/TESTS.md) · [Verlauf](docs/VERLAUF.md) · [Lizenz](virtualmin-ftps/LICENSE)

Nach Installation kann ein aktiver Timer abgleichen. Nach Neustarts stellt derselbe angewendete Abgleich die FTP-Ansichten wieder her; ohne aktiven Timer ist er manuell nötig. Paketbau und CI verändern keine Live-Serverdateien.

Ein root-eigener Verweis /var/log -> /data/log wird unterstützt, sofern Ziel und Ziel-Eltern root-eigen und nicht gruppen- oder weltschreibbar sind. Der konfigurierte Pfad bleibt /var/log/virtualmin-ftps-logs; die physische Ablage folgt diesem Verweis.

[Logrotation einrichten](virtualmin-ftps/docs/LOGROTATE.md): in engine.json einstellbar; standardmäßig wöchentlich, 52 Archive, Komprimierung und Erhalt aktiver FTP-Sitzungen.
