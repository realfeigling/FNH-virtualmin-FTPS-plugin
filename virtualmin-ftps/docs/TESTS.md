# Prüfung 0.1.18 Beta

Die Tests prüfen zusätzlich den Wechsel des Log-Stammverzeichnisses mit echtem Bind-Mount, Erhalt alter Inhalte und neue Standard-/Altpfad-Abbildung. Bestehende Chroot-, Rechte-, ACL-, Perl-, Paket- und Manifestprüfungen laufen unverändert weiter.

Zusätzlich werden die /var/log-Ausnahme, unbekannte Gruppen, Kundenmitgliedschaften, Welt-Schreibrechte, erweiterte ACLs sowie die unverändert strenge allgemeine Pfadprüfung getestet.
