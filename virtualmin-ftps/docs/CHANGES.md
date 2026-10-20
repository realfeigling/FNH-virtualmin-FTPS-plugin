# 0.1.11 — Beta

- AllowOverwrite on für jeden verwalteten VirtualHost: berechtigte Benutzer können bestehende Dateien überschreiben.
- Bestehende Plugin-Konfigurationen ohne diese Regel werden kontrolliert übernommen; fremde Änderungen bleiben gesperrt.
- Datei-/Benutzerrechte, TLS, Chroot und Domain-Logs bleiben erhalten.
- Details: OVERWRITE.md. Kein Überschreiben einer Live-Datei beim Paketbau.

# 0.1.10 — Beta

- ExtendedLog und TransferLog je Domain unter dem von Virtualmin gelieferten Home-Verzeichnis.
- Fehlende Logdateien werden beim Anwenden ohne Leeren vorhandener Logs angelegt.
- Sichere Pfad-/Dateiprüfung, Übernahme alter Zustände und Erhalt der Logs bei Löschung/Rücknahme.
- Details: DOMAIN-LOGS.md. Automatisierte Regressionstests im Repository.

# 0.1.9 — Beta

- Modulmetadaten, Prüfseiten-Titel und aktuelle Dokumentation kennzeichnen das Plugin als Beta.
- ServerIdent verwendet für alle Plugin-VirtualHosts den zur Laufzeit über hostname --fqdn ermittelten, validierten Server-FQDN. Kein fest eingetragener Beispielhostname, kein Domain-Fallback. Ungültige, kurze oder IP-Namen brechen die Generierung ab.
- Der gespeicherte Server-FQDN ermöglicht genaue Driftprüfungen und spätere Hostnamenänderungen. Alte Domain-Begrüßungen werden als exakt bekannte Vorgängerversion übernommen; fremde Änderungen bleiben gesperrt.
- ServerName, ServerAlias und Website-Zertifikatsauswahl bleiben domainbezogen.
- Details und Prüfgrenzen: SERVER-IDENT.md und TESTS.md.

# 0.1.8

- Webmin-Variable no_acl_check im root-only CLI explizit deklariert. Die Perl-Warnung „used only once“ entfällt; Root-Prüfung und Ablauf bleiben unverändert.

# 0.1.7

- Vorhandene Website-Zertifikate, Schlüssel und Chain direkt einbinden; keine neuen Zertifikate und keine Kopien für Betrieb oder Prüfung.
- Bestehende Hosts explizit oder beim regulären Abgleich auf direkte Website-Pfade umstellen; Login-Korrektur auch für 0.1.5 enthalten.
- Erneuerung an Inhaltshashes erkennen und auch bei gleichbleibenden Pfaden neu laden. Rücknahme setzt Website-Dateiinhalte nicht zurück.
- Bestehende alte Snapshots ausschließlich für mögliche Rücknahme erhalten; keine automatische Löschung.

# 0.1.6

- Fehlerhafte LOGIN-Reihenfolge korrigiert: Order allow,deny, Gruppenfreigabe und DenyAll. Sperrung bleibt DenyAll.
- Explizite, wiederholbare Reparatur für aktive Hosts mit genauer Prüfung des bisherigen Dateiinhalts, ProFTPD-Sperren, Syntaxprüfung, Reload und transaktionaler Rücknahme.
- Keine Änderung an Standardhost-Auswahl, Domain-Gruppen oder Zertifikaten.

# 0.1.5

- Optionaler FTPS-Standardhost über `manage.py set-default-host --domain NAME`, nur vor erster Aktivierung. Genau dieser Plugin-Host erhält DefaultServer on; keine automatische Übernahme fremder Hosts.
- Prüfseite mit Statusübersicht, grünen Häkchen, Warn-/Fehlersymbolen, strukturierten Domainangaben und korrekten Umlauten. Keine zusätzlichen aktiven Prüfungen oder Konfigurationsänderungen durch die Seite.
- Standardhost-Rolle und Grenzen der IP-/Namensauswahl dokumentiert.

# Änderungen 0.1.4

