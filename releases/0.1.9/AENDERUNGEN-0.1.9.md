# Virtualmin FTPS 0.1.9 Beta

- Beta-Kennzeichnung in Modulmetadaten, Prüfseiten-Titel und aktueller Dokumentation; Versionsnummer 0.1.9.
- ServerIdent wird bei Generierung aus dem validierten Server-FQDN ermittelt. Ungültige Namen führen zum Abbruch. Keine fest codierte Serverdomain.
- Bestehende bekannte Plugin-Konfigurationen können übernommen werden. Gespeicherte Identität schützt Driftprüfung auch nach einem Hostnamenwechsel. Fremde Änderungen werden abgewiesen.
- Domainbezogene ServerName-/ServerAlias- und Zertifikatsauswahl bleiben erhalten.
- Neues SHA-256-Manifest und separate Archivprüfsumme.

Prüfung: 10 lokale Testmethoden einschließlich Migration, Rücknahme und simuliertem Reload-Fehler bestanden. Python-Syntax und vier Perl-Dateien geprüft. Bibliotheksprüfung durch fehlendes WebminCore.pm begrenzt. Original- und neues Manifest sowie native Paketstruktur geprüft. Historische Testsuiten waren nicht enthalten. Keine Live-Abnahme oder Live-Serveränderung.

Installation über Webmin mit virtualmin-ftps-0.1.9.wbm.gz. Ein bereits aktiver Abgleich-Timer kann nach Installation die neue Begrüßung übernehmen. Hinweise zu Vorschau, Anwendung und Validierung stehen im Paket unter docs/SERVER-IDENT.md.
