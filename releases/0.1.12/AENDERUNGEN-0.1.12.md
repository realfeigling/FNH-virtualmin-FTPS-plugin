# 0.1.12 — Beta

- Korrektur der ausdrücklichen Migration: bereits auf den validierten lokalen Server-FQDN geänderte ServerIdent-Zeilen werden auch bei altem Zustand ohne server_fqdn übernommen.
- Ausschließlich bytegenau bekannte Konfigurationsvarianten werden akzeptiert; weitere Änderungen und fremde Begrüßungsnamen bleiben gesperrt.
- Erfolgreicher Abgleich übernimmt auch Domain-Logs und AllowOverwrite aus 0.1.10/0.1.11.
- Anleitung: GREETING-MIGRATION.md. Keine Live-Serveränderung beim Paketbau.

