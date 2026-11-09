---
docs_token: DOCS_TOKEN_CURRENT_OPEN_SLOT_CURRENT_COST_PROTECTION_V1
authority: DEVELOPMENT_DELTA_ONLY
runtime_authorization_effect: NONE
---

# Aktuelle Kosten im Schutz einer offenen Testslotposition

Ausgang ist der korrigierte Merge von PR 7209,
`c54b18f8ae791e054327163de27a4302186a0c13`. Der ursprüngliche Budgetowner hält
Entrykosten und die erste Fundingvorsorge; der ursprüngliche N1-/S7-Pfad
verbraucht seinen dauerhaften slotbezogenen Safety-Auftrag. Die neue
[ausdrückliche Testpolicy](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V7.json)
ergänzt den aktuellen Kostenvergleich. Vorherige Policies bleiben erhalten.

## Bedeutung und Quellen

Die datierten Obsidian-Sichten S01, S11 und S12 wurden mit den tatsächlichen
Ownern abgeglichen: native Kontrakte bleiben native Kontrakte, ein beobachteter
Kostenbetrag ist keine Kapitalzulassung, und Flat ist kein Holdrelease.
Finanzrechnung, Schutzauftrag, bestätigte Ausführung und Kapitalfortschreibung
behalten ihre ursprünglichen Writer.

Die vorhandene `OpenSlotLossObservationV1` kann zusätzlich fünf separat
zugelieferte originale GET-Ergebnisse tragen: Accountkonfiguration,
Instrumentmetadaten, kontobezogene Gebühren, Orderbuch und Fundingrate.
`capture_v1` verlangt dafür die ursprünglichen typisierten Transportergebnisse.
Der Beobachtungsbezug bindet die aktuelle Episode und ihren Bewertungszeitpunkt;
es wird keine neue Handelsentscheidung erfunden. Mark und gegebenenfalls FX
bleiben eigene Inputs. Unterschiedliche Paper-/Shadow-Datenströme bleiben möglich.
Der Adapter führt keine Abfrage durch und baut keinen Transport oder neue
Credential-/Endpointberechtigung auf.

Account, Instrumenttyp, native Instrumentidentität, ursprüngliche Kontrakt-
metadaten, Feegruppe und Familie müssen passen. Private Account-/Feequellen
benötigen ihre Authentifizierungskennzeichnung; öffentliche Quellen dürfen
diese nicht tragen. Erfolgreicher aktueller GET, Aufnahmebezug, Datenzeit,
Antwortform und vorhandene kurze finanzielle Frischezulassung werden geprüft.
Ein vergangener Entry-GET wird nicht als neue Aufnahme ausgegeben.

## Rechnung und tatsächlicher Consumer

Die unveränderte originale Accountingepisode liefert die native Restmenge.
Für LONG wird die ausführbare Bidseite zum SELL-Close verwendet, für SHORT die
Askseite zum BUY-Close. Die komplette Restmenge muss von der übergebenen Tiefe
gedeckt sein. Gebühren werden aus der aktuellen kontobezogenen Takergruppe
gerechnet; ein möglicher Rabatt liefert kein zusätzliches Geld.

Die Feeplanungsbasis ist das Maximum aus aktuellem Mark, aktuellem Close-VWAP
und ursprünglichem modelliertem Stoppreis. Die gegenwärtige negative Abweichung
des Close-VWAP zum Mark kommt als erwartete Schließpreisabweichung hinzu. Dabei
wird keine bereits im ursprünglichen Fillpreis enthaltene Slippage erneut vom
gemessenen Accounting-PnL abgezogen. Der aktuelle originale USDT/USDC-FX-Bezug
wird auch für die Kosten verwendet; USDC benötigt keine erfundene Konversion.

Die öffentliche Fundingquelle muss dieselbe noch kommende Abrechnung wie die
ursprüngliche Reservation benennen. LONG verwendet die aktuelle obere,
SHORT die negative untere Ratengrenze. Preisbasis, Multiplikator, Restmenge und
FX ergeben die dafür geplante USDC-Vorsorge. Prognostizierte Gutschriften sind
kein zusätzlicher Kapitalbestand. Die Rate ist laut
[OKX-API-Vertrag](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate)
eine Prognose; der darauffolgende Termin ist ebenfalls eine Prognose und kann
sich ändern. Es wird keine feste Achtstundenperiode vorausgesetzt.

