---
docs_token: DOCS_TOKEN_CURRENT_OPEN_TEST_SLOT_LOSS_PROTECTION_V1
authority: DEVELOPMENT_DELTA_ONLY
runtime_authorization_effect: NONE
---

# Verlustschutz einer offenen Testslotposition

Ausgang ist `07d966bbf`: Öffnungs-/Schließkosten und Vorsorge bis zur nächsten
Fundingabrechnung liegen beim Originalbudgetowner. Frank hat für die Testphase
25 USDC Verlustzulage je Slot, keine automatische Auffüllung und bei Verbrauch
den kontrollierten Close verlangt. Kosten sollen vorher berücksichtigt werden.
Die Fortsetzung bleibt innerhalb von BWP1; dies ist kein Paketabschluss.

## Wissensquellen und Semantik

Auf Franks erneuten Hinweis wurden die datierten Obsidian-Notizen zu Accounting,
Risk, Wiederanlauf, Kapital/Accounting/Lernergebnis und den vier unterschiedlichen
Killverträgen sowie S01, S11 und S12 berücksichtigt. Ihre konkreten Byte- und
Datumsbindungen werden im Prüfbeleg aufbewahrt. Diese Adressen sind analytische
Sichten, keine zusätzlichen Runtime-Layer oder Autorisierungen.

- **Fachsemantik/S01:** Native Kontrakte sind keine Coins, 25 USDC Notional sind
  keine Equity und kein Stopabstand. Realisierter PnL, markbewerteter offener PnL,
  Fundingrate und gebuchte Fundingzahlung bleiben verschieden. Das Original-
  Accounting führt Equity als Anfangskapital plus realisierten und unrealisierten
  PnL plus beobachtete Fundingzahlungen minus Gebühren. Im Fillpreis enthaltene
  Slippage wird nicht noch einmal abgezogen. Die neue Bewertung liest und
  verwendet diesen Originalkernel; sie führt kein eigenes Geldledger.
- **Betriebssemantik/S11:** Ein gespeicherter Schutzbefund ist kein Fill oder
  Positionsende. Der originale Budgetwriter speichert die Episode-/Slotbindung
  und den begonnenen Closeauftrag. Wiederlesen prüft dessen Originalquellen;
  unbekannter oder gescheiterter Commit verlangt den vorhandenen Wiederanlauf.
  Ein erfolgreicher Prozess-/Cold-Read-Test ist kein physischer Stromausfallbeleg.
- **Finanz-/Schutzgrenzen/S12:** Der Beobachter erzeugt kein verfügbares Kapital.
  Der bestehende Safety-Exit konsumiert nur eine überprüfte Referenz des
  Originalbudgetowners. Er verändert weder BULL/BEAR noch den globalen
  Killzustandswriter. Schutzabsicht, Ausführung, Flat, Reconciliation und
  Kapitalfreigabe behalten ihre ursprünglichen eigenen Owner.

Die Hinweise wurden insbesondere gegen den
[Accountingkernel](../../../src/ops/productive_futures_accounting_runtime_binding_v1/accounting_engine_v1.py),
den [ursprünglichen Episodenfortschritt](../../../src/ops/exit_policy_producer_binding_v1/simulated_accounting_progress_v1.py)
und den [MV2-Killreader](../../../src/ops/hard_facts_system_closure_v1/durable_kill_switch_mv2_binding_v1.py)
abgeglichen. Ein gemeinsames generisches `safe=true` ersetzt diese Verträge nicht.

## Ausdrückliche Testpolicy und Originalquellen

Die [neue Testpolicy](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V6.json) ergänzt die
vorherige Fundingpolicy. Alle bisherigen Policydateien und die operative
Konfiguration behalten ihren Vertrag. Ein vorhandener Altstore wird nicht
stillschweigend um eine neue Schutzfreigabe ergänzt.

Der vorhandene [Kosten-/Bewertungsadapter](../../../src/ops/portfolio_capital_reservation_budget_v1/entry_execution_cost_v1.py)
liest die ursprünglichen unveränderlichen Accountingarchive der aktuellen
intern simulierten Episode. Anfangsquelle, aktueller Fill-/Fundingfortschritt,
Account, Slot, Instrument, Seite und native Restmenge müssen zur gespeicherten
Originalreservation und ihrem Entryplan passen. Die Restmenge wird nicht erhöht.

Ein separat übergebener aktueller Public-Mark-GET und sein eigener Aufnahmebezug
bewerten die offene Position. Bei USDT kommt eine getrennte aktuelle originale
USDT/USDC-Indexkonversion mit eigenen Metadaten und Zeitprüfungen hinzu. Eine
alte Entryquote oder implizite Stablecoinparität ersetzt diese Quelle nicht.
Markdatenrückgabe, lokale Aufnahme, finanzielle Bewertung, Fill-/Fundingereignis
und Coretick behalten unterschiedliche Zeitbedeutungen. Die Beobachtung muss
genau zum aktuellen N1-Preis und dessen Bewertungszeitpunkt passen.

