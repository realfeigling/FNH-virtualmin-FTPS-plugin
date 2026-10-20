# 0.1.24 — Beta

## Formularübermittlung mit Authentic Theme korrigiert

Das Authentic Theme kann bei AJAX-Aufrufen die HTTP-Methode aus dem ersten sichtbaren Formular mit passender Zieladresse bestimmen. Bisher hatten Host-Auswahl (GET) und Einstellungen (POST) beide rotation.cgi als Ziel. Dadurch konnte die Speicherung trotz POST-Speicherformular als GET übertragen werden. Die Sicherung der ursprünglichen HTTP-Methode in 0.1.23 allein behebt diesen Fall nicht.

Die Seite verwendet jetzt genau ein POST-Formular für Auswahl, Prüfung und Speichern. „Anzeigen“ wechselt ausschließlich die Ansicht und hat Vorrang vor Speicheraktionen. Das angezeigte Bearbeitungsziel wird separat gespeichert: Die Auswahl eines anderen Hosts im Dropdown allein leitet eine Speicherung nicht auf diesen Host um.

POST-Pflicht, Administratorprüfung, Sitzungstoken, paralleler Änderungsschutz und Rücknahme bei Schreibfehlern bleiben unverändert. Kein Akzeptieren von GET-Schreibzugriffen als Umgehung.

Nach Modul-Update die FTP-Logrotation über den Menüeintrag frisch öffnen; eine bereits offene Fehlerseite schließen. Anschließend „Nur prüfen“ und „Speichern und anwenden“ verwenden. Bestehende Konfigurationen und Logs bleiben erhalten. Keine Live-Serveränderung beim Paketbau.

Zusätzliche Tests parsen die tatsächlich erzeugte HTML-Struktur, prüfen genau ein POST-Formular mit allen Bedienelementen, simulieren die Methodenwahl des Themes anhand des ersten passenden Formulars und prüfen Hostwechsel ohne Schreiben sowie Speichern für das angezeigte Ziel.

Referenz: get_pjax_type in https://github.com/webmin/authentic-theme/blob/master/unauthenticated/js/bundle.min.js
