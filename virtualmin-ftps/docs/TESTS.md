# Prüfung 0.1.16 Beta

23 isolierte Domain-/Log-/Migrationstests, 3 Perl-Descriptor-/Python-Übergabeprüfungen und 4 Archivprüfungen sind eingerichtet. Geprüft werden root-Eigentum und Domain-Gruppenleserechte, ein tatsächlicher Prozess mit Domain-UID/GID beim Versuch zu löschen/umzubenennen/überschreiben (muss abgewiesen werden), lesbarer Loginhalt für die Domain-Gruppe, Quell-Schnappschüsse ohne Quellenänderung, Wiederholbarkeit ohne doppelte Inhalte, Vorschau ohne Dateianlage, Symlink-/Hardlink-/Rechteabwehr, Übernahme alter Home-Pfade und Server-Begrüßungen, Dateianlage bei unverändertem Abgleich, Driftabwehr und Rücknahme bei simuliertem Reload-Fehler.

Die bisherigen ausschließlich auf kundenbeschreibbare Home-Logs gerichteten Eigentümertests wurden durch Tests des geschützten Verzeichnisbaums ersetzt. Der Löschschutz wird unter Linux durch echte UID-/GID-Absenkung geprüft. ProFTPD-Syntaxprüfung und systemd-Reload bleiben simuliert. Kein echter FTP-Livetest. Ergebnisse siehe GitHub Actions.

# Prüfung 0.1.15 Beta

38 automatisierte Tests: 31 Domain-/Migrationsfälle, 3 Perl-Descriptor-/Python-Übergabeprüfungen und 4 Paketprüfungen. Neue Fälle prüfen die unveränderte root:root-Datei in der Vorschau, die anschließende Übertragung von Datei und Verzeichnis auf Domain-Benutzer/Gruppe mit Erhalt der 0644-Rechte und Inhalte, Ablehnung fremder root-Gruppen sowie Eigentümerfehler bereits in der Vorschau ohne Änderung von Konfiguration, Zustand oder Logs.

Echte isolierte Linux-Dateisystemtests, simulierte ProFTPD-/systemd-Aufrufe. Kein Live-Serverzugriff. Ergebnisse: GitHub Actions.

# Prüfung 0.1.14 Beta

35 automatisierte Tests: 28 Domain-/Migrationsfälle, 3 Perl-Descriptor-/Python-Übergabeprüfungen und 4 Archivprüfungen. Neue Fälle prüfen UID 1015/GID 1018 mit 0644 unverändert, Neuanlage mit echter nicht-root-Domain-Identität, zulässige Gruppen-Schreibrechte, Migration root-eigener Altlogs ohne Leeren, fremde Eigentümer/Gruppen mit konkreten Fehlermeldungen, fehlende Benutzerangaben, Vorschau ohne chown und Übernahme von AllowOverride off nach on. AllowOverwrite on bleibt je Host geprüft.

Die Datei- und Eigentümerprüfungen laufen unter Linux im CI als root, mit echten fchown-/Dateisystemoperationen an isolierten Testdateien. Virtualmin-SSL-Aufrufe, ProFTPD-Syntaxprüfung und systemd-Reload bleiben simuliert. Kein echter Webmin-/FTPS-Livetest. Paketmanifest, Archivprüfsumme, Berechtigungen und Bytegleichheit der Paketdateien zum Quellstand werden geprüft. Ergebnisse siehe GitHub Actions.

# Prüfung 0.1.13 Beta

27 automatisierte Tests eingerichtet: 20 Domain-/Migrationsprüfungen, 3 Perl-Descriptor-/Python-Übergabeprüfungen und 4 Paketprüfungen. Neue Fälle: Virtualmin dir=1 mit tatsächlichem home, Subserver-Pfad, fehlendes home und deaktivierte Verzeichnisfunktion. Die echte Plugin-Descriptor-Funktion wird aus der Quelldatei ausgeführt; Virtualmin-SSL-Aufrufe sind simuliert. Python-Syntax und vier Perl-Syntaxprüfungen sind Teil der GitHub-Actions-Prüfung.

ProFTPD und Reload in den Transaktionstests simuliert. Kein echter Webmin-Lauf und keine Live-Serveränderung. Ausführungsergebnisse siehe GitHub Actions.

