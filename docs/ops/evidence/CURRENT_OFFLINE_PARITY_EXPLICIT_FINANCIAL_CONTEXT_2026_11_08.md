---
docs_token: DOCS_TOKEN_CURRENT_OFFLINE_PARITY_EXPLICIT_FINANCIAL_CONTEXT_2026_11_08
authority: NONE
runtime_authorization_effect: NONE
---

# Prüfbeleg: expliziter Finanzkontext im heutigen Paritätsvergleich

Aktuelle Basis: 65fdc5075b3adda49e12c83f21276d0ec96dd50d. Der
[gemeinsame Ownerlauf](CURRENT_OFFLINE_PARITY_EXPLICIT_FINANCIAL_CONTEXT_2026_11_08.json)
endet mit **2090 PASS, Exit 0, ohne Ausschlüsse**. Die drei im
[vorigen Beleg](CURRENT_SURVIVAL_NUMERIC_ADMISSION_2026_11_08.md) fehlgeschlagenen
Prüfungen bleiben unverändert enthalten und bestehen jetzt. Ihre Testkörper und
PASS-Erwartungen wurden nicht geändert. Der ältere fehlgeschlagene Beleg bleibt
als revisiongebundener Befund erhalten.

Der Lauf umfasst die bisherigen 1882 Fälle, 41 neue Kontext-/Mengen-/Consumerfälle,
zwei neue Manifestsperrfälle und 165 zusätzliche bestehende Adapter-/Surface-P-
Verträge. Er bindet vor/nach
dem Lauf alle erfassten Pythonquellen, die tatsächlich geladenen Module, exakte
Selectoren sowie Runner-, Inventar- und Loghash. Dieser vollständig beendete PASS
wird beim Metadaten- und Commitabschluss wiederverwendet.

Die [Reparatur und ihre Semantik](../specs/CURRENT_OFFLINE_PARITY_EXPLICIT_FINANCIAL_CONTEXT_V1.md)
verwenden den vorhandenen vollständigen Finanzkontext und die ursprünglichen
Mengen-/Intentbinder. Explizites None und fehlende Tickkontexte führen in der
neuen Übergabe zu keiner Wiederbelegung mit isolierten Kontoliteralen. Die
Financial-Fixture entnimmt LONG/SHORT dem tatsächlichen Entry-Ausgang und prüft
Instrument und Preis. Beide Vergleichszweige erhalten deklariertes synthetisches
Material. Der Originalowner verändert nachweislich Menge und Intent von 1,20 auf
0,80 Einheiten, wenn nur die explizite Scopegrenze von 120 auf 80 wechselt.

Negative Fälle prüfen fehlende/fremde Kontexte, Referenzpreis, Modus, Kapital,
Stop, fehlende Armed-Seite und abweichende Ergebnisreferenzen bei gleichen
BOUND_OFFLINE-Labels. Der neue Tickkontext wird tatsächlich durch den Replay an
beide Adapter weitergereicht; leere Folgeadressen bleiben ungebunden. Diese
Tests verwenden synthetische Daten, temporäre Stores und gesperrte oder
synthetische Ports. Reale Konten, Credentials und Venueorders wurden nicht
verwendet oder verändert.

Im ersten erweiterten Lauf bestanden 2081 Fälle, sieben weitere positive Tests
scheiterten an der Annahme eines vorhandenen datierten Archivmanifests. Ihre
positiven Assertions sind unverändert, was zusätzlich über identische AST-Körper
belegt ist. Sie verwenden jetzt eine frische temporäre aktuelle Quellbindung mit
echtem SHA-256-Manifest und dem unveränderten Originalverifier. Keine Verifier-
Antwort wird gemockt. Zwei neue Negativfälle belegen die Sperre bei fehlendem
Verzeichnis und bei einer tatsächlichen Veränderung nach der Manifestbildung.
Der fehlgeschlagene Zwischenlauf bleibt erhalten.

Das wirkliche unveränderte Standardmanifest bleibt fehlend. Eine separate
Abfrage nach dem Testlauf belegt daher weiterhin false für die finalen globalen
Erfolgsflags. Der positive Testbeleg ersetzt keine globale kanonische Quelle.
Archivbelege wurden nicht wiederhergestellt und der Manifest-/Flagowner nicht
geändert.

**Grenze:** Der Standarddatensatz erreicht keinen SHORT-Entry. Das wird als
Abwesenheit geprüft. Die gesonderten SHORT-Adapterfälle verwenden einen
tatsächlichen heutigen kanonischen SHORT-Policyausgang als synthetischen
Gegenversuch. Es wird kein natürlicher SHORT-Hostablauf behauptet. Das Ergebnis
bleibt Offline-Adapterparität; vollständige Hostkette, wirtschaftliche
Survival-Inputherleitung, produktive numerische Risikozulassung und weitere
Außenring-/Gesamtabnahmeverträge bleiben offen. Keine Betriebsparameter,
Original-Risikoformel, produktive Gates oder Runtimefreigabe wurden geändert.
