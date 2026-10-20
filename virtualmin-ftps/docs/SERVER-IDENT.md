# ServerIdent — 0.1.9 Beta

Bei jeder neuen Konfigurationsgenerierung wird `/usr/bin/hostname --fqdn` ausgeführt. Akzeptiert werden ASCII-/Punycode-FQDNs mit mindestens zwei gültigen Labels, maximal 253 Zeichen, ohne IP-Adresse oder Steuerzeichen. Großschreibung wird normalisiert, ein abschließender DNS-Punkt entfernt. Fehler führen zum Abbruch vor dem Schreiben und Reload. Es gibt keinen Ersatz durch eine Domain oder einen fest codierten Servernamen.

Alle verwalteten VirtualHosts erhalten `ServerIdent on "SERVER-FQDN"`. ServerName, ServerAlias und Zertifikatsprüfung verwenden weiterhin die jeweilige Domain. Die globale Hauptserver-Konfiguration wird dadurch nicht geändert.

Das Installieren des Moduls allein schreibt keine ProFTPD-Konfiguration. Ein bereits aktiver Timer oder ein späterer angewendeter Abgleich kann die bekannte alte Plugin-Datei automatisch umstellen. Der bestehende Aufruf `collect.pl --use-website-certificates` zeigt die Umstellung als Vorschau; mit `--apply` erfolgt die bisherige transaktionale Anwendung einschließlich Syntaxprüfung und Reload. Diese Aktionen wurden beim Paketbau nicht ausgeführt.

Der im Zustand gespeicherte bisherige FQDN dient ausschließlich der Driftprüfung. Neue Ausgabe verwendet den aktuell ermittelten Namen. Unbekannte Änderungen an der verwalteten Datei werden weiterhin abgelehnt. Rücknahme stellt die vorherige Datei und den vorherigen Zustand wieder her.
