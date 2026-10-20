# Hook-Prüfung am Nutzerarchiv

Quelle: `virtualmin-ftps-quellen.tar.gz`, SHA-256 `a240a19b00786a0b769621f24fb15673bd5544e47323ccb353b136beea8b2017`.
Basis im Archiv: `opt/webmin-2.670/virtual-server/`. `module.info` enthält `version=8.3.0.gpl`. Hashes einzelner geprüfter Dateien: `SOURCE-HASHES.txt`.

| Funktion | Tatsächlicher Quellennachweis |
|---|---|
| Eigenständiges Feature-Plugin laden | `virtual-server-lib-funcs.pl:21928`, `load_plugin_libraries` lädt `virtual_feature.pl`; `:22739`, `list_feature_plugins` berücksichtigt `feature_setup`. |
| Globale Registrierung | `edit_newfeatures.cgi:78` sucht Module mit `virtual_feature.pl`; `set-global-feature.pl:73` ff. unterstützt Plugin-Namen. |
| Domain-Checkbox | `edit_domain.cgi:414` ruft `feature_label(1)`; `:427` erzeugt `ui_checkbox($f, ...)`. `feature_suitable` wird vorher mit Parent-, Alias- und Subdomain-Objekt geprüft. |
| Create | `virtual-server-lib-funcs.pl:9432`: `plugin_call($f, "feature_setup", $dom, @args)`. Exceptions setzen das Feature bei der Anlage zurück. |
| Modify | `virtual-server-lib-funcs.pl:15599` und `:15619`: `feature_modify($d, $oldd)`. |
| Delete | `virtual-server-lib-funcs.pl:9742`: `feature_delete($dom, @args)`, ferner `:15593` beim Entfernen des Features. |
| IP-Wechsel | `save_newips.cgi:102` und `dynip-lib.pl:292`: `feature_modify($d, $oldd)`. |
| Temporär deaktivieren/aktivieren | `virtual-server-lib-funcs.pl:9817` / `:9874`: `feature_disable($d)` / `feature_enable($d)`. `:9828` speichert deaktivierte Namen mit `join(",", @disabled)`. |
| Menü | `virtual-server-lib-funcs.pl:14360` / `:14369`: `feature_links($d)` / `feature_always_links($d)`; Webmin-Modulverfügbarkeit wird berücksichtigt. |
| Zertifikatsdateien | `virtual-server-lib-funcs.pl:21274` ff., `get_website_ssl_file($d, "cert" / "key" / "ca")`. Keine Abhängigkeit vom entfernten FTP-Core-Feature. |
| ProFTPD-Sperren | `opt/webmin-2.670/proftpd/proftpd-lib.pl:519` und `:527`: `lock_proftpd_files` / `unlock_proftpd_files`. |

`try_plugin_call` in `virtual-server-lib-funcs.pl:11324` behandelt Exceptions getrennt vom gewöhnlichen Rückgabewert. Backendfehler werden deshalb als Perl-Ausnahmen weitergegeben; `return 0` wird nicht als zuverlässige Transaktionsmeldung missbraucht. Das Plugin kann die umgebende Virtualmin-Operation selbst nicht vollständig transaktional machen; deren weitere Fehlerbehandlung bleibt beim Kern.

## Renewal: kein erfundener Callback

`feature-ssl.pl:3545`, `renew_letsencrypt_cert`, installiert und speichert Zertifikate, aktualisiert bekannte Services und ruft die globale Änderungsbefehls-Schnittstelle auf. `install_letsencrypt_cert` beginnt bei `:3640`. Hier ist kein allgemeiner Callback für beliebige FTPS-Feature-Plugins nachgewiesen. Die API-Skizze `virtual_feature_api.pl` dokumentiert ebenfalls keinen solchen Hook. `feature_provides_ssl` beschreibt einen Website-SSL-Provider und wird deshalb nicht zweckentfremdet.

Stattdessen liest ein eigener systemd-Timer die aktivierten Domain-Objekte und ruft denselben transaktionalen Backendpfad auf. Damit werden auch Zertifikatwechsel außerhalb des ACME-Ablaufs erkannt. Vorhandene globale Vor-/Nachbefehle werden nicht überschrieben. Der Timer ist ein Polling-Lifecycle mit dokumentierter Verzögerung, kein nativer Renewal-Hook.

## Weitere Primärquellen

- [ProFTPD 1.3.8 mod_core](https://github.com/proftpd/proftpd/blob/v1.3.8/doc/modules/mod_core.html): VirtualHost, ServerAlias, AllowGroup, Limit, Include.
- [ProFTPD 1.3.8 mod_tls](https://github.com/proftpd/proftpd/blob/v1.3.8/doc/contrib/mod_tls.html): Zertifikatsdirektiven, TLSCertificateChainFile und IgnoreSNI. Die Server-Chain ist von der CA-Liste zur Prüfung von Client-Zertifikaten zu unterscheiden.

Die Paketinstallation prüft Version und charakteristische Aufrufstellen erneut. Das ist eine Kompatibilitätsbarriere, kein Beweis für sämtliche Laufzeitpfade. Nach Updates müssen Quellprüfung und Integrationstests wiederholt werden.

## Korrektur der Menüübergabe in 0.1.3

`get_all_domain_links` in `virtual-server-lib-funcs.pl:14907` ff. baut Modul-URLs aus `mod` und **`page`**. Ein Feld `link` ist hier nicht die Eingabe für die Ziel-URL. Das Plugin liefert daher `mod => virtualmin-ftps` und `page => index.cgi?dom=DOMAIN_ID`. Der zuvor verwendete Schlüssel `link` führte zum Modulverzeichnis ohne Domain-ID.

`tests/test_menu.pl` extrahiert die tatsächliche geprüfte Funktion aus dem Nutzerarchiv und testet damit URL-Erzeugung, Übergabe zweier unterschiedlicher Domain-IDs, den lesbaren Inspektionspfad und Ablehnung fremder Rückgabe-IDs. Die umgebenden Webmin-Dienste sind Test-Doubles. Das unterscheidet diesen Regressionstest vom bloßen Vergleich eines selbst erzeugten Link-Hashes.

Virtualmin speichert Feature-Links in `get_links_cache` / `save_links_cache`; `clear_links_cache` ist ab Zeile 15438 definiert. Ein Modulversionswechsel gehört nicht zum dort gezeigten Cache-Validator. Deshalb ist nach dem Upload der korrigierten Version einmal `collect.pl --refresh-menu` erforderlich, danach ein vollständiges Neuladen der Oberfläche. Es werden ausschließlich abgeleitete Menücache-Daten erneuert, keine Domains oder ProFTPD-Einstellungen geändert.
