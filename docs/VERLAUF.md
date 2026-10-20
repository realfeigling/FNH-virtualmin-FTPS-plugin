# Arbeitsverlauf: Virtualmin FTPS

Stand: 20. Oktober 2026.

## Vorgeschichte und Quellenlage

Ausgangspunkt ist der Chat „Virtualmin FTP Server fehlt“. Der zugängliche Ausschnitt dokumentiert unterschiedliche FTP-Begrüßungen bei mehreren VirtualHosts auf derselben IP. Gewünscht wurde der Serverhostname als ServerIdent statt des jeweiligen Domainnamens; nach einer Vorschau wurde die Änderung freigegeben. Anschließend sollte das Paket als Beta statt Experimental geführt werden.

Diese Datei ist eine zusammengefasste Projektdokumentation, kein vollständiger Chat-Export. Ältere Assistentenantworten waren teilweise nur als Inhaltsreferenzen verfügbar. Grundlage der Bearbeitung war das unveränderte angehängte Installationspaket virtualmin-ftps-0.1.8.wbm.gz; dessen SHA-256-Manifest wurde geprüft.

## Auftrag und Umsetzung

1. Plugin in allen aktuellen Metadaten, Oberflächen- und Dokumentationstexten als Beta kennzeichnen.
2. Die freigegebene ServerIdent-Änderung berücksichtigen: validierter, zur Laufzeit ermittelter Server-FQDN.
3. Neues installierbares Webmin-Paket erstellen und prüfen; keine Live-Serverkonfiguration ändern.
4. Anschließend Verlauf und Installationspaket im Repository realfeigling/FNH-virtualmin-FTPS-plugin bereitstellen.

Das Ausgangspaket enthielt noch Experimental-Kennzeichnungen und domainbezogenes ServerIdent. Version 0.1.9 Beta korrigiert Modulbeschreibung, Prüfseiten-Titel, README und Einschränkungen. Die Generierung verwendet hostname --fqdn, normalisiert gültige ASCII-/Punycode-Namen und lehnt kurze Namen, IP-Adressen, ungültige Labels und Steuerzeichen ab. Fehler brechen vor Anwendung ab.

ServerName, ServerAlias und Zertifikatsauswahl bleiben domainbezogen. Der bisherige Server-FQDN wird im Zustand gespeichert, damit Driftprüfungen auch nach Hostnamenänderungen die tatsächlich zuvor erzeugte Konfiguration vergleichen. Exakt bekannte alte Domain-Begrüßungen können übernommen werden; fremde Änderungen werden weiterhin abgewiesen.

## Prüfung und Ergebnis

10 lokale Testmethoden bestanden, einschließlich negativer FQDN-Unterfälle, mehrerer VirtualHosts, Altzustand, Hostnamenwechsel, Migration, Driftabwehr, Rücknahme und Wiederherstellung nach simuliertem Reload-Fehler. Python-Syntaxprüfungen und vier Perl-Syntaxprüfungen bestanden. Die unveränderte Modulbibliothek konnte wegen fehlendem WebminCore.pm nicht vollständig geprüft werden. Die historischen Testsuiten waren im Ausgangspaket nicht enthalten und wurden nicht erneut ausgeführt.

Originalmanifest, neues vollständiges Manifest, gzip-/Tar-Lesbarkeit, native Archivwurzel virtualmin-ftps/module.info, Version, Beta-Kennzeichnung und Skript-Ausführbarkeit wurden geprüft. Es erfolgten kein echter ProFTPD-/Webmin-Integrationstest, kein echter FTPS-Login und keine Live-Serveränderung.

## Installation und spätere Anwendung

Das Paket unter releases/0.1.9 wird über Webmin installiert. Ein bereits aktiver Abgleich-Timer kann danach die neue Begrüßung anwenden. Hinweise zu Vorschau, Anwendung, Syntaxprüfung und Rücknahme stehen in virtualmin-ftps/docs/SERVER-IDENT.md. Die Beta-Kennzeichnung ist keine nachträgliche Live-Abnahme.

## Ergänzung: Domain-Logs, 0.1.10 Beta

