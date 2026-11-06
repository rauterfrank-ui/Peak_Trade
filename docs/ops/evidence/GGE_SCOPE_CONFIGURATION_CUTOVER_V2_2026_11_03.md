# Scope/GGE-Konfiguration und getrennte Lernbestände — lokale Umsetzung 03.11.2026

docs_token: DOCS_TOKEN_GGE_SCOPE_CONFIGURATION_CUTOVER_V2_2026_11_03

Die Lösung behält beide Varianten mit eindeutiger Zuständigkeit: instrumentrelative GGE-Distanz als produktiver Default; ausdrücklich begrenzte Legacy-Policy für Vergleiche. Es gibt keinen zweiten gleichzeitigen Scope-Owner. In delegierten Zyklen gilt der validierte D_t-/R_t-Seal.

## Umgesetzt

- Raw-Envelope verwendet die GGE-Magnitude ohne wirtschaftliche Unter-/Obergrenze; der nachgewiesene Min-1-Effekt entfällt. LONG/SHORT behalten ihre Ankermechanik; Neutral aktualisiert die Distanz ohne Anker-Trailing. CHOP bleibt eingefroren. Nicht-Distanz-Risiko-/Berechtigungsregeln bleiben wirksam.
- Persistenz führt den Distanzmodus mit. Unpassende Snapshot-Policy wird abgewiesen; alte unversionierte CHOP-Zustände werden nicht automatisch umgedeutet. Normale alte Bänder werden im Raw-Pfad aus GGE aktualisiert. Delegierte Readmodels beziehen Magnitude/Anker aus dem validierten Seal.
- Stopableitung verwendet die tatsächlich ausgewertete adverse Scope-Distanz. Der GHV-Trace zeichnet die konsumierte Magnitude auf, statt ein gegebenenfalls noch altes Vorzustandsband als effektive Distanz zu bezeichnen.
- Versionierte Konfigurationskennung umfasst Instrument/Markttyp, Distanzmodus/-Owner, deklarierte Config, Policies und Regelparameter. Marktpreis und aufgelöste Volatilität sind keine neue Konfiguration pro Tick.
- Entscheidung → Outcome/Attribution/Counterfactual → Lernzustand → Export erhält die Herkunft. Host-Pools werden nach Session, Account, Code und Config getrennt. Widersprüchliche Bundle-Herkunft, Fremdkonfiguration im Vorgängerzustand und nachträgliche Umetikettierung werden abgewiesen. Die Codekennung bindet die deklarierte Git-Revision per Domain-SHA256; tatsächliche geänderte Dateien sind separat gehasht.
- Score-Label-Feedback wird gegen die aktuelle Konfiguration geprüft. Unbekannte/fremde Herkunft wird nicht übernommen; ein bereits übernommenes altes Label wird bei Abweichung entfernt. Es bleibt ein opakes Bewertungslabel, kein neu trainiertes Modell.
- Betroffene Policies/Manifest/Runbook/Map-Navigation und strukturierte Atlas-Quellen sind fortgeschrieben; Atlas-Ansichten wurden per Generator erneuert. Das ersetzt den noch offenen vollständigen Repo-Abgleich nicht.

## Prüfungen und Grenzen

31 neue Vertrag-/Integrationstests bestehen, darunter sechs Preisskalen von 0,00001 bis 100.000 in LONG/SHORT/Neutral, restaurierte Bänder, Seal-Projektion, Policy-Konflikt, CHOP-Migration, Persistenz und Capture → abgeschlossene Bars → Outcome → Lernzustand → Export mit getrennten Varianten. Positive Rückführung eigener sowie negative Rückführung fremder/unklarer Konfiguration sind geprüft.

Der fokussierte Join-/Scope-Lauf besteht mit 44 Tests; der Trace-/Persistenzlauf mit 42 Tests. Ein breiterer Lauf über das Learning-Paket und betroffene Scope-/Join-Tests ergab 754 PASS und fünf FAIL. Diese fünf Befunde bestanden bereits in der vorliegenden Basis: fehlende historische Runbook-/Navigationsverweise, ein alter Workpackage-Diff-Prefix-Gate und ein alter Ledger-Pfad-Gate. Die zugehörigen gepinnten Git-Befunde stehen in `preexisting_failures.json`. Die Gates wurden nicht gelockert. Spätere kleine Änderungen sind durch die fokussierten Läufe gebunden; der breite Lauf ist kein exakter Komplettnachweis des finalen Commits.

Numerische Probe: GGE/Init/LONG/SHORT/Neutral stimmen bei allen sechs Skalen überein. Legacy-50/500-Vergleiche bleiben unterscheidbar. Python-Lint und Atlas-Strukturprüfung bestehen. JUnit, Probe und Quellhashes liegen im gleichnamigen Evidence-Ordner.

Der untersuchte historische Capture-Ledger ist unverändert (SHA256 in `source_binding.json`). Alte Lerndaten wurden weder gelöscht noch als neue Daten etikettiert. Unbekannte Herkunft ist nicht gleich bewiesene numerische Fehlerhaftigkeit. Neue Daten sind dieser Scope-Konfiguration eindeutig zuordenbar; damit ist weder ökonomische Richtigkeit aller Labels noch Profitabilität, Trainingsqualität oder vollständige Produktivreife bewiesen. Kein Dienst aktiviert und kein GitHub-Push ausgeführt; GitHub-CI und vollständiger Repo-/Map-Abgleich bleiben offen.

Aktueller Vertrag: [Raw-/Legacy-Konfiguration und Lernen](../specs/GGE_RAW_AND_LEGACY_SCOPE_LEARNING_CONFIGURATION_V2.md). Laufender Gesamtstand: [Blueprint, Abschnitt 22](../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md).