# Prüfung 0.1.12 Beta

20 Domain-/Migrations-Regressionstests und 4 Paketprüfungen sind eingerichtet. Drei neue Fälle prüfen die exakte Befundkonstellation (Server-Begrüßung bereits geändert, server_fqdn fehlt), Vorschau ohne Änderung, erfolgreiche Anwendung mit Zustand/Logs/AllowOverwrite, Wiederholbarkeit sowie Ablehnung veränderter Ports oder fremder Begrüßungsnamen. Ausführung und Ergebnisse: GitHub Actions. ProFTPD und Reload werden in den Transaktionstests simuliert; keine Live-Abnahme.

# Prüfung 0.1.11 Beta

17 Domain-/Migrations-Regressionstests und 4 Paketprüfungen sind für diese Version eingerichtet. Die neue Prüfung betrifft die Übernahme eines 0.1.10-Zustands, Vorschau ohne Änderung, AllowOverwrite in jedem Host, Wiederholbarkeit sowie Erhalt von Loginhalt und Logrechten. Ergebnisse siehe GitHub Actions. ProFTPD und Reload weiterhin simuliert; kein echter FTP-Upload oder Überschreiben einer Live-Datei.

# Prüfung 0.1.10 Beta

20. Oktober 2026: 16 Python-Regressionstests auf GitHub Actions (Ubuntu, root-only Backend) bestanden. Geprüft: getrennte Domain-Logpfade, ungültige/fehlende Homes, sichere Dateianlage und Erhalt vorhandener Inhalte, Symlink-/Hardlink-/Rechteabwehr, doppelte Homes, Vorschau ohne Dateianlage, Übernahme alter Zustände, Wiederholbarkeit, Erhalt der Logs bei Domain-Löschung, Driftabwehr und Rücknahme bei simuliertem Reload-Fehler.

Python-Syntax und vier Perl-Syntaxprüfungen bestanden. ProFTPD-Syntaxprüfung und systemd-Reload in den Transaktionstests simuliert; keine Live-Abnahme. Die WebminCore-abhängige Perl-Bibliothek wurde nicht im echten Webmin ausgeführt. Paketstruktur, Prüfsummen und Übereinstimmung mit dem Quellstand werden zusätzlich automatisiert geprüft.

# Prüfung 0.1.9 Beta

20. Oktober 2026: 10 lokale Testmethoden bestanden (einschließlich negativer FQDN-Unterfälle): gültige/normierte Namen, ungültige/kurze/IP-/Steuerzeichen-Namen, Ermittlungsfehler, Domain-ServerName/ServerAlias bei Server-FQDN-Begrüßung, alte Domain-Identität und Login-Reihenfolge, gespeicherte Identität, mehrere Hosts mit einmaliger Ermittlung, leere Hostliste, Migration/Hostnamenwechsel/Rücknahme/Driftabwehr und Wiederherstellung nach Reload-Fehler. ProFTPD-Syntaxprüfung und Reload sind in den Transaktionstests simuliert; keine Live-Konfiguration wurde geändert.

Python-Syntaxprüfung für engine.py und manage.py bestanden. Perl-Syntaxprüfung für index.cgi, collect.pl, report-lib.pl und virtual_feature.pl bestanden. virtualmin-ftps-lib.pl konnte mangels WebminCore.pm nicht vollständig geprüft werden; die Bibliothek ist unverändert. Die historischen vollständigen Testsuiten sind im bereitgestellten Installationspaket nicht enthalten und wurden nicht erneut ausgeführt.

Original-Manifest geprüft. Neues Archiv: gzip/Tar lesbar, native Wurzel virtualmin-ftps/module.info, vollständiges SHA-256-Manifest, Versions-/Beta-Metadaten und ausführbare Skripte geprüft. Kein echter ProFTPD-/Webmin-Integrationstest oder FTPS-Login.

# Prüfung 0.1.7

Erfolgreich: 65 Python-Tests, 43 Perl-Hook-/Darstellungsprüfungen und 21 native Menüprüfungen. Neu geprüft: direkte Originalpfade, unveränderte Website-Dateien, keine erzeugten PEM-/Schlüsselkopien, Erneuerung trotz gleichbleibender Konfiguration mit Reload, Migration aus alten Snapshots einschließlich Login-Korrektur, Vorschau ohne Änderung, Rücknahme auf alte Referenzen, Abbruch bei falschem Schlüssel/fremder Änderung und Ablehnung unsicherer Dateipfade.