Auf Wunsch werden ExtendedLog und TransferLog je VirtualHost unter dem jeweiligen Domain-Home angelegt und dauerhaft gespeichert. Der Beispielpfad wird nicht fest übernommen. Sichere Dateianlage, Migration und Erhalt vorhandener Logs sind umgesetzt; 16 Regressionstests auf GitHub Actions bestanden. Keine Live-Serveränderung.

## Ergänzung: Überschreiben, 0.1.11 Beta

Gemeldet wurde 550 index.html: Overwrite permission denied. Dem Plugin fehlte AllowOverwrite on. Diese Regel wird für jeden verwalteten Host ergänzt, mit kontrollierter Migration vorhandener Zustände und Erhalt von Datei-/Benutzerrechten und Domain-Logs. Keine Live-Serveränderung oder Überschreiben einer Live-Datei.

## Korrektur der Update-Übernahme, 0.1.12 Beta

Die Nutzerausgabe zeigte: gespeicherter Server-FQDN fehlt, aktive Datei enthält bereits den Server-FQDN; ausschließlich ServerIdent-Zeilen weichen ab. Die bisherige Migration lehnte diese Konstellation ab. Die ausdrückliche Migration akzeptiert jetzt diese exakt bekannte Variante mit aktuell validiertem lokalen FQDN. Andere Änderungen bleiben gesperrt. Kein direktes Ändern von Live-Zustand oder Live-Konfiguration beim Paketbau.

## Korrektur der Virtualmin-Feldzuordnung, 0.1.13 Beta

Die Nutzerausgabe zeigte dir=1 bei allen Domains. Die Plugin-Zuordnung von dir zum Home-Pfad war falsch. Sie verwendet jetzt home; der dir-Wert bleibt Aktivierungsmerkmal. Drei neue Tests prüfen die echte Perl-Descriptor-Funktion und ihre Übergabe an Python. Keine Änderung an Live-Domainfeldern oder Home-Verzeichnissen beim Paketbau.

## Log-Eigentümer und Kundenregeln, 0.1.14 Beta

Der Nutzer stellte klar, dass Logs den Domain-Benutzern und ihren Gruppen gehören. Die bisherige root-Anforderung war falsch. Das Plugin übernimmt jetzt user und group aus Virtualmin, akzeptiert passende vorhandene Logs unverändert und legt neue Logs entsprechend an. Root-eigene Altlogs mit passender Gruppe werden ohne Leeren übertragen. Außerdem wurde auf ausdrücklichen Wunsch AllowOverride on gesetzt; AllowOverwrite on bleibt aktiv. Neue Regressionstests bilden die gemeldeten Werte UID 1015/GID 1018/0644 ab. Keine Live-Serveränderung beim Paketbau.

## Root:root-Altlogs und Vorschauprüfung, 0.1.15 Beta

Die Anwendung traf auf eine reguläre Logdatei mit UID 0, GID 0 und 0644. Die bisherige Übernahme akzeptierte nur root mit passender Domain-Gruppe. Diese Lücke ist geschlossen: root:root wird ohne Leeren und Rechteänderung auf Domain-Benutzer:Domain-Gruppe übertragen. Die Vorschau prüft vorhandene Logs nun lesend. Keine Live-Serveränderung beim Paketbau.

## Root-Logs mit Löschschutz, 0.1.16 Beta

Der Nutzer änderte die Anforderung: FTP-Logs sollen root gehören, damit der Kunde sie nicht löschen kann. Root-Eigentum allein im kundenbeschreibbaren Home wäre unzureichend. Die aktive Protokollierung verwendet deshalb einen root-kontrollierten Verzeichnisbaum unter /var/log/virtualmin-ftps/DOMAIN-ID mit Domain-Gruppenleserechten. Vorhandene Home-Logs werden als Schnappschuss übernommen und nicht gelöscht. Ein Testprozess mit Domain-UID/GID prüft, dass Lesen gelingt und Löschen, Umbenennen sowie Schreiben abgewiesen werden. Kein Live-Serverzugriff beim Paketbau.

## Kunden-Logs und Logs and Reports, 0.1.17 Beta

