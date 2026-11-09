---
docs_token: DOCS_TOKEN_CURRENT_BWP1_COST_PROVISION_AND_PAPER_SHADOW_V1
authority: DEVELOPMENT_DELTA_ONLY
runtime_authorization_effect: NONE
---

# Kostenplanung und kapitalfreie Prüfung innerhalb von Paket 1

Ausgangsrevision ist `6b132fa1bd4788a937243c179cf294658c5389f7` (PR 7207).
Dieser Anschluss ist Teil des [ersten Arbeitspakets](CURRENT_SYSTEM_FIVE_BOUNDED_WORK_PACKAGES_V1.md)
und kein neuer Handels-, Kapital- oder Aktivierungsowner.

## Präzisierungen von Frank am 9. November 2026

Das System soll fortgesetzt 24/7 handeln. Ein Fundingzeitpunkt ist kein
Handelsschluss und keine maximale Positionsdauer. Die jeweiligen Instrumente
und Positionen behalten ihre ursprünglichen Zuständigkeiten.

Die Testphase erhält weiterhin 25 USDC Notionalobergrenze und 25 USDC
Verlustzulage je Slot unter zusätzlicher tatsächlicher Kapitalzulassung.
Schließkosten sollen vorab eingeplant werden. Frank verlangt, nicht erst beim
vollständigen Verbrauch zu reagieren, und hat für den wirklichen Verbrauch
der Verlustzulage ausdrücklich den kontrollierten Close der betroffenen
offenen Position festgelegt. Eine zusätzliche pauschale prozentuale
Verlustschwelle ist damit nicht festgelegt. Dieser Positionsanschluss bleibt
bis zu seinem tatsächlichen Quellen-/Consumerbeleg offen.

**OKX-Demohandel ist für die Abnahme ausgeschlossen.** Laut Frank deckt dessen
Instrumentangebot die benötigten Prüfungen nicht ab. Paper und Shadow müssen
auf dem tatsächlich benötigten Originaluniversum und seinen zugelassenen
Marktdaten aufbauen. Verfügbarkeit und Zweckzulassung werden pro Instrument
nachgewiesen. Ein vereinfachtes Ersatzuniversum ist kein Vollständigkeitsbeleg.
Bestehende Demo-/Testnetmodule werden daraus weder aktiviert noch gelöscht.

## Schließkostenvorsorge am Originalbudgetowner

Die ausdrückliche [neue Testpolicy](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V4.json)
ergänzt die vorherige Öffnungskostenpolicy, ohne diese oder die operative
Entrypolicy zu ersetzen. Der bestehende
[Kostenowner](../../../src/ops/portfolio_capital_reservation_budget_v1/entry_execution_cost_v1.py)
liest dieselben aktuellen gebundenen Quellen: Accountidentität, Instrument-
und Feegruppe, Kontotakergebühr sowie beide Orderbuchseiten. Keine zusätzliche
Abfrage, Credentialquelle oder Versandberechtigung wird hergestellt.

Die ursprüngliche native Kontraktmenge wird unverändert übernommen. Eine
LONG-Position benötigt für den Close die Bidseite, eine SHORT-Position die
Askseite; die ursprüngliche Tiefen- und Einheitenrechnung wird wiederverwendet.
Fehlt dort ausführbare Tiefe, wird der neue Entry ohne Teilreservation abgewiesen.
Eine interne umgekehrte Preisabfrage ist keine Gegenentryentscheidung.

Die Gebühr wird für die Vorsorge auf dem Maximum von aktuellem Referenzpreis,
aktuellem Close-VWAP und ursprünglichem modelliertem Stoppreis gerechnet.
Die negative aktuelle Closepreisabweichung wird zusätzlich berücksichtigt.
Diese ausdrückliche Planungsbasis garantiert weder einen späteren Stopfill noch
einen unveränderten Gebührenplan oder ein zukünftiges Orderbuch. Funding ist
in dieser Schließkostenvorsorge noch nicht enthalten.

