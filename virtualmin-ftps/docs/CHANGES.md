# 0.1.24 — Beta

## Formularübermittlung mit Authentic Theme korrigiert

Das Authentic Theme kann bei AJAX-Aufrufen die HTTP-Methode aus dem ersten sichtbaren Formular mit passender Zieladresse bestimmen. Bisher hatten Host-Auswahl (GET) und Einstellungen (POST) beide rotation.cgi als Ziel. Dadurch konnte die Speicherung trotz POST-Speicherformular als GET übertragen werden. Die Sicherung der ursprünglichen HTTP-Methode in 0.1.23 allein behebt diesen Fall nicht.

Die Seite verwendet jetzt genau ein POST-Formular für Auswahl, Prüfung und Speichern. „Anzeigen“ wechselt ausschließlich die Ansicht und hat Vorrang vor Speicheraktionen. Das angezeigte Bearbeitungsziel wird separat gespeichert: Die Auswahl eines anderen Hosts im Dropdown allein leitet eine Speicherung nicht auf diesen Host um.

POST-Pflicht, Administratorprüfung, Sitzungstoken, paralleler Änderungsschutz und Rücknahme bei Schreibfehlern bleiben unverändert. Kein Akzeptieren von GET-Schreibzugriffen als Umgehung.

Nach Modul-Update die FTP-Logrotation über den Menüeintrag frisch öffnen; eine bereits offene Fehlerseite schließen. Anschließend „Nur prüfen“ und „Speichern und anwenden“ verwenden. Bestehende Konfigurationen und Logs bleiben erhalten. Keine Live-Serveränderung beim Paketbau.

Zusätzliche Tests parsen die tatsächlich erzeugte HTML-Struktur, prüfen genau ein POST-Formular mit allen Bedienelementen, simulieren die Methodenwahl des Themes anhand des ersten passenden Formulars und prüfen Hostwechsel ohne Schreiben sowie Speichern für das angezeigte Ziel.

Referenz: get_pjax_type in https://github.com/webmin/authentic-theme/blob/master/unauthenticated/js/bundle.min.js

# 0.1.23 — Beta

Behebt die Meldung „Speichern erfordert ein Formular mit POST“ bei der Webmin-Logrotation, wenn die CGI-Umgebung beim Laden weiterer Module bereinigt wird. Die ursprüngliche HTTP-Methode wird vor der Initialisierung gesichert und sowohl beim Einlesen als auch bei der Formularprüfung verwendet.

Gültige POST-Anfragen funktionieren auch nach einer Umgebungsbereinigung. GET-Schreibzugriffe, fehlende oder falsche Sitzungstoken und fehlende Administratorrechte bleiben abgewiesen. Nach einem Formularfehler wird die Einstellungsmaske mit den gespeicherten Werten erneut angeboten, sofern die Leseabfrage gelingt.

Nach dem Modul-Update FTP-Logrotation frisch öffnen und „Nur prüfen“ beziehungsweise „Speichern und anwenden“ verwenden. Kein manueller Eingriff in engine.json nötig. Bestehende Konfiguration, Archive und Schutzrechte bleiben erhalten. Keine Live-Serveränderung beim Paketbau.

Neue Regressionstests führen die tatsächliche CGI-Datei aus, löschen während der Administratorprüfung REQUEST_METHOD aus der Umgebung und prüfen erfolgreichen POST, Vorschau ohne Speichern sowie fortbestehende GET-/Token-Abweisung. Die vorherigen Prüfungen laufen weiter.

# 0.1.22 — Beta

## Logrotation direkt in Webmin

Im FTPS-Modul den Link **FTP-Logrotation einstellen** öffnen. Alternativ in Virtualmin den FTP-Host wählen und unter **Logs and Reports → FTP-Logrotation** öffnen. Die Einstellungsseite ist Hauptadministratoren vorbehalten; Kunden behalten ausschließlich ihre bisherigen Leseansichten.

