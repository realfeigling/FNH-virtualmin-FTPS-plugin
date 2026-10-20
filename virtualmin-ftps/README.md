# Virtualmin FTPS VirtualHosts 0.1.14 — Beta

Log-Eigentümer und Kundenregeln: [OWNERSHIP-UPDATE.md](docs/OWNERSHIP-UPDATE.md).

Korrigierte Virtualmin-Home-Übergabe: [HOME-MAPPING.md](docs/HOME-MAPPING.md).

Übernahme bereits geänderter Server-Begrüßungen: [GREETING-MIGRATION.md](docs/GREETING-MIGRATION.md).

Überschreiben vorhandener Dateien: [OVERWRITE.md](docs/OVERWRITE.md).

Domainbezogene FTP-Logs: [DOMAIN-LOGS.md](docs/DOMAIN-LOGS.md).

Eigenständiges Webmin-/Virtualmin-Feature-Plugin für **Virtualmin GPL 8.3.0**, **Debian 12** und **ProFTPD 1.3.8**. Keine Änderungen an Virtualmin-Kerndateien. Keine automatische Übernahme vorhandener FTP-VirtualHosts.

**Update mit aktiven Hosts:** Ab 0.1.8 Website-Zertifikate direkt nutzen: [WEBSITE-CERTIFICATES.md](docs/WEBSITE-CERTIFICATES.md). Der Umstellungsaufruf übernimmt auch die Login-Korrektur aus 0.1.6; nicht manuell die verwaltete Datei bearbeiten.

**Auf dem Produktivsystem vor einer Aktivierung zunächst `check` ausführen.** Die Installation startet im Prüfmodus: keine ProFTPD-Konfigurationsänderung, kein Reload und kein Renewal-Timer. Ein echter Virtualmin-/FTPS-Praxistest steht noch aus. Das Paket ist keine Freigabe für einen unbeaufsichtigten Produktionseinsatz.

## Installation über den Webmin-Uploader

Dafür die Datei **`virtualmin-ftps-0.1.14.wbm.gz`** verwenden, nicht das vollständige `.tar.gz`-Entwicklerpaket. Das native Archiv enthält direkt `virtualmin-ftps/module.info`; der Modulordner hat keine Versionsnummer im Namen.

Unter **Webmin → Webmin Configuration → Webmin Modules → Install** das `.wbm.gz` als lokale Datei auswählen. Der Upload installiert das eigenständige Modul, richtet aber noch keinen FTPS-Host und keinen Dienst ein. Danach einmalig als root den Prüfmodus vorbereiten:

```bash
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py setup
python3 /opt/webmin-2.670/virtualmin-ftps/manage.py check
```

Bei anderem aktivem Webmin-Verzeichnis den Pfad anpassen. `setup` übernimmt das bereits hochgeladene Modul und erzeugt nur seine eigene Konfiguration und seinen Zustandsordner. Es verändert keine ProFTPD-Konfiguration, führt keinen Reload aus und startet keinen Timer. Eine vorhandene Konfiguration wird nicht überschrieben. Der globale Webmin-Menüeintrag zeigt diesen Einrichtungshinweis ebenfalls an.

Anschließend das Plugin wie unten beschrieben unter Virtualmins **Features and Plugins** verfügbar machen, standardmäßig aus. Im Prüfmodus bleiben aktive Domain-Änderungen gesperrt. Für diese Upload-Variante **nicht noch einmal `manage.py install` ausführen**: Dieser Befehl ist nur für das vollständige Installationsarchiv bestimmt.

## Alternative: vollständiges Installationsarchiv, zuerst nur prüfen

Archiv beispielsweise nach `/root/virtualmin-ftps-0.1.14.tar.gz` kopieren und als root ausführen:

```bash
tar -xzf /root/virtualmin-ftps-0.1.14.tar.gz -C /root
cd /root/virtualmin-ftps-0.1.14
python3 manage.py check --webmin-root /opt/webmin-2.670
```

Dieser Befehl prüft Versions-/Quellenvoraussetzungen und liest die ProFTPD-Konfiguration einschließlich unterstützter Includes. Er zeigt fremde VirtualHosts und die TLS-Einstellungen des Hauptservers an. Er installiert nichts und testet keine echte FTPS-Verbindung. Kein `activate` ausführen, um nur zu prüfen.

