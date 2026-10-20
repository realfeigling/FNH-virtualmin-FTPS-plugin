# 0.1.16 — Beta

- Aktive FTP-Logs liegen in /var/log/virtualmin-ftps/DOMAIN-ID/ und gehören root:Domain-Gruppe mit 0640. Domain-Verzeichnisse gehören root:Domain-Gruppe mit 0750, die gemeinsame Wurzel root:root mit 0711.
- Alle Vorfahren des Logbereichs müssen root gehören und dürfen für Gruppe/Andere nicht beschreibbar sein. Dadurch kann der Domain-Benutzer aktive Logs weder löschen, umbenennen noch überschreiben; er kann eigene Logs über seine Gruppe lesen.
- Bestehende Home-Logs werden beim ersten Umstellen als größenbegrenzter Schnappschuss kopiert. Quellen bleiben unverändert. Vorhandene Zielinhalte werden weder geleert noch mehrfach angehängt.
- Zustandsbasierte Übernahme der alten Logpfade; fremde Konfigurationsänderungen bleiben gesperrt. Fehlende geschützte Dateien werden auch bei ansonsten unverändertem angewendetem Abgleich angelegt.
- AllowOverride on und AllowOverwrite on bleiben für Kundendateien erhalten.
- Details: DOMAIN-LOGS.md und OWNERSHIP-UPDATE.md.

