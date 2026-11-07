---
docs_token: DOCS_TOKEN_PORTFOLIO_OWNED_EXECUTION_IDENTITY_V2
authority: NONE
runtime_authorization_effect: NONE
---

# Originalbudget: Planherkunft und Sendeversuch V2

Dieser neue, ausdrücklich versionierte Vertrag verbindet die vorhandene N1-
Planherkunft mit dem bestehenden Originalbudgetwriter, dem separaten tatsächlichen
Einmalpermit und dem vorhandenen Exchange-Reconciler. Er rekonstruiert keine
historisch schon vorhandene Attempt-Authority. Maßgeblich sind die verlinkten
Producer, Validatoren, Writer und Consumer, nicht dieses Dokument als Freigabe.

## Herkunft und Zuständigkeit

Der [N1-Producer](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
übergibt sein originales CanonicalOrderIntent und seinen VenuePlanCandidate beim
bereits bestehenden Envelopebind an den Originalbudgetowner. Der optionale
`plan_origin` wird im vorhandenen PLAN_BOUND-Link gespeichert. Sein Schema
`portfolio_execution_plan_origin.v1` und sein Trägerdigest sind neu.

Die [Quellprüfung](../../../src/ops/portfolio_capital_reservation_budget_v1/plan_origin_v1.py)
verwendet den ursprünglichen Intentvalidator, die ursprünglichen Finanzreferenzen,
den Envelopebinder und den Venuebodybuilder. Sie erhält alle Originalfelder strikt
ohne Nachfüllung beim Kaltlesen. Die Referenzen auf die gespeicherte Sizingentscheidung
werden geprüft; die bloße Trägerprüfsumme ist kein unabhängiger Echtheitsbeweis jedes
historischen Callerfeldes. Die Herkunft der natürlichen N1-Übergabe wird zusätzlich
am tatsächlichen Producer und seiner Rückgabe geprüft.

N1 erzeugt anschließend nur `PortfolioExecutionPlanContextV1`. S5 und S6 kopieren
dasselbe Objekt pro Cycle bis zur tatsächlichen Supervisor-Rückgabe. Fehlender
Kontext bleibt `None`; ein früherer Cycle liefert keinen Ersatz. Der Supervisor
schließt weiterhin seinen Owner. Der referenzierte Store bleibt erhalten, das
geschlossene Objekt erteilt kein Recht zur Fortsetzung. Eine spätere explizite
Verwendung benötigt denselben Originalstore und dessen frische Original-Recovery.

Erst `begin_execution_submit_v2` im
[Originalbudgetwriter](../../../src/ops/portfolio_capital_reservation_budget_v1/attempt_v2.py)
erzeugt die Attempt-ID beim Übergang PLAN_BOUND → SUBMIT_MAY_HAVE_OCCURRED. Die
Quelle ist die tatsächlich gelesene aktuelle Budgetrevision. Dieselbe ursprüngliche
SQLite-Transaktion schreibt die vollständige Identität und das tatsächliche Permit.
Ein eigener Attemptledger, eine neue Kapitalformel und eine Ersatzautorisierung
entstehen nicht. Das Budget bleibt interner Hold, kein bestätigter Börsenbestand.

## Semantik der erhaltenen Originalfelder

Der vollständige [CanonicalIntent](../../../src/governance/canonical_order_intent_v1.py)
behält seine ursprünglichen Feldbedeutungen:

- `intent_id`, `intent_version`, `decision_id`, `canonical_trading_logic_version`
  identifizieren Intent, Format, Originalentscheidung und Logikstand. Sie sind
  keine Sendeversuche. `instrument_id` ist die kanonische BoundInstrument-Kennung.
- `trading_epoch` bezeichnet den ursprünglichen fachlichen Entscheidungszeitbezug.
  Readback und Wiederaufnahme stempeln ihn nicht neu und bestätigen keine heutige
  Zulässigkeit dieser Entscheidung.
- `capital_envelope_ref`, `pre_sizing_risk_ref`, `sizing_result_ref`,
  `post_sizing_risk_ref` sind die ursprünglichen Referenzen auf Finanz- und
  Risikostufen derselben gespeicherten Sizingentscheidung. Ihre Berechnungen werden
  wiederverwendet, nicht durch neue Zahlen oder identisch benannte IDs ersetzt.
- `policy_digest`, `config_digest`, `implementation_digest`, `provenance_digest`,
  `semantic_digest`, `deterministic_serialization_version` erhalten die jeweiligen
  Policy-, Konfigurations-, Implementierungs-, Herkunfts- und Serialisierungsbezüge.
  Kein Digest ist eine unabhängige aktuelle Freigabe.
- `side`, `intent_action`, `position_effect`, `reduce_only`, `expected_position_side`
  behalten Richtung, Handlung, Positionswirkung und erwartete Seite. Diese Änderung
  verbindet ausschließlich die bereits zugelassene ursprüngliche ENTER-Planung.
  Ein späterer Fill oder tatsächlicher Positionswechsel folgt daraus nicht.
- `quantity` ist die originale Decimal-Kontraktmenge, `quantity_unit` hier CONTRACTS.
  `quantity_provenance` und `instrument_metadata_ref` binden deren ursprüngliche
  Berechnung und Instrumentmetadaten. Kontrakte, Coinmenge, USDC-Kapital und Preis
  werden nicht gleichgesetzt oder neu umgerechnet.
- `order_type_policy`, `price_policy`, `time_in_force_policy`, `max_slippage_policy`
  sind originale Entscheidungspolicies. Die Speicherung erneuert sie nicht und
  fügt keine neue pauschale Verfallsfrist hinzu.
- `execution_eligible`, `adapter_compatible`, `permission_required`,
  `submission_authorized`, `submission_effect`, `runtime_effect`, `authority_effect`,
  `network_effect`, `credential_effect`, `transformation_required`,
  `validation_status`, `reason_codes` bleiben ursprüngliche Status-/Grenzfelder.
  Die unveränderte Originalvalidierung bleibt zuständig. Speicherung macht einen
  plan-only Intent nicht direkt sendbar.

Beim [VenuePlanCandidate](../../../src/ops/full_core_live_path_composition_root_v1/models_v1.py)
sind `instrument_id` und `clordid` native Instrument- und Clientorderkennung.
`side`, `quantity`, `order_type`, `td_mode`, `reduce_only` und `venue_native_payload`
bezeichnen die exakten bereits transformierten Venuewerte. Die Menge ist weiterhin
die native Kontraktmenge als Dezimalstring. `quantity_source`, `side_source`,
`instrument_source`, `path_kind` halten ihre ursprünglichen Transformationsbezüge.
`environment` stammt aus dem ursprünglichen Orderumgebungsvertrag: LIVE, TESTNET,
SHADOW und PAPER_EXCHANGE sind verschiedene Identitäten.

Das [FinalOrderEnvelope](../../../src/ops/full_core_live_path_composition_root_v1/final_order_envelope_v1.py)
erhält alle exakten Orderfelder einschließlich `price`, `pos_side`, `td_mode` und
`reduce_only`. `price` ist der originale native Orderpreisstring in der Notierung
des Instruments; ein leerer Preis ist keine Nullpreisorder. `envelope_id` und
`envelope_digest` identifizieren den unveränderten kanonischen Envelopeinhalt.
`client_order_id`/`venue_plan_clordid` beziehen sich auf dieselbe originale Planung.
`quantity_source`, `side_source`, `instrument_source`, `path_kind`, `admission_ref`,
`provenance_ref` bleiben Herkunfts-/Pfadreferenzen. `creation_epoch` ist der
ursprüngliche Envelope-Erstellungszeitpunkt, keine heutige Admission und kein
Submitzeitpunkt. `issued_for_exact_action` und `schema_version` behalten den
ursprünglichen Envelopevertrag. Keine dieser Referenzen ersetzt die Permitbarriere.

## Reine Planreferenz

Alle sieben Felder von `PortfolioExecutionPlanContextV1` sind ohne numerische Einheit:

- `root`: aufgelöster Pfad desselben Originalbudgetstores; lokale Storeidentität,
  kein globaler Anti-Clone-Beweis.
- `account`: die bereits gebundene Originalkontokennung, nicht aus einem späteren
  gerade beobachteten Konto abgeleitet.
- `reservation_id`: genau die originale Reservation dieses Holds.
- `envelope_id`, `envelope_digest`: genau das gespeicherte ursprüngliche Envelope.
- `plan_origin_digest`: Prüfsumme des vollständigen neuen Herkunftsträgers,
  kein historischer Venueplandigest und keine Authority.
- `order_environment`: unveränderte Umgebung des Originalplans.

Der Consumer prüft Typ und alle Werte gegen denselben zugelassenen, offenen Owner
und dessen COMMITTED/PLAN_BOUND-Zustand. Die Referenz enthält weder Attempt-ID noch
Authority, hat keinen Ablaufzeitstempel und erneuert keine alten Marktdaten. Die
Kontextprüfung schreibt keinen Zustand. Beide direkten Venuewrapper verlangen
zusätzlich LIVE und lehnen gleichzeitige Legacyidentity plus Planreferenz ab.

## Neue dauerhafte Executionidentity

`PortfolioExecutionReconciliationIdentityV2` trägt explizit
`contract_id=PORTFOLIO_EXECUTION_RECONCILIATION_IDENTITY_V2`.
Ihre Felder entstehen aus den Originalwerten im selben Writer:

- `canonical_decision_id`: gespeicherte Reservationsentscheidung;
  `canonical_intent_digest`: originaler Intent-Semantic-Digest;
  `plan_origin_digest`: Digest des gespeicherten Herkunftsträgers.
- `decision_outcome`: hier explizit die originale Intenthandlung ENTER_LONG oder
  ENTER_SHORT; kein nachträgliches Wirtschaftsergebnis. `selected_side` ist die
  Originalintentseite LONG/SHORT. Der bestehende Reconciler verwendet die Seite zur
  Prüfung des Vorzeichens gefüllter Mengen gegen die bestätigte Position.
- `instrument_id`: kanonische Instrumentkennung; `native_id`: originale Venuekennung.
  Der originale GET-Provider fragt mit der nativen Kennung ab; der Budgetconsumer
  vergleicht die kanonische Kennung mit PortfolioTruth. Keine Gleichsetzung.
- `account_identity`, `execution_environment`, `venue`: ursprüngliches Konto,
  Originalplanumgebung und Venue des gespeicherten Kapitalscopes. Der GET-Provider
  und der Evidence-Reconciler binden Antworten an diese Identitäten.
- `envelope_identity`, `envelope_digest`: unverändertes Originalenvelope;
  `final_quantity`, `quantity_unit`: dessen exakte native Kontraktmenge als String
  und Einheit; `order_type`, `order_price`: dessen originale Orderart und Preis.
  Keine Kapitalbetrag- oder Gewinninterpretation.
- `clordid`: originale Clientorderkennung aus dem Venueplan. `exchange_ord_id`
  beginnt ausdrücklich mit `None`, weil noch keine Venueantwort vorliegt. Eine
  später gelesene Venue-ID wird als Reconciliationevidence gespeichert; sie
  verändert die ursprüngliche Attemptidentity nicht rückwirkend.
- `send_permit_id`, `send_authority_ref`: exakte Werte des tatsächlich übergebenen
  typisierten ExternalEffectPermit. Sie sind keine Umbenennung von altem
  Kapitalguard-GO oder dessen atomic_consumption_key. Ihre Speicherung beweist
  weder gesonderte unabhängige Authorityherkunft noch eine schon verbrauchte
  zweite Barriere.
- `submit_attempt_id`: im Originalwriter erzeugte UUID-Hexkennung (32 Zeichen) für
  genau diesen Unsicherheitsübergang. Keine Uhrzeit, Zyklusanzahl, Retryberechtigung
  oder globale kryptografische Echtheitsgarantie.
- `budget_owner_root`, `portfolio_reservation_id`, `slot_id`, `cycle_id`,
  `reservation_binding_digest`: Originalstore, Hold, ursprünglicher Slot/Cycle und
  Prüfsumme der ursprünglichen Reservationsbindung. Diese Strings erteilen kein
  neues Slot-/Kapital-/Permitrecht.
- `budget_source_sequence`: positiver ganzzahliger Revisionsordinal im Originalstore,
  einschließlich anderer Budgetschreibvorgänge; weder Handelsanzahl noch Zeit.
  `budget_source_digest` ist die Prüfsumme genau dieser tatsächlich gelesenen Zeile.
  `budget_submit_sequence` bezeichnet die tatsächliche unmittelbar folgende Zeile,
  welche SUBMIT_MAY_HAVE_OCCURRED und diese vollständige Identität dauerhaft trägt.
  Ihr Parentdigest muss auf die Quellzeile zeigen. Kaltlesen und Sendereadback
  prüfen beide echten Zeilen. Diese benannten neuen Bezüge ersetzen nicht still
  das opake Legacyfeld local_durable_state_version.

Der [versionierte Parser und Reconciler](../../../src/ops/full_core_live_path_composition_root_v1/full_core_exchange_reconciliation_v1.py)
erhalten V1 separat. Markerlose historische V1-Payloads bleiben nur bei exakt
passender V1-Feldmenge lesbar. V2 ohne Marker, mit fehlenden oder zusätzlichen
Feldern wird abgewiesen. Alte Stores erhalten weder neue Herkunft noch V2-Defaults.
Ein Rückwechsel auf alte strikte Reader kann scheitern; Daten und Holds dürfen
dafür nicht entfernt oder zurückgesetzt werden.

## Permit, tatsächliche Wirkung und Ausfallgrenzen

Das [bestehende Permit](../../../src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py)
behält `permit_id`, `envelope_id`, `envelope_digest`, `authority_ref`,
`issued_for_exact_action`, `schema_version`, `single_use`, `max_post_count`,
`retry_allowed`, `second_submit_allowed`, `standing_external_effect_authorized`
und `step_29q_status` unverändert. Es ist eine einzelne envelopegebundene Erlaubnis
im bestehenden direkten Wrappervertrag, kein stehender Hostauftrag.

Die tatsächliche [Sendenaht](../../../src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py)
behält die Reihenfolge Originalbudget SUBMIT_MAY_HAVE_OCCURRED → dauerhafter
Permitverbrauch SENT_INITIATED → K1/HTTP. Die Permitdatei erhält bei V2 zusätzlich
die vollständige originale Executionidentity samt eigenem Digest. Der Consumer
liest beide Originalbarrieren zurück und verlangt genau dieselbe Identität.
Der K1-Adapter prüft außerdem die exakte Permit-ID vor jeder Schlüsselabfrage.

Der [Permitwriter](../../../src/ops/full_core_live_path_composition_root_v1/external_effect_permit_durable_consume_v1.py)
serialisiert vorhandenes Lesen/Prüfen/Ersetzen pro Root mittels exklusivem lokalem
Dateilock. Gleichzeitige Writer erhalten BUSY oder CONSUMED; sie überschreiben
keinen gewonnenen Versuch. Kein zweiter Ledger entsteht. Die vorhandenen Felder
`post_count`/`max_post_count` zählen hier die beanspruchte Einmalsendung, nicht
bestätigte Börsenorders. `outcome`, `durable_state`, `consumed_at_utc` und
`completed_at_utc` beschreiben lokalen Verbrauch, lokales Ergebnis und lokale
Writerzeiten. COMPLETED ist kein Fill. Retry-/Resubmit-/Second-submit bleiben false.
Atomarer Dateiersatz und lokale Prozesskonkurrenz sind geprüft; Hostcrash,
physischer Stromausfall, globale Root-Eindeutigkeit und Anti-Clone sind nicht bewiesen.

Fehlender Commitnachweis oder fehlgeschlagener Budgetreadback sperrt den Owner.
Nach verlorener Commitbestätigung entscheidet ausschließlich Kaltlesen des
Originalstores, welcher Zustand tatsächlich vorliegt. Fehler zwischen beiden
Barrieren oder danach behalten den Hold und sperren blinden Retry. Ein abgebrochener
Testtransport wird nicht zu einem bestätigten Nie-gesendet-Nachweis umgedeutet.
Der vorhandene Budgetreconciler verwendet weiterhin TRANSPORT_UNKNOWN. Nur exakt
zugeordnete frische Venue-/Positions-/Pendingevidence kann den bestehenden
Releasevertrag erfüllen; offene, teilweise gefüllte, gefüllte oder ungeklärte
Ausführung gibt den Hold nicht automatisch frei.

## Nachweise und ausdrücklich offener Außenring

Die [Identityfälle](../../../tests/ops/test_portfolio_owned_execution_identity_v2.py)
verfolgen Long/Short vom tatsächlichen N1 über S5/S6, den geschlossenen Supervisor,
frische Original-Recovery, beide direkten Wrapper, Unsicherheit und Original-
Reconciliation. Die [Grenzfälle](../../../tests/ops/test_portfolio_owned_execution_boundaries_v2.py)
prüfen Commit-/Readbackfehler, beide Barrieren, fremde Referenzen, Konto/Umgebung,
gleichzeitige Writer und das Veto vor K1. Das sind synthetische Ports und temporäre
Stores mit gesperrten Sockets, kein belegter natürlicher Venuebetrieb.

S6 stoppt weiterhin bei PRE_EXTERNAL_EFFECT und komponiert keinen autonomen POST.
MAX_POSITIONS_EFFECTIVE=1 und HOST_JOIN=False bleiben erhalten. Aktuelle vollständige
Safety-/Risk-/Altplan-/Mengen-/Pendingzulassung, ursprüngliche unabhängige
Authorityherkunft, Session-/GET-Ressourcenbindung, Never-submitted-Recovery und
der fortgesetzte Hostauftrag bleiben eigene offene Anschlüsse. Dieser Vertrag
schließt nicht das Runbook A–H, fünf Slots, Double Play, Lernen oder Gesamtbetrieb.