- **Gemeinsame Vorgaben** oder einzelnen FTP-Host aus der Liste wählen; die Domain-ID muss nicht eingegeben werden.
- Rotation **täglich**, **wöchentlich** oder **monatlich**, Anzahl Archive und optionale Größenrotation bearbeiten.
- Bei einem Host **Gemeinsame Vorgaben übernehmen** aktivieren, um die eigene Regel zu entfernen und den Standard zu verwenden.
- **Nur prüfen** prüft Logrotate ohne Speichern oder Rotation.
- **Speichern und anwenden** speichert engine.json und installiert die geprüfte Logrotate-Regel. Kein zusätzlicher Shell-Befehl erforderlich. Die nächste Rotation übernimmt der vorhandene System-Logrotate-Zeitplan.

Standard bleibt wöchentlich mit 52 Archiven und ohne zusätzliche Größenrotation. Voraussetzung: konfigurierte Domain-Logs und installiertes logrotate. Eine angemeldete Webmin-Sitzung ist zum Speichern erforderlich. Parallele Konfigurationsänderungen führen zum erneuten Laden statt Überschreiben. Bei Fehlern beim Schreiben werden beide Dateien wiederhergestellt. Unbeteiligte Engine-Einstellungen bleiben erhalten.

## Zeichenkodierung

Der gemeldete Menütext FTPS pr�fen wurde auf korrekte UTF-8-Byteausgabe an Webmin umgestellt. Die neue Einstellungsseite gibt deutsche Beschriftungen konsistent in UTF-8 aus. Automatische Tests prüfen die tatsächlichen Bytes und die Formularausgabe. Vorhandener Verweis /var/log -> /data/log und geschützte FTP-Leseansichten bleiben erhalten.

Nach Modul-Update die Browserseite neu laden. Falls der neue Link im Virtualmin-Menü fehlt, als root den Menücache erneuern:

```sh
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --refresh-menu
```

Keine Live-Serveränderung beim Paketbau. copytruncate und seine dokumentierte mögliche kurze Protokollierungslücke bleiben unverändert.

# 0.1.21 — Beta

Logrotation ist in /etc/webmin/virtualmin-ftps/engine.json einstellbar. Standard: wöchentlich, 52 Archive, keine zusätzliche Größenrotation. Bestehende Konfigurationsdateien werden beim Modul-Update nicht überschrieben. Fehlt der Abschnitt, gelten diese Standardwerte beim nächsten install-logrotate-Aufruf.

## Konfiguration

Diesen Abschnitt als zusätzliches Feld in das vorhandene JSON-Objekt einfügen (bestehende Angaben wie state_dir und managed_file behalten; Komma zum Nachbarfeld beachten):

```json
"logrotate": {
  "interval": "weekly",
  "rotate": 52,
  "maxsize": null
}
```

- interval: daily, weekly oder monthly.
- rotate: Anzahl Archive je Logdatei, ganze Zahl von 1 bis 3660. weekly/52 entspricht bei regelmäßiger Rotation ungefähr einem Jahr; daily/365 oder monthly/12 sind Alternativen. Leere Dateien werden nicht rotiert, deshalb ist dies keine taggenaue Löschfrist.
- maxsize: null deaktiviert zusätzliche größenbedingte Rotation. Optional beispielsweise 100M, 1G oder 500k. Zusätzliche Rotationen verbrauchen Archive und verkürzen bei fester Anzahl die Aufbewahrungsdauer. Die Größe wird nur bei System-Logrotate-Läufen geprüft.

## Änderung prüfen und übernehmen

```sh
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py check-logrotate
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py install-logrotate
```

Der erste Befehl prüft ohne Installation oder Rotation. Der zweite erzeugt /etc/logrotate.d/virtualmin-ftps neu aus den Einstellungen. Eine bereits installierte Regel aus 0.1.20 bleibt bis dahin unverändert. Die Regel nicht direkt bearbeiten, da sie bei erneuter Installation ersetzt wird. Fremde Regeln ohne Plugin-Markierung werden nicht überschrieben. Kein ProFTPD-Neustart nötig.

Komprimierung, verzögerte Komprimierung, geschützte Root-/Gruppenrechte, fehlende/leere Dateien überspringen und copytruncate bleiben feste sichere Vorgaben. /var/log -> /data/log wird weiterhin unterstützt. Der reguläre System-Logrotate-Zeitplan führt die Rotation aus; logrotate muss installiert sein.

copytruncate erhält geöffnete FTP-Dateien, kann aber zwischen Kopieren und Kürzen einzelne neu geschriebene Zeilen verlieren. Archive sind in der schreibgeschützten FTP-Ansicht lesbar; Logs and Reports zeigt die aktuellen Dateien.

