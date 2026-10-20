# 0.1.15 — Beta

- Gezielte Übernahme regulärer root:root-Altlogs zusätzlich zu root:Domain-Gruppe nach Domain-Benutzer:Domain-Gruppe. Bestehende Inhalte und Dateirechte bleiben erhalten. Root-eigene logs-Verzeichnisse mit root- oder Domain-Gruppe werden ebenfalls übertragen.
- Fremde Benutzer oder nicht passende sonstige Gruppen, Symlinks, Hardlinks und weltweit beschreibbare Dateien bleiben gesperrt.
- Die Vorschau prüft jetzt vorhandene Logpfade und Eigentümer lesend; sie erzeugt keine Dateien und ändert keine Besitzer.
- AllowOverride on und AllowOverwrite on bleiben erhalten.