Der ursprüngliche
[Reservierungsowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
reserviert Notional, Öffnungsgebühr und Schließkostenvorsorge gemeinsam. Die
verbleibende testbezogene Verlustzulage muss modellierten Stopverlust und die
gesamte Öffnungs-/Schließkostenvorsorge tragen. Ein Gebührenrabatt liefert kein
zusätzliches Kapital. Die Vorsorge erhält dieselbe Instrument-, Account-,
Slot-, Mengen-, Entscheidungs- und Originalquellbindung wie die Reservation.

Persistenz, historische Wiederholung und spätere aktuelle Prüfung behalten
ihre verschiedenen Rollen. Ein alter Readback erneuert keine Entryzulassung.
Nur der ursprüngliche bestätigte Close-/Flat-/Kapitalpfad gibt die Reserven
des Zielslots frei; andere Slots behalten ihre eigenen Geldverpflichtungen.

## Messung ohne echtes Handelskapital

Paper prüft am ursprünglichen Accounting und tatsächlichen Entscheidungsconsumer
die virtuellen Slotbudgets, Gebühren, Fundingereignisse, Verlustfolgen und
negativen Ausfallfälle. Synthetische Fixtures belegen die Rechnung und Verbindung,
aber noch keine Kostenverteilung am realen Markt.

Shadow benötigt die zugelassenen Originalmarkt-/Orderbuch-/Fundingquellen und
ein ausgewiesenes Ausführungsmodell ohne Orderversand. Es hält erwartete Kosten,
Zeitbezug, tatsächliche Datenabdeckung und Modellabweichungen getrennt fest.
Eine heutige Quote ist keine tatsächlich ausgeführte Order. Ein späterer
Kontogebührensatz kann ausdrücklich lesend gebunden werden; dieser Auftrag
startet keine private Kontosession und liest keine Credentials.

Die [Quellen-/Consumerprüfung](CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1.md)
bezieht die datierten Obsidian-Notizen ein. Paper und Shadow dürfen verschiedene
Quellen und Speicher benutzen. Zweckzulassung, Preisart, Einheit, Instrument,
Ereignis-/Kenntniszeit und tatsächlicher Consumer werden je Pfad gebunden;
ein gemeinsamer Feed wird nicht vorausgesetzt. Öffentliche Fundingraten sind
keine privaten Bills und keine bereits gebuchte Zahlung.

## Vorsorge bis zur nächsten Fundingabrechnung

Die ausdrückliche [nachfolgende Testpolicy](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json)
verlangt zusätzlich eine eigene aktuelle Public-Fundingquelle für genau das
ausgewählte Instrument. Sie ersetzt keine vorherige Policy oder operative
Konfiguration. Der Original-29P-Join reicht diesen expliziten Input an denselben
Kosten- und Reservierungsowner weiter. Dieser Anschluss führt keine Abfrage aus.

Quelle, Instrumenttyp, Entscheidungs-/Zyklusbindung, erfolgreiche öffentliche
GET-Herkunft, Aufnahmezeit und ursprünglicher Mark-/FX-Bezug werden geprüft.
Der Consumer verlangt die aktuelle Periodenmethode, einen abgeschlossenen
vorherigen Settlementzustand, endliche Rate mit zulässiger Ober-/Untergrenze
und die instrumentbezogenen kommenden Abrechnungszeiten. Fehlende oder ungültige
Größen sperren den neuen Entry ohne Teilreservation. Es gibt keine erfundene
Achtstundenperiode und keine Umdeutung der 1.800 Sekunden Rotationswartezeit.

Dabei bezeichnet `ts` die Rückgabezeit der Quelldaten, `acquired_at_utc` ihre
lokale Aufnahme und `evaluated_at_utc` die finanzielle Prüfung. Keiner dieser
Zeitpunkte ist die Fundingzahlung. `fundingTime` bindet die kommende Abrechnung;
`nextFundingTime` ist die Prognose für die darauf folgende. Die vorhandene
kurze finanzielle Aufnahmezulassung wird wiederverwendet; es wird daraus keine
allgemeine Frischeregel für andere Datenconsumer. Der dokumentierte Endpoint
deckt SWAP und X-Perps-FUTURES ab, nicht automatisch jedes andere Futuresprodukt.
Ein fehlender Datensatz beweist keine Fundingfreiheit eines Instruments.

Die übergebene Rate ist eine Vorhersage für die nächste Abrechnung, keine
beobachtete Kontobewegung. Die Vorsorge benutzt deshalb für LONG die gegenwärtige
obere und für SHORT die negative untere Ratengrenze, multipliziert mit der
gebundenen modellierten Preiseinheit, dem ursprünglichen Kontraktmultiplikator,
der unveränderten nativen Menge und dem ursprünglichen zugelassenen FX-Bezug.
Eine günstige Vorhersage liefert weder einen Geldzufluss noch zusätzliches
Reservierungskapital. Veränderliche spätere Preis-/Ratengrenzen und tatsächliche
Ausführung werden dadurch nicht garantiert.

Notional, Öffnungsgebühr, Closevorsorge und Fundingvorsorge zählen atomar gegen
dasselbe verfügbare Kapital. Die Kosten einschließlich Funding müssen zusammen
mit dem ursprünglichen modellierten Stopverlust in die verbleibende
testbezogene Verlustzulage passen. Persistenz und Cold-Read rekonstruieren die
ursprüngliche Quellenrechnung; eine historische positive Vorsorge ist keine
neue Entryzulassung. Die späte ursprüngliche Budgetprüfung verwirft einen
inzwischen veralteten Input oder überschrittenen Fundingzeitpunkt und erhält
den bestehenden Hold. Beim bestätigten Close wird nur die Vorsorge des
betroffenen Slots freigegeben, während andere Slots ihre Verpflichtungen behalten.

Dieser Anschluss umfasst die **Entryvorsorge bis zur nächsten Abrechnung**.
Er implementiert noch keine laufende Erneuerung für eine darüber hinaus offene
Position. Die bestehenden vier Funding-Episode-Adapter, Startup und Recovery
bleiben unverändert. Ein einfaches öffentliches Fundingfact mit Rate und Zeit
belegt außerdem noch nicht alle hier verlangten Grenzen und Herkunftsfelder.

## Noch offene Anschlüsse und Quellen

Der [Schutz einer offenen Testslotposition](CURRENT_OPEN_TEST_SLOT_LOSS_PROTECTION_V1.md)
ergänzt die Entryvorsorge: Originalaccounting und frischer Mark-/FX-Bezug
erreichen den ursprünglichen kontrollierten Safety-Exit. Ein begonnener Close
und eine belegte markbewertete Erschöpfung werden dauerhaft gebunden. Die
laufende Erneuerung zukünftiger Kosten-/Fundingverpflichtungen bleibt offen;
ein abgelaufener Erstbeleg wird nicht zu einer neuen Deckungszulassung.
Vollständige
Margin-/Liquidationszulassung sowie die fachlich gewählte
Wirtschaftsrahmenrolle gegenüber den festen nativen Replay-Survivalwerten bleiben
eigene Anforderungen dieses Pakets. Diese Kostenergänzung schließt Paket 1 nicht.

Primärquellen für die Kostenbedeutung:
[OKX-Gebührenregeln](https://www.okx.com/help/trading-fee-rules-faq),
[OKX-EEA-Fundingmechanismus](https://www.okx.com/en-gb/help/funding-fee-mechanism-eea),
[OKX-Fundingquelle](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate),
[ursprüngliche Geldnormalisierung](../../../src/ops/governed_productive_monetary_normalization_v1/sizing_source_v1.py).
