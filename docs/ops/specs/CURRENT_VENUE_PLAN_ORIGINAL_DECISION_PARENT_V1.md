---
docs_token: DOCS_TOKEN_CURRENT_VENUE_PLAN_ORIGINAL_DECISION_PARENT_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Ursprünglicher Core-Entscheidungsparent am tatsächlichen Planconsumer

Basis 9978959a6e5edffa6f6f332b15384e046d09d84f auf dem bestehenden Arbeitsbranch.
Dieser Anschluss prüft die konkrete Herkunft des aktuell zur Planbildung
übergebenen ENTER-Intents. Er erzeugt keine neue Entscheidung und ist keine
vollständige heutige Core-/Risk-/Altplan-/Kapitalzulassung.

## Ursprüngliche Konstruktion

Der [ursprüngliche Decisionowner](../../../src/trading/master_v2/canonical_trading_decision_evidence_v1.py)
führt decision_id, logische trading_epoch, Instrument, Outcome, Seite und eigene
semantische Identität. Der [ursprüngliche 29P-Adapter](../../../src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py)
verbindet seine tatsächliche Sizingentscheidung und Quantityprovenance mit diesem
Entscheidungsparent. Der [ursprüngliche 29Q-Adapter](../../../src/trading/master_v2/canonical_order_intent_offline_replay_binding_adapter_v0.py)
erzeugt daraus den typisierten CanonicalOrderIntent und bindet dessen tatsächlichen
Digest an denselben Parent. Nach einer zulässigen Originaltransformation werden
die entsprechenden Referenzen und der Parentdigest ursprünglich neu gebunden.

Die [ursprüngliche Abbildung](../../../src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py)
trennt ENTER_LONG/ENTER_SHORT und LONG/SHORT. Der
[Intentowner](../../../src/governance/canonical_order_intent_v1.py) besitzt seine
Validierung und die Referenzfunktionen für Kapitalenvelope, Vor-/Nachrisiko,
Sizing und Quantityprovenance. Diese Quellen sind am Source-Freeze
c742a23c964901c1353fcf3468e618db9cb6ef42 vorhanden und bleiben bytegleich.
Eine früheste historische Entstehung wird daraus nicht behauptet.

## Belegte Lücke am aktuellen Consumer

Der [aktuelle Planbinder](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_venue_plan_v1.py)
ruft den bestehenden [Core-Intent-Composer](../../../src/ops/full_core_live_path_composition_root_v1/composition_root_v1.py)
auf. Dessen frühere Typ-, Instrument-, Mengen-, Safety- und Nichtleerprüfungen
verbanden den verwendeten Intent noch nicht vollständig mit dem tatsächlichen
Entscheidungsparent und den tatsächlichen 29P-Referenzen. Die optionale explizite
expected_trading_epoch wurde vom natürlichen Planbinder nicht gesetzt; sie war
kein Ersatz für die Bindung an den tatsächlich übergebenen Parent.

13 Gegenfälle am unveränderten Basiscode erhalten trotzdem einen Venueplan:
fremde Decision-ID, andere logische Epoche, entgegengesetzte Entryaktion,
fremde Intent-/Risk-/Quantityreferenz, falscher Parentdigest, falsche Bindungseffekte,
fremde Sizing-/Kapital-/Nachrisikoreferenz und falscher Kinddigest. Eine positive
Originalprobe besteht bereits. Die Gegenproben sind keine ausgeführten Orders.
Ein anderer Originalbudgetconsumer konnte manche Widersprüche später schon
ablehnen; das ersetzt die fehlende Prüfung am früheren Planconsumer nicht.

## Feldbedeutung und tatsächliche Prüfung

Für den bestehenden ENTER-Zweig prüft derselbe Composer zusätzlich:

- Den tatsächlichen typisierten finalen Decisionparent einschließlich dessen
  ursprünglichem semantischem Digest. Die eigenen Runtime-/Order-/Authorityflags
  bleiben NONE und die ursprünglichen Eligibility-/Adapterflags false.
- Den tatsächlichen CanonicalOrderIntent durch den vorhandenen Originalvalidator.
  Ein nichtleerer oder selbstkonsistent ersetzter Kinddigest allein genügt nicht.
- Identische ursprüngliche decision_id bei Parent, Intent und kanonischem
  Sizingresultat. Diese ID ist kein Venue-Order-ID- oder Kapital-Attempt-Ersatz.
- trading_epoch als ursprünglichen logischen Ganzzahlbezug des Parents; der
  Intent muss exakt dessen ursprüngliche Stringdarstellung tragen. Boolean und
  umtypisierter Parentstring sind keine Ersatzepoche. Es findet keine Umrechnung
  in UTC, Unixsekunden oder Millisekunden statt.
- Dieselbe durch den Originalmapper abgebildete Entryaktion und Seite sowie
  dieselbe Sizingseite, finale native Menge und Einheit CONTRACTS. Kanonische
  Instrumentkennung und spätere native Venuekennung bleiben unterschiedliche
  Referenzen unter ihren bestehenden Instrumentprüfungen.
- Die vorhandenen fünf Originalreferenzen für Kapitalenvelope, Vor-/Nachrisiko,
  Sizing und Quantityprovenance gegen genau das übergebene Originalsizingsresultat.
  Ihre Originalfunktionen berechnen Referenzen; der Composer rechnet weder Menge
  noch Finanzrisiko neu aus.
