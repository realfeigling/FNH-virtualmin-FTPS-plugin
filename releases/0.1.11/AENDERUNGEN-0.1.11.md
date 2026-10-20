# 0.1.11 — Beta

- AllowOverwrite on für jeden verwalteten VirtualHost: berechtigte Benutzer können bestehende Dateien überschreiben.
- Bestehende Plugin-Konfigurationen ohne diese Regel werden kontrolliert übernommen; fremde Änderungen bleiben gesperrt.
- Datei-/Benutzerrechte, TLS, Chroot und Domain-Logs bleiben erhalten.
- Details: OVERWRITE.md. Kein Überschreiben einer Live-Datei beim Paketbau.

Keine Live-Serverkonfiguration geändert. Ein aktiver Timer kann die neue Regel nach Installation anwenden.
