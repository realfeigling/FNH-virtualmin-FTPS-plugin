# Geschützte FTP-Logs — 0.1.16 Beta

Die aktive Protokollierung verwendet einen vom Kunden nicht beschreibbaren Bereich außerhalb des Domain-Home:

```apache
ExtendedLog /var/log/virtualmin-ftps/DOMAIN-ID/ftp.log ALL
TransferLog /var/log/virtualmin-ftps/DOMAIN-ID/xferlog
```

DOMAIN-ID ist Virtualmins numerische Domain-ID. AllowOverride on und AllowOverwrite on bleiben erhalten; Kunden können weiterhin ihre normalen Dateien gemäß Unix-Rechten überschreiben.

## Eigentümer und Löschschutz

Die gemeinsame Wurzel gehört root:root mit 0711. Je Domain gehört das Verzeichnis root:Domain-Gruppe mit 0750; Dateien gehören root:Domain-Gruppe mit 0640. Gruppenmitglieder können ihre Logs lesen, aber weder schreiben noch Verzeichniseinträge löschen oder umbenennen. Root-Eigentum an einer Datei allein schützt nicht vor Löschen, wenn der Kunde deren Elternverzeichnis verändern darf. Deshalb werden aktive Logs aus dem kundenbeschreibbaren Home entfernt und in einem geschützten Verzeichnisbaum gespeichert.

Auch sämtliche Vorfahren des Zielbereichs müssen root gehören, dürfen für Gruppe/Andere nicht beschreibbar und keine Symlinks sein. Vorhandene unsichere Zielverzeichnisse oder Dateien werden abgewiesen; globale Verzeichnisrechte werden nicht automatisch verändert. Ziel-Logdateien müssen regulär sein, einen einzelnen Hardlink besitzen und root:Domain-Gruppe gehören. Symlinks und Gruppen-/Andere-Schreibrechte sind gesperrt.

Der optionale Konfigurationswert log_root kann einen anderen bereits root-kontrollierten Elternbereich verwenden. Ohne diesen neuen Eintrag in einer bestehenden engine.json gilt /var/log/virtualmin-ftps. Es wird kein separates benutzerbeschreibbares Linkziel im Home erstellt.

## Übernahme vorhandener Logs

Beim ersten Anlegen jeder Zieldatei wird ein Schnappschuss der bisherigen Datei übernommen. Quelle ist der im alten Zustand gespeicherte Logbereich oder das bisherige Home/logs. Fehlende Quellen ergeben eine neue leere Logdatei. Die Quelldateien und ihre Eigentümer/Rechte bleiben unverändert; sie werden nicht gelöscht. Unterstützt werden reguläre, einzelne Quell-Dateien des Domain-Benutzers oder root mit root- oder Domain-Gruppe. Unsichere Quellen und Symlinks werden abgewiesen.

Kopiert wird maximal die bei Öffnung beobachtete Dateigröße. Eine während der Kopie verkürzte Quelle führt zum Abbruch und Entfernen ausschließlich der neu erstellten unvollständigen Zieldatei. Bereits vorhandene Zielinhalte werden weder überschrieben noch nochmals ergänzt. Alte aktive FTP-Sitzungen können nach einem Reload weiterhin in ihre bisher geöffneten Logs schreiben; die Home-Quelldateien bleiben deshalb erhalten. Neue Verbindungen verwenden nach erfolgreicher Umstellung die geschützten Logs.

Eine Vorschau prüft bestehende Pfade und Quellen lesend. Erst --apply erstellt Verzeichnisse und Dateien. Bei Fehlern können bereits vollständig angelegte Ziel-Logs zurückbleiben; die Konfigurations-Rücknahme entfernt diese nicht. Rollback kann die vorherigen Home-Logpfade wieder aktivieren. Domain-Löschung und Deaktivierung löschen keine Protokolle. Logrotation und Aufbewahrung werden mit dieser Version nicht eingerichtet; eine vorhandene Rotation muss root-Eigentum und Domain-Gruppe beibehalten.
