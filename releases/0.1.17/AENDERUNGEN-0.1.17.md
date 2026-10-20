# 0.1.17 — Beta

- Standardablage der geschützten Originale ist /var/lib/virtualmin-ftps-logs/DOMAIN-ID, aus state_dir abgeleitet. /var/log bleibt unverändert; auch der frühere automatische log_root-Wert /var/log/virtualmin-ftps wird gezielt auf den neuen Standard abgebildet.
- Schreibgeschützte Bind-Ansicht unter Domain-Home/logs/ftps, direkt im FTP-Chroot lesbar. Root-eigene Originale bleiben gegen Löschen und Überschreiben geschützt.
- Native Einträge FTP-Log und FTP-Transfer-Log unter Logs and Reports. Reine Leseansicht mit begrenzter Ausgabe und Domain-/Modul-ACL-Prüfung.
- Der vollständige angewendete Abgleich aktualisiert ausschließlich die Log-Modulberechtigungen der Domain-Hauptkonten und den Menücache.
- AllowOverride on und AllowOverwrite on bleiben enthalten.

