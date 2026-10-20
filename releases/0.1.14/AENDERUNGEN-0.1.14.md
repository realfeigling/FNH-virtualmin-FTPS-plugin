# 0.1.14 — Beta

- Logs gehören dem von Virtualmin gemeldeten Domain-Benutzer und seiner Domain-Gruppe. Vorhandene passende Logs behalten Eigentümer, Gruppe, Rechte und Inhalt; neue Dateien erhalten diese Identität und 0640.
- Reguläre root-eigene Logs mit bereits passender Domain-Gruppe aus früheren Versionen werden beim Anwenden ohne Leeren auf den Domain-Benutzer übertragen. Bestehende root-eigene Logverzeichnisse mit passender Gruppe werden ebenfalls übertragen. Andere Eigentümer-/Gruppenabweichungen bleiben gesperrt.
- Gruppen-Schreibrechte sind bei passender Domain-Gruppe erlaubt. Weltweit beschreibbare Dateien, Symlinks, Hardlinks und ungeeignete Dateitypen bleiben gesperrt. Fehlermeldungen nennen den konkreten Pfad und die Eigentümer-/Rechtewerte.
- Jeder verwaltete Host erhält AllowOverride on und weiterhin AllowOverwrite on. AllowOverride erlaubt .ftpaccess-Dateien; AllowOverwrite erlaubt das Überschreiben innerhalb der bestehenden Unix-Rechte.
- Bekannte alte Zustände mit AllowOverride off werden kontrolliert übernommen. Kein manuelles Bearbeiten der verwalteten Datei nötig.
- Details: DOMAIN-LOGS.md und OWNERSHIP-UPDATE.md.