- Die tatsächlich vorhandenen Parent-zu-Kind-Links order_intent_ref,
  risk_sizing_ref und quantity_provenance_ref samt ihren ursprünglichen
  BOUND_OFFLINE-Bindungsmarkern. Diese Marker bezeichnen die bestehende
  Bindungsart; sie werden nicht in produktive Risikoadmission oder Authority
  umbenannt. Der Originaldigestverbrauch bleibt getrennt von der Herkunft einer
  unabhängigen aktuellen Finanz- oder Marktquelle.

composed_epoch ist die bestehende Referenz der Komposition; creation_epoch gehört
zum späteren Envelope. Beide ersetzen die logische Eltern-Epoche nicht. Es gibt
keine neue gemeinsame Plan-TTL oder Regel, nach der jeder Cursorfortschritt
automatisch einen alten Plan unzulässig machen würde. Die positive Probe mit
weit entfernter composed_epoch belegt ausschließlich diese Trennung, keine
zukünftige Markt-/Betriebszulassung.

## Producer, Übergabe und nachgewiesene Wirkung

Der natürliche N1-Pfad liefert seinen wirklichen post-29P-Replay samt Parent,
Sizing und Intent an den vorhandenen Planbinder. Der zusätzliche Vergleich liegt
vor CoreLiveExecutionIntent und nativer Translation. Ein Widerspruch liefert
DENY und keinen Venueplan. Im bestehenden Predicate-Trace steht das konkret
geprüfte Parentprädikat; der Trace schafft keine zusätzliche Regelautorität.
Die bisherigen frühen Safety-, leeren Identity-, Duplicate- und expliziten
Caller-Epochensperren behalten ihre bisherige Fehlerpriorität.

Sechs Proben durch den tatsächlichen N1-/Supervisorpfad prüfen beide Seiten und
fremde Decision-ID, Epoche beziehungsweise entgegengesetzte Aktion. Es entsteht
kein Originalplanwrite und kein Budgetcommit des Sendeplans. Der ursprüngliche
Budgetowner gibt den noch nicht gesendeten Hold über seinen schon vorhandenen
Plan-Failure-Pfad frei. Es gibt keine neue Releaseberechtigung und keinen Eingriff
in SUBMIT_MAY_HAVE_OCCURRED, Permitverbrauch oder MAY_HAVE_SENT.

Der vorhandene Full-Close-Handoff behält seinen eigenen vollständigen Quellen-
und Positionsconsumer. Die neue ENTER-Prüfung wird nicht als alternative
Reduktions-/Closezulassung benutzt. Die originalen Close-/Positionsgrenzen
werden gesondert geprüft. Am tatsächlichen POST schützt die bestehende
Quellintegritätsoberfläche zusätzlich den Composer, Binder und die ursprünglichen
Decision-/29P-/29Q-/Mappingquellen; kein Baselinepin oder fremder Writer wird ersetzt.

## Verifikation, Quellenbindung und offene Fehler

[Originalconsumerfälle](../../../tests/ops/test_current_venue_plan_original_decision_parent_v1.py)
prüfen 32 neue Fälle. Der [datierte Nachweis](../evidence/CURRENT_VENUE_PLAN_ORIGINAL_DECISION_PARENT_2026_11_08.md)
bindet die finalen Ergebnisse und die getrennten Fehlbefunde. Der finale Ownerlauf
bindet zusätzlich die tatsächlich geladenen Repo-Pythonmodule: Ihre Hashes werden
vor dem Lauf aufgenommen und nach dem vollständigen Lauf erneut geprüft.

Eine separat erreichte ältere Kompositionssuite hat 25 FAIL und 11 PASS. Dieselben
25 fehlschlagenden Testadressen werden auch mit dem exakten ursprünglichen
Kompositionsowner der Basis reproduziert. Mehrere erwarten ENTER-/BLOCKED-
Strukturen, während ihre ursprüngliche Fixture NO_ACTION ohne Sizing liefert.
Ein weiterer unveränderter Venueplan-Dokumenttest erwartet einen entfernten
historischen Runbook-Header. Diese Fehler bleiben offen. Sie werden weder als
PASS gezählt noch durch neue Parentprüfungen oder einen Dokumentcheck ersetzt.
Auch die zwei zuvor ausgeklammerten Dokumentverträge, sieben älteren Collector-/
Account-Verträge und frühere breite Abnahmeschulden bleiben offen.

Die Prüfung gilt beim tatsächlichen Planaufruf. Ein später gespeicherter Plan
trägt weiterhin seinen ursprünglichen Intent und Venueplan gemäß
[Originalplanvertrag](ORIGINAL_PLAN_NATIVE_ORDER_POLICY_BINDING_V1.md). Dieser
Anschluss speichert keinen neuen vollständigen Coreparent im Budget und beweist
keine fortdauernde Zulässigkeit gegenüber späteren Core-/Risk-/Marktänderungen.
Vollständige aktuelle Admission, unabhängige Authority, signierte Recovery,
Legacyherkunft, vollständige Pending-Custody und autonomer Host bleiben offen.
S6 endet weiter PRE_EXTERNAL_EFFECT; MAX_POSITIONS_EFFECTIVE=1 und HOST_JOIN=False
bleiben. Kein neuer GET, Refresh, Retry, Finanzwert, operativer Safety-/Credential-
zugriff, Venuekontakt oder Dienststart gehört zu diesem Anschluss.
