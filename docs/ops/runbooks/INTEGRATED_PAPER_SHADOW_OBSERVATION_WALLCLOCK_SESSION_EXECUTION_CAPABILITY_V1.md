# INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1

```text
status: ACTIVE
capability: INTEGRATED_PAPER_SHADOW_OBSERVATION_WALLCLOCK_SESSION_EXECUTION_CAPABILITY_V1
owner: ops.integrated_paper_shadow_observation_wallclock_session_execution_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
economic_gate_effect: NONE
```

> **Technical wallclock capability — not productive authorization.**
> Implements fail-closed OKX-EEA public REST market-data observation with
> atomic authorization consumption, evidence, and PASS/FAIL/ABORT semantics.
> Repository defaults do **not** authorize a productive session.
> No real network was used to land this capability.
> No productive preregistration, Operator-GO, confirm token, or authorization
> artifact is created by this capability PR.

## Pipeline position

```text
… → PAPER_SHADOW_OBSERVATION_READINESS_PASS
  → OPERATOR_PAPER_SHADOW_OBSERVATION_GO
  → INTEGRATED_PAPER_SHADOW_OBSERVATION   # this capability (wallclock MD-observe)
  → INTEGRATED_PAPER_SHADOW_ECONOMIC_EVIDENCE
  → …
```

IPSO (`INTEGRATED_PAPER_SHADOW_OBSERVATION_SESSION_CAPABILITY_V1`) remains the
offline observation contract owner and stays non-executing by default.
This capability is the sole wallclock execution successor.

## Hard invariants

```text
orders_authorized=false
testnet_authorized=false
live_authorized=false
auto_promotion_authorized=false
credentials_authorized=false
paper_execution_authorized=false
ECONOMIC_VALIDITY_PASS=false
PROMOTION_PASS=false
network_scope=okx_eea_futures_public_md_observe_v1   # required when network_authorized
session_execution_scope=paper_shadow_observation_wallclock_v1
transport=rest_poll_v1
host=eea.okx.com
instrument=ETH-USD_UM_XPERP-310404
max_session_duration_seconds=21600
execution_class=ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION
```

## Authorization

Requires a verified bundle from
`PAPER_SHADOW_OBSERVATION_OPERATOR_GO_AND_SESSION_PREREGISTRATION_CAPABILITY_V1`
with exact network and session-execution scopes.
GO alone does not start a session.
Consumption is atomic and happens before the first network byte.
Consumed bundles are single-use; start failure after consumption is ABORT.

## Transport

- REST polling only (WebSocket out of scope)
- Host: `https://eea.okx.com`
- GET only; public paths allowlisted
- No credentials, no private endpoints, no orders

## Observation semantics

Reuses IPSO / shadow-no-order / Master-V2 decision→risk→safety composition and
analytical portfolio economics labeled
`ANALYTICAL_SIMULATION_NOT_PAPER_EXECUTION`.
This is not Paper Execution and not venue fills.

## CLI

```bash
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py preflight
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py verify-evidence --evidence-root <path>
python scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py run ...
```

`preflight` and `verify-evidence` are offline.
`run` delegates to the successor productive path
`INTEGRATED_PAPER_SHADOW_PRODUCTIVE_AUTHORIZATION_ISSUANCE_AND_REAL_NETWORK_EXECUTION_CAPABILITY_V1`
(verified non-fixture authorization required; real network additionally needs
`PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1`, which is never sufficient alone).
Library tests continue to inject fake transport and fake clocks.

## Datenprüfung für den Paper-/Shadow-Pilot

Der Shadow-Preflight prüft den lokalen Startpfad. Die Sitzung liest den
öffentlichen OKX-EEA-Markpreis für `ETH-USD_UM_XPERP-310404`. Der
Volatilitätsproducer benötigt 61 aufeinanderfolgende finalisierte
Minuten-Markpreise. Die reguläre I17-Qualifikation bindet 7.200 Sekunden in
Preregistrierung, Operator-GO und Wallclock-V2-Autorisierung. Der optionale
verlängerte Lauf bindet 21.600 Sekunden. Vor der einmaligen Nutzung der
Autorisierung prüft der Gatekeeper die genehmigte Dauer. Die Marktdatenprüfung
weist die 61 finalisierten Werte für den konkreten Lauf nach.

```bash
./scripts/pt scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py preflight
./scripts/pt scripts/ops/run_integrated_paper_shadow_observation_wallclock_session_v1.py \
  verify-evidence --evidence-root /absolute/shadow-evidence --require-typed-ddo
```

Die zweite Prüfung liest das versiegelte Sitzungsledger mit dem DDO-Owner
und dem Double-Play-Consumer. Sie verlangt mindestens einen Zyklus, in dem
der Core einen typisierten Volatilitätswert erhielt und das dazugehörige
Entscheidungsbündel vollständig wieder gelesen werden kann. Das JSON-Feld
`ddo_readback` meldet auch Schreibfehler und die Zahl der vollständigen
Bündel. Marktbeobachtung und analytische Fills in dieser Sitzung verwenden
einen Markpreis und modellierte Zusatzinputs. Die Wirtschaftlichkeitsprüfung
braucht separat gebundene Originalquellen für Quotes, Tiefe, Kosten und
Funding.