Der bestehende Verlustschutz vergleicht die markbewertete verbleibende
Testverlustzulage mit dem Maximum aus ursprünglicher Gesamtvorsorge und aktuell
beobachteter Close-/Fundingvorsorge. Reicht sie dafür nicht aus, bindet derselbe
Budgetwriter den bestehenden Safety-Auftrag des genauen Zielslots. N1, S7 und
der native Core bleiben unverändert. Andere Slots werden nicht geschlossen.
Ein günstigerer späterer Kostenbefund hebt einen bereits begonnenen Close nicht
auf. Das ist keine neue prozentuale Verlustschwelle.

Fehlende, fremde, alte oder unzulässige aktuelle Kostendaten erzeugen einen
eigenen unbewiesenen Kostenstatus im gespeicherten Schutzbefund. Der vorherige
Originalschutz und eine unabhängig belegte Verlusterschöpfung bleiben wirksam.
Es wird weder eine fehlende Verpflichtung als null gesetzt noch eine positive
Finanzzulassung behauptet. Wiederholung und Cold-Read rekonstruieren die neue
Quellenrechnung; reine Änderungen eines gespeicherten Kostenbetrags reichen
nicht als neuer Beleg.

## Erhaltene Grenzen und nächster Übergang

Dieser Anschluss aktualisiert die **Schutzrechnung innerhalb der ursprünglich
gebundenen nächsten Fundingperiode**. Er bucht keine Fundingzahlung, verändert
keine Reservation und reserviert kein zusätzliches Kapital. Eine spätere
öffentliche Meldung `settled` ist keine private oder simulierte Accountingbuchung.
Ein anderer beziehungsweise abgelaufener Fundinghorizont bekommt deshalb keine
neue positive Zulassung durch diesen Adapter.

Für die vollständige laufende Verpflichtungserneuerung bleiben der nachgewiesene
Abrechnungsübergang und die atomare Anpassung tatsächlich gehaltener Reserven
offen. Ebenso offen bleiben vollständige Margin-/Liquidationszulassung und der
gesamte Wirtschaftsrahmen von BWP1. Die alten 433- und 74-Fall-Belege behalten
ihre jeweiligen früheren Revisionen.

Simulierte Daten und Fills beweisen keine Kostenverteilung am realen Markt,
garantierten Closepreis, physische Stromausfallfestigkeit oder unbegrenzten
Dauerbetrieb. Startup, ursprüngliche Wiederaufnahme, vier Funding-Episode-
Adapter, operative Finanzkonfiguration und Freeze-Tags bleiben erhalten.

Der [quellengebundene Nachweis](../evidence/CURRENT_OPEN_SLOT_CURRENT_COST_PROTECTION_V1_2026-11-09.json)
enthält 172 ausgewählte bestandene Fälle ohne Fehler, Skips oder Deselektion.
Darunter liegen 28 neue Kosten-/Schutzfälle. Für LONG ist der ursprüngliche
Closefill-/Flat-/Reconciliationpfad, für SHORT der natürliche Entry bis zum
ursprünglichen S7-Safetyentscheid geprüft. Dies ist keine gemeinsame Abnahme
aller Repositorytests und kein vollständiger neuer SHORT-Closefillnachweis.

Quellen: [ursprüngliche Kostenvorsorge](CURRENT_BWP1_COST_PROVISION_AND_PAPER_SHADOW_V1.md),
[offener Slotverlustschutz](CURRENT_OPEN_TEST_SLOT_LOSS_PROTECTION_V1.md),
[Kosten-/Bewertungsadapter](../../../src/ops/portfolio_capital_reservation_budget_v1/entry_execution_cost_v1.py),
[Originalbudgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py),
[verbundene Kostenfälle](../../../tests/ops/test_current_open_slot_cost_protection_v1.py).
