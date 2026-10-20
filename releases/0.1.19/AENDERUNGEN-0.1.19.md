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