Echte OpenSSL-Testzertifikate; ProFTPD/systemd weiterhin simuliert. Keine Live-Abnahme des Zielservers.

# Prüfung 0.1.6

Erfolgreich: 62 Python-Tests sowie 43 Perl-Hook-/Darstellungsprüfungen und 21 Prüfungen der nativen Menüfunktion. Neu: Reparatur-Vorschau ohne Konfigurationsänderung/Reload, genaue Inhaltsprüfung, unveränderter Domainzustand, wiederholbarer Aufruf, transaktionale Rücknahme, Syntaxfehler und Reload-Fehler mit Erhalt der alten Datei, korrekte neue LOGIN-Reihenfolge und weiterhin gesperrte Domains.

Die Bedeutung von Order wurde gegen die offizielle ProFTPD-1.3.8-Dokumentation überprüft. Ein echter FTPS-Login ist weiterhin auf dem Zielsystem nachzuweisen.

# Prüfung 0.1.5

Erfolgreich: 57 Python-Tests, 43 Perl-Hook-/Darstellungsprüfungen und 21 Prüfungen der nativen Virtualmin-Menüfunktion. Neu geprüft: Auswahl nur vor Erstaktivierung, ungültige Standardhost-Namen, genau ein DefaultServer on, TLS-Pflicht, übrige Hosts off, Reihenfolge innerhalb der eigenen Datei, Rollenanzeige, Entfernen des Standardhosts sowie grüne/gelbe/rote Statusübersicht und HTML-Escaping.

ProFTPD und systemd sind simuliert; Zertifikatsprüfungen verwenden OpenSSL. Keine Live-Abnahme oder Prüfung des tatsächlichen Browser-Themes.

# Prüfung der Textkorrektur 0.1.4

Die Änderung betrifft ausschließlich deutsche Oberflächentexte und UTF-8-Verarbeitung. Bestehende Perl-Hook-/Ausgabeprüfungen und der native Pakettest werden erneut ausgeführt. Die FTPS-Verwaltungslogik wurde nicht verändert; der vollständige Backend-Teststand der Vorversion bleibt unten als historischer Nachweis erhalten. Eine Anzeigeprüfung im Browser des Nutzers steht nach dem Upload noch aus.

# Testnachweis 0.1.3

Stand: 19. Oktober 2026.

- Python: 54 Tests bestanden, einschließlich Quellvertrag und nativer Paketstruktur.
- Perl-Hooks und lesbare Ausgabe: 38 Assertions bestanden.
- Neues Menü-Integrationstestskript: 21 Assertions bestanden.
- Syntax: drei Python-Dateien und fünf Perl-Dateien geprüft.

Der neue Test extrahiert `get_all_domain_links` aus der vom Nutzer bereitgestellten Virtualmin-8.3-Quelle und führt genau diese Funktion aus. Der Plugin-Eintrag muss dadurch `/virtualmin-ftps/index.cgi?dom=ID` ergeben. Für zwei unterschiedliche ausgewählte Domains wird dieser tatsächlich erzeugte Link bis zum lesbaren Prüfbericht verfolgt. Backend-Operation ist ausschließlich `inspect`, schreibendes Anwenden ist aus. Falsche Antwort-Domain-IDs werden abgelehnt. Die Menücache-Erneuerung verwendet den nativen Helper ohne Backend-Aufruf.

Bei der Ausführung meldet die isolierte native Menüfunktion eine Warnung zu einem nicht belegten Kategorieeintrag im Testkontext; alle Assertions bestehen. Es ist kein Fehler im erzeugten FTPS-Link. Die umgebenden Webmin-Dienste sind simuliert. Ohne Nutzerquellen überspringt `tests/test_menu.pl` diese Integration ausdrücklich; die Nutzerquellen werden nicht weiterverteilt.

Die bisherigen OpenSSL-/Transaktions-/Rollbacktests bleiben enthalten. Ein echter Klick im Webmin des Nutzers und eine echte FTPS-Verbindung sind nach diesem Update noch zu bestätigen. Es wurden keine produktiven Konfigurationsänderungen aus dieser Arbeitsumgebung durchgeführt.