Der Adapter setzt den unveränderten Accountingkernel auf den aktuellen Mark.
Die Equitydifferenz seit dem bestätigten Opening des Zielzyklus enthält dessen
bereits beobachtete Gebühren und Fundingzahlungen. Ältere abgeschlossene
Slotzyklen werden genau einmal aus dem ursprünglichen Testverlustzustand
berücksichtigt und bleiben auf den damaligen Kenntnisstand begrenzt. Ein
Instrumentwechsel oder Neustart erzeugt kein neues Anfangsbudget.

## Tatsächliche Wirkung und Zustandsfolge

Ist die so markbewertete Verlustzulage verbraucht, speichert derselbe
[Originalbudgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
den Erschöpfungsbeleg und einen Closeauftrag für genau diese Reservation und
Episode. Vor der gebundenen nächsten Fundingabrechnung kann auch die fehlende
Deckung der bereits reservierten Close-/Fundingvorsorge den kontrollierten
Close beginnen. Dafür wird keine neue prozentuale Verlustschwelle erfunden.

Der [N1-Join](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
reicht ausschließlich eine überprüfbare Referenz dieses Originalwriters an den
[bestehenden S7-Adapter](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py)
weiter. Dieser bindet sie unmittelbar vor dem ursprünglichen Coreaufruf an Slot,
Instrument und Episode und verwendet den bereits vorhandenen expliziten
Safety-Eingang. Der unveränderte Core produziert seinen eigenen Safety-Exit und
seine ursprüngliche Full-Close-Intent-/Mengenübergabe. Offene Positionen werden
vor neuen Entries verarbeitet.

Ein begonnener Close bleibt bis zum ursprünglichen bestätigten Abschluss
gebunden, auch wenn ein späterer Mark sich verbessert oder die nächste optionale
Bewertung fehlt. Tatsächlich belegte Erschöpfung sperrt zusätzlich neue Entries
dieses Testslots. Die ursprünglichen frühen und späten Budgetconsumer lesen
diese Tatsache erneut. Eine vorsorgliche Schließung wegen fehlender Kostendeckung
ist dagegen kein erfundener Verbrauch der gesamten 25 USDC: Nach bestätigtem
Close und wirtschaftlicher Fortschreibung entscheidet das ursprüngliche
verbleibende Verlustbudget über einen weiteren Entry.

Fehlende, alte, zukünftige oder fremde optionale Mark-/FX-/Episodeninputs erzeugen
weder einen Verlustbetrag noch eine neue positive Finanzzulassung. Der N1-Output
weist die neue Beobachtung ausdrücklich als unbewiesen aus. Ursprüngliche
risikoreduzierende Ausgänge bleiben verfügbar; eine bereits gespeicherte gültige
Closebindung bleibt erhalten. Ein Fehler des Originalbudgetwriters wird nicht
als bloß fehlende Beobachtung verschluckt.

Der Schutzbefund gibt keinen Hold frei. Erst tatsächlicher simulierter Closefill,
Flatwitness, originale Reconciliation und frische Kapitalfortschreibung führen
den ursprünglichen Zielslotabschluss aus. Andere Slots behalten ihre Menge,
Instrumentbindung und Kostenverpflichtungen. Startup, ursprüngliche Recovery,
native Coreformeln und die vier Funding-Episode-Adapter bleiben unverändert.

## Quellengebundene Entwicklungsfortschreibung

Franks beauftragter kontrollierter Testslotclose wird über genau die beiden
oben verlinkten N1-/S7-Wiringadapter verbunden. Der
[bestehende Policyprüfer](../../system_atlas/policy_projection.py)
behält das ursprüngliche vollständige Rotationsbundle und akzeptiert zusätzlich
exakt dieses zusammenhängende Adapterpaar als Nachfolger. Die 17 übrigen
Rotationsquelldateien und deren eingefrorene Policybindungen bleiben erhalten.
Ein einzelner geänderter Adapter, fremde Bodies oder eine umgedeutete
Parentbindung werden abgewiesen. Eine gewöhnliche Hashnachführung erweitert
diese konkrete Zulassung nicht. Die Fortschreibung betrifft keine native
Handelsformel, keine Startup-/Recoveryregel und keine externe Ausführungsfreigabe.

## Bewusste Nachweisgrenzen

Der Quellpfad ist ausdrücklich intern simuliertes Accounting mit separat
übergebenen Mark-/FX-Ports. Sein markbewerteter Verlust ist keine beobachtete
private Venue-Kontobelastung. Die Erstkosten-/Fundingvorsorge wird hier nicht
zu einer garantierten aktuellen Kostenobergrenze umbenannt. Nach Ablauf ihres
gebundenen Fundinghorizonts wird keine neue Vorsorge und keine fehlende Zahlung
als null erfunden; die reine gemessene Verlusterschöpfung bleibt ein eigener
Schutzgrund. Die laufende Erneuerung von Kosten-/Fundingverpflichtungen und die
vollständige Margin-/Liquidationszulassung bleiben offen.

Diese Trennung ist Teil der [Paper-/Shadow-Quellensemantik](CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1.md).
Mehrere Datenströme bleiben möglich. Ein lokaler Schutztest belegt weder das
gesamte benötigte Instrumentuniversum noch natürlichen durchgängigen Dauerbetrieb.
Ein eigenständiges Sendemandat oder eine Live-/Testnetfreigabe entsteht nicht.
