---
docs_token: DOCS_TOKEN_CURRENT_MF_N5_FULL_AUTONOMY_PRODUCTIVE_RUNTIME_ORCHESTRATOR_CONTRACT_V1
status: active
scope: Compose finished ranking handoff through occupied-lane N=5 joins to sequential PRE_EXTERNAL readiness without trading-decision or external-effect authority
capability: NONE
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-09-19
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
RUNTIME_ACTIVATION_ALLOWED: false
MULTI_FUTURE_RUNTIME_AUTHORIZED: false
SELECTION_AUTHORITY: false
ALPHA_ALLOWED: false
HARD_STOP: true
---

# CURRENT MF N=5 Full-Autonomy Productive Runtime Orchestrator Contract V1

```text
DOCUMENT_CLASS=DOCS_AND_TYPED_CONTRACT_NON_AUTHORIZING_PRODUCTIVE_FA_RUNTIME_ORCHESTRATOR
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
OWNER_GO_THIS_SLICE=OWNER_GO_PR2_FULL_AUTONOMY_PRODUCTIVE_RUNTIME_ORCHESTRATOR
CONTRACT_ID=CURRENT_MF_N5_FULL_AUTONOMY_PRODUCTIVE_RUNTIME_ORCHESTRATOR_CONTRACT_V1
SLICE_ID=PRODUCTIVE_FULL_AUTONOMY_N5_RUNTIME_ORCHESTRATOR
PRODUCTIVE_ENTRYPOINT=ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.run_productive_full_autonomy_n5_runtime_orchestrator_v1
HARNESS_JOIN_CHAIN_REPLACED=false
AUTONOMY_ORCHESTRATOR_STATUS=PRODUCTIVE_COMPOSE_IMPLEMENTED
AUTONOMY_TRADING_DECISION_AUTHORITY=false
FULL_AUTONOMY_TRADING_DECISION_AUTHORITY=false
FIRST_TRADING_DECISION_CONSUMER=run_current_productive_master_v2_runtime_cycle_v1
PORTFOLIO_BUDGET_OWNER=portfolio_capital_reservation_budget_v1
CRS_QUANTITY_OWNER=src.governance.capital_risk_sizing_v1
PORTFOLIO_RESTART_STATUS=FAIL_CLOSED_NO_UNPROVEN_RESTORE
TERMINAL_BOUNDARY=PRE_EXTERNAL_EFFECT_ORCHESTRATION_ROLLUP
AUTHORITY_EFFECT=NONE
RUNTIME_AUTHORIZATION_EFFECT=PRODUCTIVE_FA_RUNTIME_ORCHESTRATION_COMPOSE_ONLY
JOIN_RANKING_AUTHORITY=false
JOIN_SELECTION_AUTHORITY=false
JOIN_CAP23_SELECTION_AUTHORITY=false
JOIN_CAP24_BINDING_AUTHORITY=false
JOIN_TRADING_AUTHORITY=false
JOIN_EXECUTION_AUTHORITY=false
JOIN_FULL_AUTONOMY_HOST_AUTHORITY=false
MF_PRODUCTIVE_JOIN=false
HOST_JOIN=false
PRODUCTIVE_RUNTIME_CARDINALITY=1_UNJOINED
MAX_POSITIONS_EFFECTIVE=1
N_GT_1_ENABLED=false
MULTI_FUTURE_RUNTIME_AUTHORIZED=false
EXECUTION_SCHEDULE=SEQUENTIAL_LANE_ID_ORDER_NOT_CONCURRENT
EXTERNAL_EFFECT_AUTHORIZED=false
POST_ALLOWED=false
ATLAS_AUTHORITY=NONE
```

## Purpose

Single productive Full-Autonomy **orchestration** entrypoint that composes existing
`current_mf_n5_*` join owners from finished ranking/membership inputs through:

