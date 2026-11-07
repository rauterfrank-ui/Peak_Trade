---
docs_token: DOCS_TOKEN_N1_ORIGINAL_PLAN_ORIGIN_BINDING_2026_11_07
authority: NONE
runtime_authorization_effect: NONE
---

# Ursprüngliches Intent und Venueplan im Originalbudget

Basis: ad63a2dc5bc5823d98e42c3b0bd72026b04aeed2 nach PR 7194.
Der [JSON-Nachweis](N1_ORIGINAL_PLAN_ORIGIN_BINDING_2026_11_07.json) bindet
Producer, Consumer, Quellen, Gegenprobe und abgeschlossene Ownerprüfung.
Dies ist ein Quellanschluss vor der weiterhin offenen natürlichen Executionidentity.

## Ursprüngliche Konstruktion und tatsächlicher Verlust

Der [ursprüngliche CanonicalIntentvertrag](../../../src/governance/canonical_order_intent_v1.py)
bindet Decision, kanonisches Instrument, native Kontraktmenge, finanzielle Referenzen,
Konfiguration und Handelspolicies. Seine Flags geben keine direkte Submission frei.
Der ursprüngliche Venueplan entsteht anschließend aus der zugelassenen Core-/Intent-
Transformation. Seine native Instrumentkennung, clOrdId, Orderumgebung und sein
Venuepayload sind eigene Felder; das Envelope übernimmt nur einen Teil davon.

