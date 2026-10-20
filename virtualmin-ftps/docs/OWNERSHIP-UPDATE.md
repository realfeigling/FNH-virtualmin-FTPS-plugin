# FTP-Logs, Kundenansicht und Logs and Reports — 0.1.18 Beta

Die geschützten Originale liegen standardmäßig unter /var/log/virtualmin-ftps-logs/DOMAIN-ID. Die bisherigen automatischen Ablagen neben state_dir sowie /var/log/virtualmin-ftps werden auf diesen Standard abgebildet. Individuelle andere log_root-Werte bleiben erhalten und müssen einen root-kontrollierten Elternpfad besitzen. /var/log und dessen Rechte werden nicht geändert.

Originaldateien gehören root:Domain-Gruppe mit 0640; Domain-Verzeichnisse gehören root:Domain-Gruppe mit 0750. Kunden dürfen die Originale lesen, aber weder löschen noch überschreiben. Frühere Quellen werden wie in 0.1.16 als größenbegrenzter Schnappschuss übernommen, nicht gelöscht und nicht geleert. Alte FTP-Sitzungen können noch in alte bereits geöffnete Dateien schreiben; neue Verbindungen verwenden nach erfolgreicher Anwendung die neue Konfiguration.

## Direkter FTP-Zugriff unter Kunden-Logs

Unter Domain-Home/logs/ftps wird der geschützte Domain-Logbereich als Bind-Mount mit ro,nosuid,nodev,noexec eingehängt. Dort liegen ftp.log und xferlog. Die Ansicht liegt innerhalb des FTP-Chroots und ist direkt lesbar. Sie enthält keine beschreibbaren Kopien und keinen absoluten Symlink, der im Chroot ins Leere zeigen würde. Vorhandene Home/logs/ftp.log und xferlog bleiben als frühere Quellen erhalten.

Der neue Mountpoint ftps muss fehlen oder ein leeres root-eigenes Verzeichnis sein. Fremde Mounts, Symlinks oder nicht leere Kundenverzeichnisse werden nicht ersetzt. Fehlende logs-Verzeichnisse werden für den Domain-Benutzer angelegt. Die neue Ansicht benötigt Linux x86_64 oder aarch64 mit open_tree/mount_setattr/move_mount (Linux 5.12+) und Mount-Berechtigungen des root-Prozesses. Unzureichende Containerrechte führen zum Abbruch vor Übernahme der neuen ProFTPD-Konfiguration. Die Einhängung verwendet gepinnte Verzeichnisdeskriptoren; Verzeichniswechsel durch Kunden dürfen den Mount nicht an fremde Pfade umleiten.

Der vorhandene aktive Plugin-Timer stellt die Ansicht beim nächsten erfolgreichen angewendeten Abgleich nach einem Neustart wieder her. Es werden keine /etc/fstab-Einträge angelegt. Bis dahin kann die Ansicht leer sein; die Originale bleiben geschützt und die Webmin-Anzeige liest sie direkt. Wird der Timer nicht verwendet, muss der Abgleich nach Neustarts ausdrücklich ausgeführt werden. Beim Entfernen eines Hosts wird seine bekannte Einhängung gelöst, ohne die Originale zu löschen. Rücknahmen lösen neu eingeführte Ansichten wieder. Kunden können beschreibbare übergeordnete Home-Verzeichnisse ggf. umbenennen und damit ihren Zugang verbergen; die geschützten Originale werden dadurch nicht gelöscht. Keine Logrotation oder Aufbewahrungsbereinigung wird neu eingerichtet.

## Logs and Reports

Das Plugin liefert die Links FTP-Log und FTP-Transfer-Log in der nativen Kategorie logs. Die CGI bietet ausschließlich Anzeige: maximal die letzten 200 Zeilen bzw. 64 KiB, HTML-escaped, keine Funktion zum Bearbeiten, Leeren oder Löschen. Vor dem Backend-Aufruf werden aktuelle Virtualmin-Domainberechtigung und Modul-ACL mit konkreten Domain-IDs geprüft. Domainfremde oder manipulierte Logselektoren werden abgewiesen.

feature_webmin meldet die begrenzten Leserechte an Virtualmin. Für bestehende Hauptkonten aktualisiert ein vollständiger angewendeter Abgleich zusätzlich genau den Zugriff auf das FTPS-Modul und dessen Domain-Liste; die Berechtigungen anderer Module bleiben unverändert. Extra-Administratoren erhalten keine pauschale Erweiterung und benötigen die passende native Modulfreigabe. Nach der Aktualisierung neu anmelden oder die Oberfläche vollständig neu laden. Root behält den administrativen Prüfbericht; Domain-Kunden sehen die reinen Logansichten.

## Anwendung

Modul 0.1.18 Beta über Webmin installieren. Zuerst Vorschau:

~~~bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
~~~

Nach erfolgreicher Vorschau anwenden:

~~~bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply &&
proftpd -t -c /etc/proftpd/proftpd.conf &&
systemctl is-active proftpd
~~~

Den Modulpfad anpassen, falls Webmin an anderer Stelle aktiv ist. Ein aktiver Timer kann nach Installation automatisch abgleichen. Danach neue FTP-Verbindungen verwenden. Fehlende Quellen werden als neue leere Originaldateien angelegt; vorhandene Zielinhalte werden nicht überschrieben. Bei Fehlern können fertige neue Originale und leere Mountpoint-Verzeichnisse bestehen bleiben. Kein direktes Ändern von /var/log-Rechten ist nötig.

Beim Paketbau wurde keine Live-Serverkonfiguration geändert und kein Mount auf dem Zielserver eingerichtet.

Quelle für Menü-/ACL-Schnittstellen: https://www.virtualmin.com/docs/development/creating-plugins/