Sichtbare Prüfausgabe und Menübeschriftung verwenden echte Umlaute: „FTPS prüfen“, „Prüfung“, „Prüfmodus“, „Schlüssel“ und weitere deutsche Texte. Der HTML-/Text-Formatter verarbeitet die Texte als Unicode; die vorhandene Ausgabegrenze kodiert sie als UTF-8. Keine Änderung an FTPS-Verwaltungslogik oder aktiver Konfiguration.

# Änderungen 0.1.3

- Fehlerursache des Screenshots korrigiert: Der Domain-Menüeintrag verwendete `link`, während Virtualmin den Modulpfad aus `mod` und `page` erzeugt. Der neue Eintrag übergibt die Domain-ID im richtigen Feld.
- Neuer Regressionstest führt die echte, aus dem bereitgestellten Archiv extrahierte Funktion `get_all_domain_links` mit dem Plugin-Eintrag aus und verfolgt die Domain-ID bis zum lesbaren Prüfbericht. Keine Wahl einer anderen oder ersten Domain als Fallback.
- Neuer expliziter Befehl `collect.pl --refresh-menu` erneuert Virtualmins Menücache über `clear_links_cache`. Kein FTPS-Backendaufruf, kein Reload, keine Zertifikatsprüfung.
- Bestehende Konfiguration und Prüfmodus benötigen keine Neuinitialisierung. Nach Upload einmal Menücache erneuern und Browser mit Strg+F5 neu laden.

# Änderungen 0.1.2

- Eigene read-only Operation `inspect` für genau eine Domain. Keine Fremd-Zertifikatsprüfung, keine Vollsynchronisierung, kein globaler ProFTPD-Syntaxlauf in der Domain-Prüfseite.
- Lesbare deutsche Prüftabellen mit getrennten Domainergebnissen und gemeinsamen Voraussetzungen. Technische Fehlerdetails bleiben eingeklappt, keine rohe JSON-Darstellung. Die CLI-Einzelprüfung ist ebenfalls lesbar, JSON optional mit `--json`.
- Ohne ausgewählte Domain zeigt die Modulstartseite einen Kontext-Hinweis statt einer Liste aller Domains.
- Reiner VirtualHost-Betrieb setzt im Hauptserver `Port 0` und `DefaultServer off` voraus. Die frühere Forderung nach globalem `TLSEngine on` entfällt. Keine automatische globale Konfigurationsänderung.
- Eigene Hosts haben explizit `Port 21`, `DefaultServer off`, `ServerName`, `ServerAlias` und `ServerIdent` mit dem Domainnamen. Begrenzungen der allerersten Begrüßung vor HOST/SNI sind dokumentiert.
- Neue Tests für den Domainumfang, andere defekte Zertifikatspfade, unveränderte aktive Dateien, verweigerte schreibende Prüfaufrufe, deaktivierten Hauptserver und HTML-Escaping/lesbare Darstellung.

# Änderungen 0.1.1

- Eigenes natives Webmin-Modularchiv mit exakt `virtualmin-ftps/module.info` an der erwarteten Stelle. Das vollständige Installationsarchiv bleibt separat erhalten.
- `manage.py` läuft sowohl aus dem Entwicklerpaket als auch direkt aus dem hochgeladenen Modul. Neuer Befehl `setup` initialisiert das bereits installierte Modul im Prüfmodus.
- Die Modulstartseite zeigt ohne vorbereitete Konfiguration den Einrichtungshinweis; danach eine Domainauswahl statt einer ungültigen Domain-ID.
- Drei Tests für die Upload-Einrichtung und ein Pakettest für Archivwurzel, Prüfsummen und Ausführbarkeit des Managers aus dem tatsächlich entpackten `.wbm.gz`.
- Keine neue automatische Aktivierung, keine neuen Virtualmin-Hooks, keine Änderung am ProFTPD-Konfigurationsformat. Der Ownership-Header der verwalteten Datei bleibt zur Formatkompatibilität bei 0.1.0.

Der Webmin-Uploader selbst wurde hier nicht ausgeführt. Die native Archivstruktur und die Einrichtungspfade sind lokal geprüft. Es gibt keinen unbestätigten automatischen Postinstall-Hook; die Einrichtung erfolgt ausdrücklich mit `setup`.