Im [tatsächlichen N1-Producer](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
liegen Intent und Venueplan gemeinsam vor. Der Originalbudgetowner erhielt bislang
nur das Envelope. Der noch nicht gesendete dauerhafte PLAN_BOUND-Link enthält deshalb
weder das Originalintent noch das vollständige Planobjekt oder dessen Orderumgebung.
Die Gegenprobe bestätigt den fehlenden Eintrag für Long und Short am wirklichen
Standing-Supervisor mit synthetischen Quellen.

Die frühere Oktober-Kapitalguard-/Reconciliationlinie bleibt gesondert. Ihre
Authority, Consumption-Key und Callerinputs werden nicht umbenannt. Die bereits
in [PR 7194 gebundene Quellenprüfung](ORIGINAL_BUDGET_SEPARATE_SEND_PERMIT_HANDOFF_2026_11_07.md)
bleibt Herkunftsbeleg, keine heutige Betriebsfreigabe. Andere aktuell gelesene
Stateowner liefern keine passende Ersatzversion: Die kanonische Authorization-V2
schließt Orders und Live ausdrücklich aus; das allgemeine Orderledger ist
in-memory. Ein dortiger Verbrauch oder Zähler ist kein natürlicher N1-Submitversuch.

## Producer, Persistenz und tatsächliche Consumerwirkung

1. N1 übergibt jetzt genau sein ursprüngliches CanonicalIntent und seinen bereits
   entstandenen VenuePlanCandidate zusammen mit dem Envelope an denselben Budgetowner.
2. Die [neue Quellbindung im bestehenden Budgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/plan_origin_v1.py)
   serialisiert diese Originalwerte als optionalen PLAN_BOUND-Eintrag plan_origin.
   Ihr eigenes Schema und ihr Trägerdigest sind neu; sie werden nicht als historisch
   vorhandene Authority oder als alter Venueplandigest ausgegeben.
3. Die vorhandene strikte Dataclass-Decodierung erhält alle Intentfelder ohne Defaults.
   Der ursprüngliche Intentvalidator und seine vorhandenen Referenzfunktionen prüfen
   Decision, kanonisches Instrument, Config, Menge, Metadaten und finanzielle Herkunft
   gegen die bereits gespeicherte Original-Sizingentscheidung. Es entsteht keine neue
   Finanz- oder Mengenrechnung.
4. Der originale Envelopebinder und Venuebodybuilder prüfen die unveränderte
   Transformation. Die Orderumgebung wird nach ihrem bestehenden Identity-Vertrag
   geprüft; SHADOW, PAPER_EXCHANGE, TESTNET und LIVE werden nicht gleichgesetzt.
5. Der [originale Executionlink-Consumer](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py)
   prüft diesen Eintrag bei Bindung, Submit und Kaltlesen. Bei vorhandenem Originalplan
   muss die zugelieferte Executionumgebung exakt dessen Orderumgebung entsprechen.
   Die reine Originalkontextprüfung gibt zusätzlich Trägerdigest und Orderumgebung
   zurück, ohne einen Zustand zu verbrauchen.
6. Der bestehende Submit-/Reconciliationwriter erhält die Quellbindung bei seinem
   Writeback zusammen mit der separaten Permitkopie. Hold, Legacyidentity und beide
   ursprünglichen Submitbarrieren bleiben getrennt und unverändert zuständig.

Kanonische und native Instrumentkennung bleiben verschieden. Decimal-Kontraktmenge,
ursprüngliche Quellenreferenzen, Trading-Epoch, Envelope-Erstellungszeit und
Orderumgebung behalten ihre eigenen Bedeutungen. Ein Readback erzeugt keinen neuen
Quellenstempel und erneuert keine alte Core-/Riskentscheidung.

## Replay, Kompatibilität und Autoritätsgrenze

Ein identisches Rebind ist idempotent und schreibt keinen neuen Storezustand.
Geänderte oder nachträglich ergänzte Herkunft wird abgewiesen. Fehlende historische
Felder bleiben bei Legacylinks abwesend; sie werden weder aus dem Envelope erfunden
noch beim Kaltlesen ergänzt. Ältere strikte Reader können erweiterte Links ablehnen.
Für einen Rückwechsel dürfen weder gespeicherte Felder entfernt noch Holds
zurückgesetzt werden.

Diese Quellbindung ist kein unabhängiger Authenticity-/Anti-Clone-Beweis jedes
Callerfeldes und keine aktuelle Versandzulassung. Authority-, Attempt- und lokale
Stateversionsfelder der Legacyidentity bleiben unberührt. Der Supervisor schließt
seinen Owner weiterhin; kalte Wiederaufnahme verlangt originale frische Recovery.
S6 endet weiter an PRE_EXTERNAL_EFFECT. Kein neuer GET, Ledger, Permitproducer,
Submitversuch oder automatischer POST-Anschluss entsteht.

## Prüfung und verbleibender Anschluss

[31 neue Fälle](../../../tests/ops/test_n1_original_plan_origin_v1.py) prüfen Long/Short
am tatsächlichen Supervisor, exakte Quellwerte, ursprüngliche Sizingreferenzen,
fremde und beschädigte Kontexte, unveränderte Holds, Rebind, Legacy ohne Nachfüllung,
Environment-Veto, Kaltlesen, die direkten Wrapper sowie den Originalhost-Reconciler.
Die gemeinsame Prüfung endet mit **263 PASS, Exit 0**, am exakt gebundenen Codestand.
Alle Quellen sind synthetisch, Stores temporär und Sockets in den neuen Fällen gesperrt.

Eine frühere neue Testannahme verwendete einen Risk-Readback nach dem Schließen des
Supervisors und scheiterte korrekt an RISK_DURABLE_OWNER_REQUIRED. Die Probe übernimmt
jetzt den während des Originalbinds aufgenommenen Snapshot. Diese Produktsperre wurde
nicht verändert. Zwei vorhandene Beobachtungstestports reichen die neuen Argumente
unverändert an den Originalowner weiter; ihre bisherigen Assertions bleiben erhalten.

Ein echter Attempt-/Stateversionsproducer im ausgewählten natürlichen Sendepfad und
der passende versionierte Executionidentity-Vertrag bleiben als nächster Anschluss
offen. Ein neuer Vertrag muss seinen Writer, Zeitpunkt, Dauerhaftigkeit und Consumer
ausdrücklich benennen; Cycle-ID, Reservation, Permit-ID oder Budgetsequenz werden
nicht pauschal zu Ersatzwerten. Ebenso offen bleiben eigenständige Authorityherkunft,
vollständige aktuelle Zulassung, Root-/Owner-Eindeutigkeit, Pending-Custody,
Never-submitted-Recovery, fortgesetzter Hostauftrag und Gesamtbetrieb. Die älteren
Collector-/Account-Closeout-Fehler, der alte Atlas-Dokumenttest und der datierte
Obsidian-Projektionscheck werden durch diesen PASS nicht geschlossen.
