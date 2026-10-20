# Virtualmin-Home korrekt übernehmen — 0.1.13 Beta

Virtualmins Feld `dir` zeigt an, ob die Verzeichnisfunktion aktiviert ist (typischer Wert: 1). Der tatsächliche absolute Domain-Home-Pfad steht in `home`.

Die Versionen 0.1.10 bis 0.1.12 übergaben versehentlich `dir` als Home-Pfad an den Backend-Prozess. Dadurch scheiterte die Vorschau an der Meldung "Domain home must be a canonical absolute ASCII path". 0.1.13 korrigiert die Zuordnung auf `home`. Sowohl die aktivierte Verzeichnisfunktion als auch ein vorhandener Home-Wert sind Voraussetzungen. Es werden keine Virtualmin-Domainfelder oder Home-Verzeichnisrechte verändert.

Drei zusätzliche Tests führen die tatsächlich aus dem Plugin extrahierte Perl-Funktion ftps_descriptor mit simulierten Virtualmin-SSL-Aufrufen aus. Geprüft sind dir=1 mit realem Home (einschließlich Subserver-Pfad), fehlendes home und deaktivierte Verzeichnisfunktion. Das Ergebnis wird auch durch den echten Python-Normalisierer und die Logpfad-Erzeugung geprüft.

## Anwendung

0.1.13 Beta über Webmin installieren. Danach zunächst:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates
```

Ist die Vorschau erfolgreich, anwenden:

```bash
perl /opt/webmin-2.670/virtualmin-ftps/collect.pl --use-website-certificates --apply
proftpd -t -c /etc/proftpd/proftpd.conf
systemctl is-active proftpd
```

Den Modulpfad gegebenenfalls anpassen. Die Migration der bereits gesetzten Server-Begrüßung aus 0.1.12 bleibt enthalten. Domain-Logs und AllowOverwrite werden beim erfolgreichen angewendeten Abgleich übernommen. Die Vorschau schreibt keine Konfiguration, keinen Zustand und keine Logdateien. Ein aktiver Timer kann nach dem Update automatisch abgleichen.

Beim Paketbau wurden keine Live-Serveränderungen vorgenommen.

Quellen zur Feldbedeutung: [Virtualmin install-script.pl](https://github.com/virtualmin/virtualmin-gpl/blob/master/install-script.pl) und [security-lib.pl](https://github.com/virtualmin/virtualmin-gpl/blob/master/security-lib.pl).
