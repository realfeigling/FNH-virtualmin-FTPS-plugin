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