Die hier bereitgestellte Version benötigt ausschließlich Python-Standardbibliothek, Perl-Core-Module, OpenSSL, systemd und das installierte ProFTPD. Kein Download von Abhängigkeiten, kein zusätzlicher Netzwerkdienst.

## Installation im Prüfmodus

Erst wenn die erste Prüfung nachvollziehbar ist:

```bash
python3 manage.py install --webmin-root /opt/webmin-2.670
```

Dabei werden nur das neue Webmin-Modul, seine Konfiguration und sein eigener Zustandsordner angelegt. Die Installation überschreibt kein vorhandenes Modul und keine vorhandenen FTPS-Zustandsdaten. Das vollständige `.tar.gz` wird mit `manage.py install` eingerichtet. Für den Webmin-Uploader stattdessen das separate `.wbm.gz` und anschließend `manage.py setup` verwenden.

In Virtualmin als Hauptadministrator **System Settings → Features and Plugins** öffnen, „FTPS VirtualHosts“ als Plugin aktivieren und **nicht standardmäßig für neue Domains einschalten**. Die globale Aktivierung ist normale Virtualmin-Konfiguration; keine Kernpatches. Browseransicht gegebenenfalls neu laden.

Die Funktion ist dann als Domain-Checkbox verfügbar. **Im Prüfmodus verweigert die Checkbox aktive Änderungen absichtlich.** Zur Planung den Domain-Menüpunkt „FTPS pruefen“ verwenden oder mit der unveränderlichen Domain-ID prüfen:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --domain DOMAIN_ID --candidate
```

`DOMAIN_ID` durch die numerische Virtualmin-ID ersetzen. Diese lesbare Einzelprüfung untersucht nur die gewählte Domain: Zertifikat, Schlüssel, Hostname, Kette und passende Konflikte. Gemeinsame Voraussetzungen werden separat angezeigt. Andere Domain-Zertifikate und die ProFTPD-Gesamtkonfiguration werden dabei ausdrücklich nicht geprüft; weder aktive Dateien noch Dienstzustand werden geändert. Für maschinenlesbare Ausgabe kann `--json` ergänzt werden. Vor tatsächlichen Änderungen bleibt der vollständige Syntaxcheck zwingend.

Die separate administrative Vollsynchronisierungsplanung aller ausdrücklich aktivierten FTPS-Domains (nicht die Domain-Prüfseite):

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl
```

## Vor dem Live-Modus auf deinem Server

Die vorgelegte Konfiguration enthält fünf Alt-VirtualHosts, `TLSEngine off` im Hauptserver und doppelte `TLSProtocol`-/`TLSRequired`-Einstellungen. **Das Paket korrigiert oder migriert diese nicht automatisch.**

1. Für eine erste Domain darf kein fremder VirtualHost auf demselben Domainnamen existieren. Die bisherige Konfiguration muss separat gesichert und eine etwaige Migration gezielt geplant werden. Bei einem Konflikt verweigert das Plugin die Einrichtung.
2. Gewünschter Betrieb ausschließlich mit VirtualHosts: Im Hauptserver `Port 0` und `DefaultServer off` setzen. `TLSEngine off` bleibt dort zulässig; es wird kein globaler FTPS-Hauptserver benötigt. Das Paket ändert diese globalen Einstellungen nicht automatisch. Vor einer solchen Umstellung die Alt-VirtualHosts auf explizites `Port 21` prüfen, damit ihre Erreichbarkeit nicht von geerbten Einstellungen abhängt. Kein Reload allein für diese Umstellung ohne abgestimmte gültige VirtualHost-Konfiguration. Doppelte/alte TLS-Einstellungen separat prüfen.
3. Auf gemeinsam genutzten IPs müssen die Clients die richtige Domain über SNI oder geeignetes `HOST` vor der TLS-Aushandlung wählen. Ein Client ohne beides kann nicht zuverlässig unterschiedliche Zertifikate derselben IP auswählen. `IgnoreSNI` und globales `UseImplicitSSL` werden abgelehnt.
4. IPv6 wird nur verwendet, wenn die Domain eine IPv6-Adresse hat und ProFTPD es nicht global deaktiviert. Im gelieferten Hauptserver steht `UseIPv6 off`.
5. Ports, NAT und Firewall müssen passen: explizites FTPS auf TCP 21, passiv 49152–65534. Das Paket ändert keine Firewall.

### Bewusste Aktivierung