Der Bundle-Prüfer verlangt Prüfsummeneinträge für Marktsequenz, Zyklusledger,
Zähler, Abschlussurteil und inneres Integritätsmanifest. Die beiden
Manifestlisten müssen für die enthaltenen Dateien übereinstimmen.

Das Zyklusledger bindet die zugehörige Marktsequenz, Venue-Zeit, den
tatsächlichen Markempfang und die Zeit nach Empfang aller Zyklusinputs.
Die zugehörige Double-Play-Aufzeichnung erhält den Zykluszeitpunkt in UTC
mit Subsekunden. Diese Zeit beschreibt die für die Entscheidung verwendete
Host-Uhr; sie ist keine separat gemessene Dauer der Core-Berechnung.
O4 vergleicht UTC-Zeitpunkte einschließlich ihrer Nachkommastellen.

Die optionale O7-Anbindung an das Dashboard (`PEAK_TRADE_O7_LIVE_OHLCV_BRIDGE_ENABLED=1`)
braucht einen ausdrücklich gesetzten absoluten `PEAK_TRADE_STATE_ROOT`.
Vorprüfung und Laufzeitstart weisen einen fehlenden oder relativen Pfad ab,
bevor der Start die einmalige Autorisierung verbraucht. Ohne O7 benötigt die
DDO-Aufzeichnung nur das Evidenzverzeichnis der Shadow-Sitzung.

Paper verwendet eigene Evidenz- und Zustandswurzeln. Die lokalen
Roundtrip-Tests verwenden den Original-Core und simuliertes Accounting
mit einem DDO-Ledger je Slot. Der vorhandene Scheduler-Adapter mit
`high_vol_no_trade` deckt die Start- und Beobachtungsstrecke ab. Für den
Pilot mit simulierten Fills braucht es eine konkrete Bindung des
Paper-Starts an den Core, das Accounting und die vorgesehenen Datenprofile.
Der [Datenvertrag](../specs/CURRENT_PAPER_SHADOW_DATA_ROUTING_SEMANTICS_V1.md)
führt die zuständigen Eingangsconsumer und ihre Zeit- und Quellenbezüge.

Der [Paper-Vorcheck](../../../scripts/ops/prepare_bounded_paper_start_v1.py)
prüft am expliziten As-of die gespeicherten Facts durch die Ranking- und
C1-Consumer sowie die virtuelle Startbilanz im originalen Accounting.
Er öffnet keine Sitzung und meldet die offenen Startbindungen.

```bash
./scripts/pt scripts/ops/prepare_bounded_paper_start_v1.py \
  --data-profile /absolute/paper-data-profile.json \
  --virtual-accounting /absolute/paper-virtual-accounting.json \
  --run-root /absolute/new-paper-run \
  --native-instrument "$paper_native_instrument" --as-of-ms "$paper_as_of_ms"
```

Das Datenprofil enthält die fünf Zweckschlüssel und je Zweck die
serialisierte Ausgabe von `PurposeBoundPublicFactSourceV1.profile_v1()`.
Die Accounting-Datei enthält `initial_equity` und `contract` mit den
Feldern aus `ContractMetadataV1.to_dict()`. Menge, Multiplikator,
Tickgröße, Währung und Marginsätze stammen aus dem gewählten
Simulationsprofil. Ein erfolgreicher Input-Vorcheck ist ein Teilbefund.
Die Ausgabe `launch_blockers` führt die noch fehlende Hostbindung und
die Prüfung von Core-Marktinputs und Kosten auf.

Für die spätere [DDO-/GVEF-Auswertung](../specs/OFFLINE_DDO_NATIVE_RESEARCH_CYCLE_V1.md)
müssen die vollständigen Entscheidungsbelege erhalten bleiben. Die
Outcome-Messung benötigt mindestens zwei lückenlose finalisierte
O4-Stundenbars nach dem eingefrorenen Startzeitpunkt des Messfensters,
passend zu Venue und Instrument. Der vorhandene Offline-Follow-up-Worker
verwendet den Herkunftstyp `SYNTHETIC_OFFLINE`. Die Abnahme mit
beobachteten Originaldaten braucht einen eigenen Herkunftsnachweis über
die zuständigen Consumer. Forschungsprofil, finalisierte Backtestdaten
und aufgelöste Konfiguration bleiben explizite Eingaben.

## Explicit non-goals (this capability PR #5592)

- Productive preregistration / Operator-GO / confirm token issuance
  (owned by successor productive-issuance capability)
- Automatic session grant on merge
- Paper / Testnet / Live orders
- Economic Validity PASS
- Auto-promotion
- Dashboard authority
- Zero-Order as substitute

## Successor note

PR #5592 alone was not real-startfähig (`REAL_NETWORK_CLI_PATH_NOT_ENABLED_IN_THIS_PR`,
no productive issuance, no default real HTTP fetcher). The successor capability
supplies productive issuance and the real public-MD transport while keeping
Orders/Paper/Testnet/Live/credentials forbidden.

Decision→economics binding (non-HOLD, persistent portfolio, reconstruction
verifier) is owned by
`WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1`
(enabled by default in wallclock runtime config).
