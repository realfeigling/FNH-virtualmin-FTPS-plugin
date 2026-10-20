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