Dieser Schritt verändert die ProFTPD-Konfiguration und führt einen Reload aus. Er gehört in ein kontrolliertes Wartungsfenster, erst nach Prüfung der Voraussetzungen:

```bash
python3 manage.py activate --webmin-root /opt/webmin-2.670
```

Er fügt nur einen eindeutig markierten Include-Block in `proftpd.conf` ein, erstellt die zunächst leere Datei `/etc/proftpd/virtualmin-ftps.conf`, prüft die Konfiguration, lädt ProFTPD neu und aktiviert den eigenen Renewal-Timer. Bei einem Fehler wird versucht, die Änderung zurückzunehmen. Vorherige Hauptkonfiguration: `/var/lib/virtualmin-ftps/activation-main.backup`.

Optional vor der ersten Aktivierung: `python3 manage.py set-default-host --domain web4.de.fnh.co`. Nur diese ausdrücklich ausgewählte Domain erhält anschließend `DefaultServer on`; ohne Auswahl bleibt jeder Plugin-Host auf `off`. Details, Grenzen und Testfolge: [FTPS-Standardhost](docs/DEFAULT-HOST.md).

Danach die FTPS-Checkbox **für eine geeignete Domain** einschalten. Das Plugin erzeugt eigene VirtualHosts mit `Port 21`, `DefaultServer off` (außer dem ausdrücklich gewählten Standardhost), Domain-`ServerName`, `ServerAlias` und `ServerIdent on "SERVER-FQDN"` (validierter Server-FQDN zur Laufzeit), Home-Chroot, Gruppenbeschränkung, TLS-Pflicht, TLS 1.2/1.3 und direkten Verweisen auf die Website-Zertifikate. Keine anonymen FTP-Bereiche werden erzeugt. Die Gruppenbeschränkung verwendet die Unix-Gruppe der Domain; Subserver mit gemeinsamer Gruppe bilden dadurch keine voneinander isolierten Benutzerkreise.

Ein neuer Host mit fehlendem, selbstsigniertem oder sonst nicht gültigem Zertifikat kann ausdrücklich **ausstehend** bleiben, bis die erste gültige Ausstellung vorliegt. Er hat in dieser Zeit noch keinen verwalteten aktiven VirtualHost. Der Timer versucht es erneut. Prüfberichte zeigen `pending`; die Virtualmin-Einrichtung meldet den Wartezustand. Eine angekreuzte Checkbox ist deshalb allein kein Verbindungsnachweis.

## Begrüßung und Domainauswahl

Für jeden Plugin-Host wird der Domainname als Servername und Begrüßung gesetzt. Bei erfolgreichem `HOST domainname` sendet ProFTPD die Begrüßung des ausgewählten Hosts. TLS-SNI wählt den passenden TLS-Host; es kann die bereits versandte erste Klartextbegrüßung nicht nachträglich ändern. Bei gemeinsamer IP kennt der Server beim TCP-Verbindungsaufbau den ursprünglich im Client eingegebenen DNS-Namen noch nicht. Daher kann keine Konfiguration für jeden Client die richtige allererste Begrüßung garantieren. Für einen solchen Anspruch wären getrennte IPs/Ports oder ein Client mit passender Namensauswahl nötig.

`Port 0`/`DefaultServer off` schalten den eigenständigen Hauptserver und den expliziten Catch-all ab. Sie erzwingen nicht automatisch, dass Clients ohne HOST/SNI an einer konfigurierten Shared-IP abgewiesen werden: Dort kann der erste passende VirtualHost als anfänglicher Kontext dienen. Dies ist keine nachgewiesene Sperre aller Zugriffe per IP.

## Upgrade von 0.1.1 im Prüfmodus