Die /var/log-Elternprüfung scheiterte auf dem Zielserver. Gewünscht wurden unveränderte /var/log-Rechte, geschützte Logs mit Zugang unter Kunden-Logs und native Menüeinträge. Auf Rückfrage wurde direkter FTP-Zugriff innerhalb des Chroots ausdrücklich gewünscht. Die neue Ablage verwendet einen root-kontrollierten Bereich neben state_dir, eine schreibgeschützte Bind-Ansicht unter logs/ftps und domainbegrenzte Webmin-Leseansichten. Keine Live-Serveränderung beim Paketbau.

## 0.1.18 Beta – Logablage unter /var/log

Auf Nutzerwunsch auf /var/log/virtualmin-ftps-logs umgestellt. Root-Eigentum, lesbare schreibgeschützte FTP-Ansicht und Logs and Reports erhalten. Alte Originaldateien nicht gelöscht oder verschoben. Keine Live-Konfiguration geändert.

## 0.1.19 Beta – Systemverweis für /var/log

Die Diagnose auf web4 zeigt /var/log -> /data/log; beide Eltern und das Ziel gehören root mit 0755. Die bisherige Ablehnung aller Verweise war die Ursache. Ausschließlich der geprüfte Systemverweis wird nun für Logs unterstützt, einschließlich FTP-Einhängung und historischer Übernahme.

## 0.1.20 Beta – Logrotation

Auf Nutzerwunsch geprüfte Logrotate-Konfiguration für geschützte FTP-Logs ergänzt. Einrichtung über manage.py install-logrotate; tägliche Rotation mit 14 Archiven und Erhalt laufender FTP-Dateideskriptoren. Kein Live-Serverzugriff.

## 0.1.21 Beta – Konfigurierbare Rotation

Auf Nutzerwunsch Intervall, Archivanzahl und optionale Größenrotation als logrotate-Abschnitt in engine.json ergänzt. Neuer Standard weekly/52 ohne maxsize. Änderungen werden über geprüften install-logrotate-Aufruf übernommen; vorhandene Konfigurationen beim Paket-Update bleiben erhalten.

Ergänzende Nutzeranforderung: individuelle Rotation je virtuellem FTP-Host über Domain-ID-Overrides in logrotate.domains; neue Hosts erben Standardwerte. Echte Tests prüfen getrennte Aufbewahrung ohne doppelte Rotation.

## 0.1.22 Beta – Webmin-Einstellung und Kodierung

Auf Nutzerwunsch native Webmin-Formulare für globale und hostbezogene Logrotation ergänzt. Screenshot zeigte FTPS pr�fen; Menüausgabe auf korrekte UTF-8-Bytes korrigiert. Hauptadministrator-ACL, POST mit sitzungsgebundenem Token, Schutz vor parallelem Überschreiben, geprüfte Regel und Wiederherstellung bei Schreibfehlern. Kein Zugriff auf den Live-Server.

## 0.1.23 Beta – POST-Prüfung

Nutzer meldet POST-Fehler im Webmin-Formular. Ursprüngliche HTTP-Methode vor Modulinitialisierung sichern; Regressionstests simulieren bereinigte Umgebung und prüfen sowohl Erfolg als auch weiterhin gesperrte Schreibzugriffe. Nach Fehlern Einstellungsformular erneut anbieten.

## 0.1.24 Beta – Ursache im AJAX-Formularablauf

POST-Meldung besteht trotz gesicherter Methode weiter. Nutzer bestätigt unveränderte Browseradresse. Authentic-Quellcode get_pjax_type wählt bei stringförmiger Zieladresse die Methode des ersten passenden sichtbaren Formulars. Hostauswahl-GET und Speicher-POST hatten dasselbe Ziel. Umstellung auf genau ein POST-Formular, getrenntes Bearbeitungsziel und explizite reine Auswahlaktion. Neue HTML-/Transporttests.

## 0.1.25 Beta – Domain-Kontext erhalten

Nutzer wünscht aus „FTPS prüfen“ direkt nur die Logrotation dieser Domain. Link übergibt Domain-ID, Einstellungsseite blendet globale Auswahl im Domain-Kontext aus. Bestehende Domain-Regel mit 53 gegenüber 52 Standardarchiven bestätigt; keine Werte automatisch verändert.
