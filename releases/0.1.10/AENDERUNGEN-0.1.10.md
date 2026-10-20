# 0.1.10 — Beta

- ExtendedLog und TransferLog je Domain unter dem von Virtualmin gelieferten Home-Verzeichnis.
- Fehlende Logdateien werden beim Anwenden ohne Leeren vorhandener Logs angelegt.
- Sichere Pfad-/Dateiprüfung, Übernahme alter Zustände und Erhalt der Logs bei Löschung/Rücknahme.
- Details: DOMAIN-LOGS.md. Automatisierte Regressionstests im Repository.

16 Regressionstests bestanden. Keine Live-Serverkonfiguration geändert. Ein aktiver Timer kann nach Installation die neue Konfiguration anwenden.
