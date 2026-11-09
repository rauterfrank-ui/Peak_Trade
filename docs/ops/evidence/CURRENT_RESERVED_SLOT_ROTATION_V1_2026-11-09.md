---
docs_token: DOCS_TOKEN_CURRENT_RESERVED_SLOT_ROTATION_V1_2026_11_09
authority: DEVELOPMENT_DELTA_ONLY
runtime_authorization_effect: NONE
---

# Feste Slotrotation: gebundener Prüfstand vom 9. November 2026

Ausgangsrevision ist `e2abdf73876b6f093347b27c4145b86cb7fc16c6`.
Die [maschinelle Quellenbindung](CURRENT_RESERVED_SLOT_ROTATION_V1_2026-11-09.json)
enthält die tatsächlichen Prüfaufrufe, Log-/JUnitdigests, Quelldigests und das
vollständige geprüfte Entwicklungspaket. Sie ist ein begrenzter Nachweis für den
[beauftragten Rotationsvertrag](../specs/CURRENT_RESERVED_SLOT_ROTATION_V1.md).

## Ergebnis und tatsächlicher Verbrauch

**541 unterschiedliche ausgewählte Fälle PASS**, ohne Fehler, Skips oder
Deselektion: 233 Auswahl-/Rotations-/Exit-/Governancefälle und 308 ursprüngliche
N1-/Kapital-/Wiederaufnahmefälle. Beide vollständigen Läufe sind an dieselben
geänderten Pythonquellen gebunden; die Fallidentitäten überschneiden sich nicht.
Frühere Zwischenläufe und der zur gezielten Journalhärtung abgebrochene Lauf
werden nicht hinzugezählt.

Der tatsächliche ursprüngliche simulierte N5-Root prüft das schwächste Instrument
auf Slot 1 beziehungsweise Slot 5. Nur dieser Slot erhält einen kontrollierten
Rotationsclose; die übrigen Bindungen und Geldverpflichtungen bleiben erhalten.
Der eigene Nachfolger durchläuft den gebundenen aktuellen Marktpreis und
GGE-/Scopepfad, zwei eigene Long- beziehungsweise Shortbeobachtungen, den
ursprünglichen Openingplan, simulierten Fill, die eigene Episode und tatsächliche
Positionsverwaltung. Neue Entries folgen im Host auf bestehende Positionen.

Die getrennten Zustandsfälle prüfen feste Paarbindung trotz neuer Kandidaten,
1.799 Sekunden Wartezeit, frische Erholung und Aufhebung, fehlende/alte/zukünftige
Quellen, neue Positionszyklen ohne Timerreset, falsche Slotidentität, Readback,
CAS-Konflikt und Abbruch zwischen terminalem Archiv und Indexfreigabe. Unlesbare
oder strukturell falsche Rotationsdateien werden nicht überschrieben. Negative
Entrywirkung und fortgesetzte ursprüngliche Exits sind am tatsächlichen Consumer
belegt. Die Plannerfixtures allein werden nicht als bestätigte Fills ausgegeben.

## Governance und erhaltene Originale

Die exakt gebundene Fortschreibung umfasst 19 Laufzeitquellen und davon fünf
eingefrorene Policyquellen. Vorheriger vollständiger Stand oder vollständiger
geprüfter Nachfolger werden zugelassen; Teilpakete, fremde Bodies und geänderte
Originalbaselines bleiben abgewiesen. Der Membershipowner wird ausdrücklich um
das feste Paar und die Wartephase erweitert. Dies ist eine spätere beauftragte
Erweiterung und keine rückwirkende Änderung der früheren Fundingfreigabe.

Ursprünglicher Startup, dauerhafte Topologie, Kapital-Recovery und
Reconciliation-Startup sowie die vier zuvor zugelassenen Fundingadapter sind
bytegleich zur Ausgangsrevision. Native Master-V2-Handelsformeln und beide
Freeze-Tags bleiben unverändert.

Zwei veraltete Membershiptestannahmen wurden an die tatsächliche aktuelle
Bootstrapquelle beziehungsweise die eigene gespeicherte Artefaktidentität
gebunden. Ihr gleichartiges Scheitern am unveränderten Ausgangscommit wurde
vorher separat nachgewiesen; dessen Belegdigest steht in der Quellenbindung.
Gespeicherte kanonische Artefakte wurden nicht geändert oder historisch ersetzt.

## Grenzen

BWP1 bleibt **IN_BEARBEITUNG**. Closekosten-/Fundingvorsorge, vollständige
Margin-/Liquidations- und Verlustfolgenzulassung sowie der vollständige native
Wirtschaftsrahmenanschluss bleiben offen. Feste native Survival-/Bruttoedgewerte
sind weiterhin keine gemessenen Rotations- oder Wirtschaftsgrößen.

Simulierte Verbundprüfungen belegen keinen physischen Stromausfall, reale
Venueausführung oder unbegrenzten Dauerbetrieb. Dies ist kein vollständiger
Repositorytestlauf. Die bekannte alte YAML-Atlas-Testschuld wird nicht durch die
aktuelle Source-Atlasprüfung ersetzt. Keine Live-/Testnet-, Order- oder
Kapitalfreigabe entsteht aus diesem Nachweis.