1. recovered topology / Cap23 / Cap24 / bound ingest / MV2+DP handoff
2. sequential occupied-lane governed cycles with shared portfolio budget owner (PR #6621 seam)
3. PRE_EXTERNAL host-join readiness rollup (optional N=5 completion rollup stays off by default)

Cap23 owns the selection, Cap24 binds the native instrument, Master V2 with
Double Play owns the trading decision, and the portfolio and sizing owners
control the reservation and final quantity. The orchestrator coordinates these
calls and rejects a readiness result that carries a permit or external effect.
The declared topology has five lane addresses. The current authority pins
allow one productive position and keep the five-lane host join disabled.

A multi-lane composition requires identified C1 payloads and bound
Mark/Index provenance for each selected instrument. Cap24 supplies the
selected instrument and its Mark sidecar. C1 history and the original Index
observation come from their own sources. An untagged, empty or failed C1
response blocks that composition before delivery to Master V2.

The sealed N1 consumer still takes a common bid, ask, volume, open interest
and funding rate. Multi-lane fixtures can exercise C1 and price identity
with that interface. Productive multi-lane admission requires instrument-
and time-bound inputs for those remaining fields to reach each lane's
market context independently.

Die Instrumentkarten und ihre Prüfergebnisse gehören zum Universum
**Master V2 Double Play**. Ihr Datenvertrag liegt in
`src/ops/master_v2_double_play_instrument_cards_v1.py`. Jede Karte und
jeder Prüfbeleg trägt diese feste Zugehörigkeit im Feld `owner_universe`.
Die Zugehörigkeit der Karte geht in ihren Inhaltsdigest ein.

Eine zugewiesene Karte übernimmt die vorhandene
`OccupiedLaneRuntimeInstrumentIdentityV1` mit Slot-ID, beiden
Instrumenten-IDs, Auswahlbezug und `instrument_epoch`. Das Ranking und
der bestehende Cap23-/Cap24-Auswahlpfad liefern die Zuordnung.
Der Offline-Consumer vergleicht die Karte mit den übergebenen
Slot-/Instrumentpaaren aus dieser Kette, einschließlich Ranking-Snapshot,
Rankingdigest und Universumsbezug.
Eine veraltete Bindung oder doppelte Belegung wird beim betroffenen
Kandidaten abgewiesen. Das Ergebnis führt Slot-ID und Generation weiter.
Vor einer Slotzuweisung bleibt die Karte nach Instrumenten-ID adressierbar.

Der Offline-Adapter `offline_candidate_cards_v1.py` verarbeitet die Karten
über den vorhandenen reinen Master-V2-Replay. Er bindet die native und
kanonische Instrumenten-ID an C1, Geld-/Briefkurs, 24-Stunden-Kontraktvolumen,
Open Interest in Kontrakten, Fundingrate und Mark-/Index-Provenienz.
Mess- und Erfassungszeit müssen zum geprüften Informationsstand passen.
Eine neue Quellenfassung erhält einen neuen Digest und ein neues Prüfergebnis.
Jeder Kandidat erhält sein eigenes Prüfergebnis. Nach einer Ablehnung werden
die übrigen Kandidaten weiter geprüft. Master V2 kann auch für vollständig
gebundene Werte auf keinen Einstieg entscheiden.

Der Offline-Beleg führt Karten-, Marktkontext-, GGE-Eingabe- und
Entscheidungsdigest. Der GGE-Digest wird ausgewiesen, wenn die im Replay
erzeugte Scope-Initialisierung zu diesem Kontext gehört und denselben
Geometriewert konsumiert. Die vorhandenen Tests nutzen synthetische Quellen.
Der Archivadapter `bind_archived_candidate_captures_v1` liest die vorhandenen
GET-Receipts mit ihren Originalbytes, prüft deren Hash und bindet ihren Inhalt
an die Karte. Die automatische Versorgung aus laufenden Paper-/Shadow-Sitzungen
und die produktive Übergabe der Karten sind noch offen.

Der Kartenadapter und sein Datenmodell sind im eigenen Beleg
`MASTER_V2_INSTRUMENT_CARDS_SEAL_V1.json` per SHA-256 eingefroren.
Das Lint Gate prüft beide Dateien und vergleicht spätere Änderungen mit dem
Siegel aus dem Zielbranch. Dieser Dateisatz hat den Autorisierungseffekt
`NONE`.

Implementation:
`src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py`

Constants:
`src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/constants_v1.py`

Tests:
`tests/ops/test_current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.py`
