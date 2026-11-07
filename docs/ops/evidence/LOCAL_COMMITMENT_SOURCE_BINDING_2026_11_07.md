---
docs_token: DOCS_TOKEN_LOCAL_COMMITMENT_SOURCE_BINDING_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Lokaler Hold: Bedeutung und Bindung bis zum Reservierungsconsumer

Basis: 1174f9f48ce9a1323938fc22b479ae6689353eec nach PR 7188.
Der [JSON-Beleg](LOCAL_COMMITMENT_SOURCE_BINDING_2026_11_07.json) bindet
Quellen, ursprüngliche Gegenprobe, Testauswahl und offene Grenzen.
Dies setzt die [Treasury-Quellenkorrektur](TREASURY_CAPITAL_SOURCE_SEMANTICS_2026_11_07.md)
mit einem echten Readback des vorhandenen Budget-Owners fort.

## Ursprung, Bedeutung und tatsächlicher Zahlenweg

[PR 6620](https://github.com/rauterfrank-ui/Peak_Trade/pull/6620), Commit
fb79e70c724a6a906407013652f0ae1f674978af vom 19.09.2026, führte den geteilten
Portfolio-Budget-Owner ein. Die Beschreibung spricht von Reservierung freier
USDC-Margin. Im tatsächlichen ursprünglichen Code berechnet dagegen zuerst
der originale Sizing-Owner die Menge; anschließend wird dessen resulting_notional
atomar reserviert. Diese Reihenfolge und die Betragsquelle sind am Originalblob
geprüft. Die damalige Memory-Variante verwirft alte Holds bei neuen Epochen;
die heutige Durable-Variante hält sie über Refresh und Recovery hinweg fest.
Die genaue Entstehungsrevision dieser späteren Durable-Erweiterung ist hier
nicht vollständig rekonstruiert; ihr tatsächlicher aktueller Code ist gebunden.

Die Rollen sind deshalb getrennt zu lesen:

- Der ursprüngliche 29P-Producer liefert aktuelle freie USDC-Margin abzüglich
  eines gegebenenfalls anwendbaren P01. Das ist kein historischer Kapitalstock.
- Im kanonischen Sizingpfad enthält ein lokaler Hold den berechneten
  Nominalwert bei seiner ursprünglichen Entscheidung. Er ist weder ein
  bestätigter Fill noch automatisch die bei OKX gebundene Initialmargin.
- Die öffentliche rohe Reserve-API kann auch einen vom Aufrufer deklarierten
  Budgetbetrag speichern. Ohne ursprüngliches Sizingbinding wird dieser Betrag
  nicht als nachgewiesener resulting_notional oder native Menge etikettiert.
- Der Budget-Consumer setzt seine aktive Holdsumme in bereits gebundenes Kapital
  und die bestehende Exposure-Grenze ein. Die beiden Grenzen werden durch ein
  Minimum verbunden; derselbe Betrag wird dabei nicht additiv zweimal abgezogen.

Die reine Originalprobe mit 1.000 USDC Producerwert und 60 USDC lokalem
Budgetdebit liefert deshalb available_capital=940 und remaining_capital=940.
Der vorgeschaltete bisherige Full-Core-Helfer liefert unabhängig davon den festen
U04-Witness 0/leer. Dieser Wert beweist weder einen leeren lokalen Holdbestand
noch eine konkrete Venue-U04-Belegung. U04 wird nicht mit der lokalen Summe
gleichgesetzt. Das ersetzt keine Rekonstruktion seiner historischen Varianten.

Die [OKX-Dokumentation](https://www.okx.com/docs-v5/en/)
unterscheidet Nominalexposure, freie Equity und für Orders gebundene Margin.
Aus einer gemeinsamen Währung folgt keine gleiche finanzielle Bedeutung.
Eine konkrete Umrechnung oder ein Credit pro lokalem Hold wird hier nicht abgeleitet.

## Kausale Kette und Zustandswirkung

1. Originale Marginaufnahme → Treasury/E4/C08 → originaler 29P-Producer.
2. Originaler Budget-Owner → accountgebundener Readback seines tatsächlichen
   Buchs unter seinem Lock. Er trägt Reservation, Slot, Decision, Cycle und
   ursprüngliche Observation-ID; vorhandene Mengen-/Instrument-/Sizing- und
   Ausführungsbindungen werden mit ihrer tatsächlichen Belegart mitgeführt.
3. Der Marginjoin prüft diesen Readback beim selben ursprünglichen Owner.
   Er macht daraus keinen U04-Fakt und zieht ihn nicht erneut vom Venuewert ab.
4. Derselbe Readback erreicht die originale Sizing-/Reservierungsseam.
   Deren bestehende Kapitalfacts und Mengenrechnung bleiben maßgeblich.
   Die atomare Reserve prüft zusätzlich die gebundene Verpflichtungsgeneration.
   Fremde, manipulierte oder inzwischen geänderte lokale Zustände sperren.
5. RESERVED und COMMITTED zählen weiterhin gegen das lokale Budget.
   COMMITTED ist ein interner Pre-External-Halt. Der Umschlag erhält danach
   die originale Reservation-/Instrument-/Mengenbindung.
6. Die bestehende Sendeseam persistiert SUBMIT_MAY_HAVE_OCCURRED vor dem
   Transport. Bei unbekanntem Ausgang bleibt die Verpflichtung bestehen.
   Ein exakt abgeglichener Entry-Fill mit passender Position hält sie ebenfalls.
7. Bestätigtes Cancel/Reject ohne Fill und mit klarer Pending-Custody kann über
   die originale Reconciliation freigeben. Ein vollständiger Positionsschluss
   benötigt den originalen Close-/Positions-/Pending-/Zeitnachweis und frisches
   zulässiges Kapital, bevor der zuständige Owner freigibt und aktualisiert.
   Lokales Flat oder ein Planlabel allein ersetzt diese Kette nicht.

Der Readback ist eine vorübergehende Projektion des vorhandenen Owners, kein
zweites Ledger. Ein neu geöffneter Owner erzeugt nach seinem ursprünglichen
Restore einen neuen Readback; ein Handle eines anderen oder geschlossenen
Owners wird nicht übernommen. Ein ungewisser Persistenzabschluss erlaubt
keinen leeren Ersatzreadback. Die ursprüngliche Persistenzschema-Version und
die Reservierungs-/Release-/Recoveryregeln bleiben erhalten.

Der produktive ENTER-Pfad verwendet jetzt den realen Readback statt des festen
Empty-U04-Helfers. Der alte Helfer bleibt für ausdrücklich synthetische historische
Aufrufer bestehen. Funding/CT verlangt weiterhin seinen eigenen expliziten U04;
der neue lokale Readback darf diesen Vertrag nicht ersetzen. Die alte unsichere
U04-Positivmenge bleibt am Marginpfad ohne Coveragebeleg gesperrt.

## Prüfung, Fixturekorrekturen und Grenzen

200 ausgewählte Owner-/Integrationsfälle bestehen; 18 davon sind neue gezielte
Fälle. Die Kette umfasst echte vorhandene Writer/Consumer mit synthetischen
Inputs, temporären Stores und ursprünglichen Prozessabbruchtests. Eine
konkurrierende Reserve nach Sizing, aber vor Commit, wird durch die neue
Generationsprüfung ohne zusätzliche Teilreservation abgewiesen.

Die breitere erste Prüfung erreichte 51 bisher maskierte Fehler aus zwei
Close-/Fortsetzungsaufbauten: Sie übergaben unterschiedliche Digests für ihre
eigene Marginbeobachtung und denselben behaupteten Antwortbody. Zwei
repräsentative Originalfälle wurden mit Produktmodulen der Basisrevision
reproduziert. Die Aufbauten benutzen nun denselben ursprünglichen Beleg und
den realen lokalen Owner. Ihre unabhängigen synthetischen Kontowelten erhalten
außerdem Isolation des prozesslokalen Reihenfolgespeichers vor/nach jedem Test.
Reihenfolge-/Frische-/Replayprüfungen innerhalb eines Falls bleiben aktiv;
kein Runtimezustand wird zur Freigabe zurückgesetzt. Alle 52 Close-/Fortsetzungsfälle
und anschließend die gesamte 200er-Auswahl bestehen. Keine fachlichen
Negativassertionen wurden entfernt oder gelockert.

Ein bekannter ENTER-Dokumentfall mit entferntem Atlas-YAML bleibt ausdrücklich
abgewählt. Die weiteren früher dokumentierten Alt-/Setupfehler sind damit nicht
pauschal behoben. Die gezielte Auswahl ersetzt keine Gesamtabnahme.

Weiter offen bleiben die fachliche Eignung der bisherigen konservativen
Nominalbudgetgrenze für das Zielsystem, eine nachgewiesene Zuordnung konkreter
lokaler Holds zu aktueller Venue-Margin sowie unabhängige Kapitalrekonstruktion.
Die unveränderte Sizingseam verwendet ihre lokale Holdsumme auch als
current_reconciled_exposure; das ist hier **keine neu gemessene Marktexposure**.
Der getrennte ursprüngliche Offline-Riskadapter besitzt eigene Positions-/Fill-/
Resthold-Coverage, wird dadurch aber nicht produktiv aktiviert oder zum
Margin-Credit-Owner. Ebenso bleiben vollständiger Host-/Stromausfallwiederanlauf,
natürlicher Dauerbetrieb und fünf aktive Slots gesonderte Arbeit.

Kein echter Venue-GET, Credentialzugriff, Dienststart, Order- oder Kapitalvorgang.
Behauptet wird eine geprüfte lokale Producer-/Consumerbindung mit unveränderter
Zahlenalgebra, keine vollständige Venue-Netting- oder Betriebsfreigabe.
