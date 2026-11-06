# GGE-only und gemeinsame BTC-Zulassung — Umsetzung 03.11.2026

docs_token: DOCS_TOKEN_GGE_ONLY_AND_BTC_COMMON_ADMISSION_2026_11_03

Die aktive Lösung verwendet ausschließlich GGE. Feste Scope-Initialisierung und explizite Legacy-Distanzgrenzen werden im integrierten Double Play abgewiesen. Die zuvor zugelassene begrenzte Vergleichskonfiguration ist auf Franks ausdrückliche Korrektur hin außer Betrieb genommen; historische Vergleichsdaten und Referenzcode bleiben getrennt erhalten.

## Geändert und geprüft

- GGE-Distanz wird im Trailing ohne wirtschaftliches Clamping verwendet. Die frühere Clamp-Funktion ist aus dem Double-Play-Modul in eine reine Forschungsreferenz verschoben; es gibt keinen Runtimecaller. Auch die festen Maximaldistanzen bei der Scope-Ereigniserzeugung beeinflussen das aktive Profil nicht mehr. Sonstige Risiko-, CHOP-, Confirmation- und Berechtigungsregeln bleiben erhalten.
- Futures werden nicht mehr pauschal Perpetual genannt. Native und kanonische Typ-/Asset-/Quote-/Expiry-Identitäten müssen zusammenpassen; aktuell unterstützte lineare Perpetual-/Terminkontrakte werden unterschieden. Unbekannte/inverse oder widersprüchliche produktive Identität wird blockiert.
- G17 muss zum ausgewählten kanonischen/native Instrument und zur Venue gehören; zukünftige Schätzzeitpunkte werden abgewiesen. Eine in Regeln separat gelieferte Volatilität darf den kanonischen Wert nicht ersetzen. Prozent-/annualisierte-/falsche Intervall-Daten werden nicht als kanonische Fraction-Volatilität angenommen. GGE weist Boolean-/Overflow-Eingaben ab und bindet Beobachtungsherkunft/Zeit in seinen Digest.
- Franks bestätigte Entscheidung: **„Ja, gleiche Zulassungs- und Risikoregeln für Bitcoin“**. Die spezielle BTC-/Alias-Sperre ist aus Universe, kanonischen IDs, Double Play, Kapital-/Mengenbemessung und Order-Intent-Assetfiltern entfernt. Gemeinsame Metadaten-, Mindestmengen-/Notional-, Kapital-, Risiko-, Zustands- und Freigabeprüfungen sind nicht aufgehoben. Das alte Flag für eine gesonderte Bitcoin-Richtungsstrategie ist kein Assetverbot und wird nicht zu einem neuen Strategierecht.
- Bei der instrumentweisen Gegenprüfung wurde AIXBT zunächst wegen einer BTC/XBT-Teilzeichenfolge fälschlich ausgeschlossen. Die aktive gemeinsame Assetbehandlung beseitigt diese falsche Einordnung; AIXBT und BTC durchlaufen die jeweiligen normalen Futuresregeln.
- Learning verwendet einen neuen v3-Konfigurationsvertrag. Vorherige v2-/begrenzte oder unklare Bestände werden nicht still übernommen. Bestehende Code-/Configbindung, Lernpooltrennung und Rückführungsprüfungen bleiben erhalten. Der historische Capture-Ledger ist per SHA256 unverändert bestätigt.

## Nachweis und Grenzen

Die versionierte Metadaten-Fixture enthält alle **493 zulässigen Instrumente des vorhandenen Snapshots vom 16.10.2026**, dessen Herkunft und Revision festgehalten sind. Pro Instrument laufen synthetische PT1M-Mark-Historien durch den wirklichen G17-Producer, die typisierte Bindung, GGE und die integrierte Double-Play-Geometrie. Eine unabhängige Decimal-Berechnung von Logreturns und Populationsstandardabweichung prüft die Magnitude. Drei ausdrücklich synthetische BTC-Identitäten ergänzen USDT-/USDC-Perpetual und einen USD/USDC-Terminkontrakt. Sie sind keine aktuellen Börsenquotes oder realen BTC-Lotdaten.

Fremde Historie, falscher Native-Kontrakt, Zukunftsdaten, falsche Volatilitätseinheiten, abweichende Regel-Volatilität, alte feste Policies, Overflow und ungültige Kontraktidentitäten sind als Gegenfälle geprüft. Ein BTC-Fall mit unzulässiger Mindestmenge wird genauso blockiert wie der entsprechende ETH-Fall. Alte Testfixtures mit Zukunftsdaten oder BTC-Historie bei ETH wurden korrigiert bzw. als Ablehnungsfall festgeschrieben; die Prüfregeln wurden nicht gelockert.

Testläufe und Ergebnisse stehen in [test_summary.json](gge_only_future_interpretation_v3_2026_11_03/test_summary.json); JUnit und Quellhashes liegen daneben. Der Regressionslauf besteht mit 885 Tests, der zusätzliche Asset-/Kernlauf mit 195 und der Learning-/Scope-Lauf mit 113. Läufe überlappen und werden nicht zu einer künstlichen Gesamtsumme addiert. Die abschließende Geometrieprüfung bindet zusätzlich die vollständig wirkungslosen alten numerischen Cap-Slots. Frühere einzelne Teststände bleiben als ergänzende Nachweise erkennbar; kein einzelner Lauf wird als Gesamtprüfung des Repositories ausgegeben.

Das belegt die untersuchten Verarbeitungsketten und Negativgrenzen. Es beweist weder die Vollständigkeit heutiger Listings noch sämtliche zukünftigen Kontrakttypen, Markt-/Forecastqualität, Profitabilität, richtiges historisches Lernen oder Produktivreife. Ungeprüfte Kontrakte werden nicht durch Annahmen zugelassen. Die früher dokumentierten fünf übergeordneten Alt-Gate-Befunde sowie der vollständige Repo-/Map-Abgleich und GitHub-CI sind gesondert offen. Keine Live-Aktivierung, Orders, Kapitalbewegung oder Veröffentlichung.

Aktueller Vertrag: [GGE-only und gemeinsame Asset-Zulassung](../specs/GGE_ONLY_FUTURES_AND_COMMON_ASSET_ADMISSION_V3.md). Fortlaufender Arbeitsstand: [Blueprint, Abschnitt 23](../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
