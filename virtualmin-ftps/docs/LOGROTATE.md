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