Quellen: https://github.com/logrotate/logrotate/blob/main/logrotate.8.in und https://github.com/proftpd/www.proftpd.org/blob/master/docs/howto/Logging.html

Keine Live-Serverkonfiguration beim Paketbau geändert.

# 0.1.20 — Beta

- Logrotate-Konfiguration für ftp.log und xferlog aller numerischen Domain-Verzeichnisse ergänzt.
- Täglich, 14 Rotationen, maxsize 100M bei jedem regulären Logrotate-Lauf, missingok, notifempty, compress und delaycompress. Keine harte 100-MB-Obergrenze zwischen Läufen.
- copytruncate erhält aktive Datei, Inode, Root-Eigentum und Domain-Gruppenrechte; bestehende FTP-Sitzungen und schreibgeschützte Kundenansichten bleiben nutzbar. Kein ProFTPD-Neustart oder Reload durch die Rotation.
- /var/log -> /data/log wird auf die geprüfte physische Quelle aufgelöst. Bei späterem Wechsel von log_root die Konfiguration erneut installieren.
- Vorschau validiert mit logrotate --debug. Installation schreibt ausschließlich /etc/logrotate.d/virtualmin-ftps, root-eigen mit 0644; fremde Konfigurationen werden nicht überschrieben. Vorhandene Logdateien werden beim Installieren nicht rotiert.

## Einrichtung nach Modul-Installation und angelegten Domain-Logs

Logrotate muss installiert sein (Debian: apt-get install logrotate). Der reguläre System-Logrotate-Timer oder Cronjob übernimmt die Ausführung; das Plugin legt keinen zweiten Rotationszeitplan an.

```sh
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py check-logrotate
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py install-logrotate
logrotate --debug /etc/logrotate.d/virtualmin-ftps
```

Kopieren und anschließendes Kürzen sind nicht atomar: Logzeilen, die genau dazwischen geschrieben werden, können verloren gehen. ProFTPD empfiehlt copytruncate bzw. delaycompress für weiter offene Logs. Die Archive bleiben in denselben geschützten Domain-Verzeichnissen und sind über die FTP-Ansicht lesbar; Logs and Reports zeigt weiterhin die aktuellen Dateien.

Quellen: https://github.com/proftpd/www.proftpd.org/blob/master/docs/howto/Logging.html und https://github.com/logrotate/logrotate/blob/main/logrotate.8.in

Kein Zugriff auf die Live-Serverkonfiguration beim Erstellen oder Testen des Pakets. Installation der Rotation erfolgt erst mit dem oben gezeigten Befehl.

# 0.1.19 — Beta

- Behebt die Ablehnung eines root-eigenen /var/log-Verweises wie /var/log -> /data/log.
- Verweis und /var werden geprüft; Zielverzeichnis und sämtliche Ziel-Eltern müssen echte root-eigene Verzeichnisse ohne Gruppen-/Welt-Schreibrechte sein. Weitere Verweise im Zielpfad werden abgewiesen.
- ProFTPD verwendet weiterhin /var/log/virtualmin-ftps-logs/DOMAIN-ID. Bei /var/log -> /data/log liegen die Dateien physisch unter /data/log/virtualmin-ftps-logs/DOMAIN-ID.
- Die schreibgeschützte FTP-Einhängung verwendet das geprüfte tatsächliche Ziel. Historische Logübernahme unterstützt denselben Verweis.
- Root-Eigentum, Kundengruppen-Leserechte, Logs and Reports sowie AllowOverride on und AllowOverwrite on bleiben erhalten. Keine Änderung des Systemverweises oder seiner Zielrechte; kein automatisches Löschen alter Dateien.

Nach Installation zuerst Vorschau und anschließend Anwendung:

```sh
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
```

Ein aktiver Plugin-Timer kann nach Installation selbst abgleichen. Bei Umstellung während aktiver FTP-Sitzungen alte Dateien behalten, da bestehende Sitzungen dort weiter protokollieren können. Keine Live-Serveränderungen beim Paketbau.

# 0.1.18 — Beta