Das neue `.wbm.gz` über das bestehende Modul installieren. Danach einmal den alten Menücache über die nachgewiesene native Virtualmin-Funktion erneuern:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --refresh-menu
```

Anschließend die gesamte Browserseite mit Strg+F5 neu laden, die Domain auswählen und den Menüpunkt erneut öffnen. Der Menücache-Aufruf prüft keine Zertifikate, ruft keinen FTPS-Backendvorgang auf und ändert keine ProFTPD-Konfiguration. Vorhandene `engine.json` und Plugin-Zustandsdaten werden nicht durch eine neue Vorlage ersetzt. Ein erneutes `setup` ist nicht erforderlich und würde vorhandene Konfiguration erhalten. Kein `activate` für die neue Prüfseite erforderlich. Für bereits aktiv betriebene ältere Plugin-Konfigurationen ist vorher `freeze` und ein geplanter Konfigurationsabgleich nötig; die neuen Identitätsdirektiven können sonst als Abweichung erkannt werden.

## Zertifikate und Lifecycle

- `feature_setup`, `feature_modify`, `feature_delete`, `feature_disable` und `feature_enable` verwenden die nachgewiesene Feature-API. Modify umfasst Domain-/IP-/Gruppenänderungen. Delete benötigt kein noch vorhandenes Home oder Zertifikat.
- Zertifikat, Schlüssel und Chain werden über Virtualmins Website-SSL-API bestimmt. Ab 0.1.8 werden die vorhandenen Website-Dateien direkt eingebunden. Das Plugin erstellt keine neuen Zertifikate und keine Zertifikats-/Schlüsselkopien, auch nicht während der Prüfung. Die Website-Pfade müssen zuverlässig administriert werden.
- OpenSSL prüft Zertifikat/Schlüssel-Paar, Hostname, Gültigkeit und Server-Chain gegen den Debian-Vertrauensspeicher. Private PKIs benötigen dort ihre CA. Unverschlüsselte RSA-/EC-Schlüssel werden unterstützt; verschlüsselte Schlüssel nicht. Ein RSA-/EC-Wechsel erzeugt die passende ProFTPD-Direktive. Die Server-Chain wird mit `TLSCertificateChainFile` eingebunden, nicht als zusätzliche Client-CA-Liste.
- Ohne nativen allgemeinen Renewal-Callback prüft `virtualmin-ftps.timer` ungefähr 60 Sekunden **nach Ende** des vorherigen Laufs erneut. Inhalts-Hashes erkennen Änderungen trotz gleichbleibender Pfade. Keine globalen Virtualmin-Änderungsbefehle werden ersetzt.
- Nach einer tatsächlichen Lifecycle-Änderung wartet die Vollsynchronisierung mindestens 120 Sekunden: Virtualmin speichert Domain-Dateien teilweise erst nach Rückkehr des Hooks. Das verhindert, dass ein früher Timerlauf unmittelbar den alten Dateistand wieder anwendet. Es ist keine globale Transaktionsgarantie gegenüber dem Virtualmin-Kern.
- Unveränderte Konfiguration und unveränderte Zertifikatsinhalte lösen keinen erneuten Reload aus. Bei geändertem Zertifikatsinhalt wird auch bei identischen Pfaden neu geladen. Die Zertifikatsprüfung selbst wird regelmäßig wiederholt. Ein Lauf ist linear in der Anzahl aktivierter Domains; bei großen Systemen muss der Ressourcenbedarf erst gemessen werden.
- Bereits aktive Hosts werden bei ungültigem neuem Zertifikat nicht durch einen Wartezustand ersetzt. Der Synchronisationslauf schlägt sichtbar fehl und führt keinen geplanten Reload aus. Weil die Website-Dateien direkt referenziert werden, sind alte Zertifikatsinhalte nicht durch das Plugin geschützt oder wiederherstellbar. Ein anderweitiger Reload kann bereits ersetzte Dateien laden.
- Die Vollsynchronisierung ist eine gemeinsame Transaktion. Ein Fehler bei einer aktiven Domain blockiert deren gesamten Lauf; einzelne Lifecycle-Änderungen können weiterhin gezielt ausgeführt werden. Das Journald-Protokoll muss überwacht werden.

```bash
systemctl status virtualmin-ftps.timer
systemctl status virtualmin-ftps.service
journalctl -u virtualmin-ftps.service -n 50 --no-pager
```

## Rollback und vollständige Deaktivierung

**Nur weitere automatische Änderungen stoppen:**

```bash
python3 manage.py freeze
```

Dies stellt auf Prüfmodus, stoppt Timer und laufenden Service; die aktuell laufende FTPS-Konfiguration bleibt erhalten. Neue Checkbox-Änderungen werden verweigert.

**Letzte erfolgreiche Plugin-Transaktion rückgängig machen:**

```bash
python3 manage.py rollback
```

Der Timer bleibt gestoppt und das Plugin im Prüfmodus. Rücknahme betrifft die verwaltete Datei und den Plugin-Zustand mit den vorherigen Zertifikatspfaden; bereits ersetzte Website-Dateiinhalte werden nicht wiederhergestellt. Nur bei der Migration von älteren Versionen kann die vorherige Konfiguration noch auf bestehende alte Snapshots verweisen. Die Domain-Flags in Virtualmin werden nicht zurückgedreht. Nicht einfach den Timer erneut starten: Er würde den aktuellen Virtualmin-Wunschzustand wieder anwenden. Nach einem manuellen Rollback muss der Zustand bewusst abgestimmt werden.

**Alle Plugin-VirtualHosts aus ProFTPD entfernen:**

```bash
python3 manage.py deactivate
```

Der Befehl friert zuerst das Plugin ein und entfernt ausschließlich seinen exakt markierten Include-Block. Er erhält fremde Konfigurationsänderungen und Alt-VirtualHosts. Syntaxprüfung und Reload müssen erfolgreich sein; andernfalls wird versucht, den bisherigen Include wiederherzustellen. Bereits vorhandene alte Zertifikatssnapshots und Zustandsdateien bleiben für Wiederherstellung/Analyse erhalten. Die Funktion ist ausdrücklich keine vollständige Wiederherstellung aller Eigenschaften eines FTP-Servers nach Domain-Löschung oder IP-Entzug: Bereits gelöschte Unix-Konten/IPs werden nicht wieder angelegt.

Nach erfolgreicher Deaktivierung kann der Hauptadministrator das Plugin unter Features and Plugins global abschalten und das eigenständige Webmin-Modul entfernen. Das bloße Entfernen des Moduls ersetzt `deactivate` nicht. Backups mit privaten Schlüsseln bleiben ausschließlich root-zugänglich; ihre endgültige Löschung erfolgt nach deiner Aufbewahrungsentscheidung. Es gibt keine automatische Bereinigung alter Zertifikatssnapshots.

## Fehler und Wiederaufnahme

Ein Transaktionsjournal ermöglicht die Wiederherstellung nach einem unterbrochenen Dateiaustausch. Beim nächsten schreibenden Vorgang wird zuerst die alte Konfiguration geprüft, wiederhergestellt und neu geladen. Scheitert auch das, bleibt das Journal erhalten und weitere Arbeit bricht ab. Dann `freeze` ausführen und Dienst/Journal lokal prüfen. Niemals ein Journal oder einen benötigten Zertifikatssnapshot zur Fehlerbehebung blind löschen.

Nach `freeze`, `rollback` oder `deactivate` gibt es absichtlich keinen Ein-Klick-Resume. Vor einer erneuten Freigabe müssen Domain-Flags, Plugin-Zustand und aktive Konfiguration abgeglichen werden. `activate` unterstützt nur eine neue, leere Aktivierung und verweigert die Übernahme vorhandener verwalteter Dateien. Für ein bereits genutztes System ist eine Wiederaufnahme ein eigener geprüfter Wartungsschritt.

Dateisperren koordinieren Plugin-Prozesse. Die normale Perl-Anbindung verwendet zusätzlich Webmins ProFTPD-Dateisperren. `manage.py`-Wartungsschritte dürfen nicht parallel zu anderen ProFTPD-Konfigurationsarbeiten erfolgen; Texteditoren oder fremde Deployment-Werkzeuge beachten Webmins Sperren nicht.

## Grenzen und Testnachweis

Details stehen in [docs/LIMITATIONS.md](docs/LIMITATIONS.md), [docs/HOOKS.md](docs/HOOKS.md) und [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md). Automatisierte Tests (im vollständigen Entwicklerpaket):

```bash
python3 -m unittest discover -s tests -v
perl tests/test_hooks.pl
perl tests/test_menu.pl
```

Die Tests erzeugen ausschließlich temporäre Testschlüssel und Testzertifikate. OpenSSL arbeitet dabei echt. ProFTPD, systemd und die Webmin-Laufzeit sind simuliert. Der separate Quellvertragstest prüft die bereitgestellten Virtualmin-Dateien, wenn sie neben diesem Quellordner vorliegen; Nutzerquellen sind nicht im Installationspaket enthalten.

Das Plugin bleibt als eigenständiges Modul außerhalb der Virtualmin-Kerndateien. Das macht es kernpatchfrei, aber garantiert keine Kompatibilität mit zukünftigen Updates. Andere Virtualmin-Versionen werden bewusst abgelehnt, bis die Hooks erneut geprüft sind.

Lizenz: MIT; siehe `LICENSE`. Das Paket enthält eigenen Code, keine Virtualmin-/Webmin-Quellen und keine Daten deines Servers.
