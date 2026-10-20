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
