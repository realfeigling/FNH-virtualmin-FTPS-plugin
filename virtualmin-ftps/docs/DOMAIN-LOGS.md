# Domainbezogene FTP-Logs — 0.1.14 Beta

Das Home-Verzeichnis stammt aus Virtualmins home-Feld; dir ist ausschließlich das Aktivierungsmerkmal. Benutzer und Gruppe stammen aus user und group. Benutzer-/Gruppennamen werden im Backend über die lokale Unix-Benutzerverwaltung aufgelöst.

Beispiel für einen Host mit dem Home-Verzeichnis /data/www/pages/u607101601:

```apache
AllowOverride on
AllowOverwrite on
ExtendedLog /data/www/pages/u607101601/logs/ftp.log ALL
TransferLog /data/www/pages/u607101601/logs/xferlog
```

Jeder Host erhält seine eigenen Pfade. Mehrere Hosts mit identischem Home-Verzeichnis werden bei Anwendung abgewiesen.

## Eigentümer und Erhalt

Fehlende Logverzeichnisse werden mit Domain-Benutzer:Domain-Gruppe und 0750, fehlende Logdateien mit Domain-Benutzer:Domain-Gruppe und 0640 angelegt. Bestehende passende Domain-Logs behalten Eigentümer, Gruppe, Rechte und Inhalt. Auch bestehende 0644- oder 0664-Dateien werden akzeptiert; Schreibrechte für Andere bleiben gesperrt.

Reguläre root-eigene Logdateien mit passender Domain-Gruppe werden beim angewendeten Abgleich auf den Domain-Benutzer übertragen. Das korrigiert die Anlage durch frühere Plugin-Versionen. Rechte und Inhalt bleiben dabei erhalten. Root-eigene logs-Verzeichnisse mit passender Gruppe werden ebenfalls übertragen. Andere fremde Eigentümer oder Gruppen werden mit einer Meldung einschließlich Pfad und Ist-/Sollwerten abgewiesen. Bestehende Domainverzeichnisse werden nicht pauschal umgechownt.

Symlinks, nicht reguläre Dateien, Mehrfach-Hardlinks und weltweit beschreibbare Verzeichnisse bleiben gesperrt. Dateien werden relativ zu geöffneten Verzeichnisdeskriptoren ohne Symlink-Verfolgung geöffnet. Die bestehenden ProFTPD-Logschutzregeln bleiben erforderlich; Domain-Besitzer können Pfade unter ihrem Home weiterhin umbenennen.

Vorschauen erstellen keine Logs und ändern keine Eigentümer, Rechte, Konfiguration oder Zustandsdateien. Erst Anwendung erstellt Dateien bzw. korrigiert die beschriebenen root-eigenen Altdateien. Logs bleiben bei Domain-Löschung, Deaktivierung und Rücknahme erhalten. Bei Fehlern können neu angelegte Dateien und bereits korrigierte Log-Eigentümer zurückbleiben; der Konfigurations-Rollback setzt Dateieigentümer nicht zurück. Aufbewahrung und Logrotation werden nicht neu eingerichtet.

## Anwendung

Modul installieren, dann den bestehenden vollständigen Abgleich zuerst ohne --apply als Vorschau ausführen. Nach erfolgreicher Vorschau mit --apply übernehmen. Details: OWNERSHIP-UPDATE.md. Ein bereits aktiver Timer kann nach Installation automatisch abgleichen.