- Neue Standardablage: /var/log/virtualmin-ftps-logs/DOMAIN-ID. Alte automatische log_root-Werte werden umgestellt; individuelle andere Pfade bleiben erhalten.
- Originale bleiben root-eigen (Dateien 0640, Domain-Gruppe lesbar). FTP-Ansicht logs/ftps bleibt schreibgeschützt; Logs and Reports bleibt erhalten.
- Pfadwechsel löst die bisherigen eigenen Bind-Mounts und bindet die neue Quelle ein; Vorschau prüft die bisherige Ansicht. Wiederherstellung bei fehlgeschlagenem Anwenden bleibt enthalten.
- /var/log darf root gehören und von root, syslog oder adm gruppenschreibbar sein, sofern alle Gruppenmitglieder Systemkonten mit UID unter 1000 sind. Andere gruppenschreibbare Eltern, Symlinks und Welt-Schreibrechte werden abgewiesen. Keine Änderung der /var/log-Rechte.
- Vorhandene Logs werden bei fehlendem Ziel als begrenzter Schnappschuss übernommen; alte Dateien bleiben erhalten. Kein automatisches Verschieben oder Löschen.

Vor Installation den Plugin-Timer bei Bedarf anhalten, damit die Anwendung kontrolliert erfolgt. Für eine vollständige Übernahme während eines Wartungsfensters bestehende FTP-Sitzungen beenden bzw. Zugriffe unterbrechen. Noch offene Sitzungen können bis zu ihrem Ende in die alten Dateien schreiben; diese deshalb behalten und erst nach Prüfung manuell archivieren. Keine gleichnamigen Zieldateien blind überschreiben.

Nach Installation:

```sh
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
```

Ein zuvor angehaltener virtualmin-ftps.timer muss anschließend wieder gestartet werden. Kein Live-Server wurde beim Paketbau verändert.

# 0.1.17 — Beta

- Standardablage der geschützten Originale ist /var/lib/virtualmin-ftps-logs/DOMAIN-ID, aus state_dir abgeleitet. /var/log bleibt unverändert; auch der frühere automatische log_root-Wert /var/log/virtualmin-ftps wird gezielt auf den neuen Standard abgebildet.
- Schreibgeschützte Bind-Ansicht unter Domain-Home/logs/ftps, direkt im FTP-Chroot lesbar. Root-eigene Originale bleiben gegen Löschen und Überschreiben geschützt.
- Native Einträge FTP-Log und FTP-Transfer-Log unter Logs and Reports. Reine Leseansicht mit begrenzter Ausgabe und Domain-/Modul-ACL-Prüfung.
- Der vollständige angewendete Abgleich aktualisiert ausschließlich die Log-Modulberechtigungen der Domain-Hauptkonten und den Menücache.
- AllowOverride on und AllowOverwrite on bleiben enthalten.

# 0.1.16 — Beta

- Aktive FTP-Logs liegen in /var/log/virtualmin-ftps/DOMAIN-ID/ und gehören root:Domain-Gruppe mit 0640. Domain-Verzeichnisse gehören root:Domain-Gruppe mit 0750, die gemeinsame Wurzel root:root mit 0711.
- Alle Vorfahren des Logbereichs müssen root gehören und dürfen für Gruppe/Andere nicht beschreibbar sein. Dadurch kann der Domain-Benutzer aktive Logs weder löschen, umbenennen noch überschreiben; er kann eigene Logs über seine Gruppe lesen.
- Bestehende Home-Logs werden beim ersten Umstellen als größenbegrenzter Schnappschuss kopiert. Quellen bleiben unverändert. Vorhandene Zielinhalte werden weder geleert noch mehrfach angehängt.
- Zustandsbasierte Übernahme der alten Logpfade; fremde Konfigurationsänderungen bleiben gesperrt. Fehlende geschützte Dateien werden auch bei ansonsten unverändertem angewendetem Abgleich angelegt.
- AllowOverride on und AllowOverwrite on bleiben für Kundendateien erhalten.
- Details: DOMAIN-LOGS.md und OWNERSHIP-UPDATE.md.

# 0.1.15 — Beta

- Gezielte Übernahme regulärer root:root-Altlogs zusätzlich zu root:Domain-Gruppe nach Domain-Benutzer:Domain-Gruppe. Bestehende Inhalte und Dateirechte bleiben erhalten. Root-eigene logs-Verzeichnisse mit root- oder Domain-Gruppe werden ebenfalls übertragen.
- Fremde Benutzer oder nicht passende sonstige Gruppen, Symlinks, Hardlinks und weltweit beschreibbare Dateien bleiben gesperrt.
- Die Vorschau prüft jetzt vorhandene Logpfade und Eigentümer lesend; sie erzeugt keine Dateien und ändert keine Besitzer.
- AllowOverride on und AllowOverwrite on bleiben erhalten.

# 0.1.14 — Beta

- Logs gehören dem von Virtualmin gemeldeten Domain-Benutzer und seiner Domain-Gruppe. Vorhandene passende Logs behalten Eigentümer, Gruppe, Rechte und Inhalt; neue Dateien erhalten diese Identität und 0640.
- Reguläre root-eigene Logs mit bereits passender Domain-Gruppe aus früheren Versionen werden beim Anwenden ohne Leeren auf den Domain-Benutzer übertragen. Bestehende root-eigene Logverzeichnisse mit passender Gruppe werden ebenfalls übertragen. Andere Eigentümer-/Gruppenabweichungen bleiben gesperrt.
- Gruppen-Schreibrechte sind bei passender Domain-Gruppe erlaubt. Weltweit beschreibbare Dateien, Symlinks, Hardlinks und ungeeignete Dateitypen bleiben gesperrt. Fehlermeldungen nennen den konkreten Pfad und die Eigentümer-/Rechtewerte.
- Jeder verwaltete Host erhält AllowOverride on und weiterhin AllowOverwrite on. AllowOverride erlaubt .ftpaccess-Dateien; AllowOverwrite erlaubt das Überschreiben innerhalb der bestehenden Unix-Rechte.
- Bekannte alte Zustände mit AllowOverride off werden kontrolliert übernommen. Kein manuelles Bearbeiten der verwalteten Datei nötig.
- Details: DOMAIN-LOGS.md und OWNERSHIP-UPDATE.md.

# 0.1.13 — Beta

- Fehler korrigiert: Home-Pfad wird aus Virtualmins home-Feld statt aus dem dir-Aktivierungsmerkmal übernommen.
- Fehlender Home-Wert wird bereits in der Perl-Übergabe abgefangen. Die bestehende Pfadprüfung bleibt unverändert.
- Drei neue Prüfungen der echten Descriptor-Funktion einschließlich Übergabe an Python.
- Migration der Server-Begrüßung, Domain-Logs und AllowOverwrite bleiben enthalten. Anleitung: HOME-MAPPING.md.

# 0.1.12 — Beta

- Korrektur der ausdrücklichen Migration: bereits auf den validierten lokalen Server-FQDN geänderte ServerIdent-Zeilen werden auch bei altem Zustand ohne server_fqdn übernommen.
- Ausschließlich bytegenau bekannte Konfigurationsvarianten werden akzeptiert; weitere Änderungen und fremde Begrüßungsnamen bleiben gesperrt.
- Erfolgreicher Abgleich übernimmt auch Domain-Logs und AllowOverwrite aus 0.1.10/0.1.11.
- Anleitung: GREETING-MIGRATION.md. Keine Live-Serveränderung beim Paketbau.

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

## Eigene Einstellungen je virtuellem FTP-Host

Unter domains lassen sich anhand der stabilen Virtualmin-Domain-ID eigene Werte festlegen. Die Regeln gelten jeweils für ftp.log und xferlog dieses Hosts. Nicht angegebene Werte werden vom gemeinsamen Standard geerbt; maxsize: null schaltet eine geerbte Größenrotation aus.

```json
"logrotate": {
  "interval": "weekly",
  "rotate": 52,
  "maxsize": null,
  "domains": {
    "1792423871587556": {
      "interval": "daily",
      "rotate": 365
    },
    "17921619452822993": {
      "interval": "monthly",
      "rotate": 12
    }
  }
}
```

Damit erhält web4test.beck-mann.de im Beispiel tägliche und artists.de monatliche Archive. Die IDs vor Verwendung mit der eigenen Virtualmin-Konfiguration abgleichen. Andere Hosts – auch neue – verwenden automatisch den gemeinsamen Standard. Nach Änderungen check-logrotate und install-logrotate ausführen. Eigene Regeln stehen vor der Standardregel und verhindern doppelte Rotation über ignoreduplicates (Logrotate ab 3.21, enthalten in Debian 12).
