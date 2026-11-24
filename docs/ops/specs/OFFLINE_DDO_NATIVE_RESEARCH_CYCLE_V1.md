# Offline DDO and native research cycle

## Fachliche Zuordnung und Nachweis am Consumer

Das Selbstlern-Universum umfasst DDO-Lernen und Meta-Learning. Das Optimierungsuniversum führt die übergeordnete Parametersuche aus und liefert gemessene Versuchsergebnisse zurück. GVEF prüft den erklärten Vergleich. Maßgeblich für die ursprüngliche Konstruktion sind insbesondere §§ 4, 12, 15, 18, 22 und 25 des [archivierten Learning Master Runbooks](../evidence/self_learning_original_layers_restoration_v1_2026_11_04/originals/self_learning_master_core_bound.original.txt).

1. **Originalentscheidung → spätere Messung.** Instrument, Sitzung, Zyklus und Decision-Referenz identifizieren die damalige Entscheidung. Im ETH-Paper-Lauf liefert eine abgeschlossene simulierte Position ihren Netto-PnL in der Quotewährung. Im ETH-Shadow-Lauf liefern zwei finale Stundenbars einen dimensionslosen Markpreis-Logreturn. Der Entscheidungszeitpunkt stammt vom Core. Die Bereitstellung der Marktdaten und der Eintritt in den Entscheidungszyklus haben eigene Zeitstempel.
2. **DDO → Selbstlernen → Optimierung.** DDO bindet das Outcome über Evaluation und Attribution an dieselbe Entscheidung. Der persistierte LearningState trägt den Evidence-Export. Die Optimierungsaufnahme prüft dessen Identität, Semantik und Zulässigkeit. Der Forschungsauftrag ergänzt Datensatz, Kenntniszeit, Strategieversion, Vergleichsbasis und Parameterraum. Das Maß für die spätere Kandidatenbewertung stammt aus der Ausführung dieses Auftrags.
3. **Optimierung → Meta-Learning → nächste Suche.** Die native Forschung speichert Parameter, Messung, Experimentidentität und Herkunft. Meta verarbeitet diese Versuchsevidenz mit der gespeicherten Policy. Die nächste Suche bindet eine tatsächlich verwendete Vorschlagsidentität. Bereits getestete Parameterbereiche werden zusätzlich als Suchabdeckung geführt. Ein neuer Parameterwert wird erst durch sein eigenes Ausführungsartefakt zum gemessenen Versuch.
4. **Versuchspaar → GVEF → Folgeversuch.** Die Evaluation bindet Baseline und Kandidat in ihrer Reihenfolge, Originalmessungen, Prüfplan, Softwarestand und erforderliche Domänenbelege. Der Kampagnenworker prüft die gespeicherte Entscheidung über die Fortsetzung. Ein mechanischer Pass erlaubt im gebundenen Profil genau eine weitere Suche. Deren Ergebnis kann eine Messung oder ein ausgeschöpfter Suchraum sein. Bei gesperrter Evaluation bleibt der Folgeversuch angehalten. Der [lesende Prüfer](../../../src/experiments/learning_research_chain_readback_v1.py) verfolgt diese Identitäten vor der Veröffentlichung des Kampagnenabschlusses und beim Wiederlesen.
5. **Kandidat → unabhängiger Shadow-Vergleich → Reality Gap → nächste Hypothese.** Hierzu braucht es dasselbe Experiment, vergleichbare erwartete und beobachtete Größen, Einheiten, Horizont und eine gebundene Bewertungspolitik. Der November-Paper-Beleg schloss den Vergleich des Gebührenmodells mit 5 Basispunkten auf beiden Seiten. Beim Shadow-Forschungsjob blieb dieser Teil offen. Ein Vorschlag oder ein mechanischer GVEF-Pass erteilt keine Freigabe für eine produktive Parameteränderung.

### Historische Referenz und Taktung

Die Paper- und Shadow-Läufe vom 14. November 2026 lieferten jeweils drei native Messungen und einen gemessenen Folgeversuch. Die Versuche umfassten die MA-Parameter 10/30, 10/40 und 10/20. Meta gab in beiden Jobs null Parameterempfehlungen aus. Die gespeicherte Suchabdeckung führte zu weiteren Versuchen. Ein separater [Kontrolltest](../../../tests/experiments/test_canonical_research_result_to_meta_input_v1.py) prüft bei gemessener Überanpassung, dass ein Vorschlag die tatsächliche Auswahl des Parameterbereichs ändert. Die Wirtschaftlichkeitsbewertung blieb gesperrt. Der separate Vergleich vom 15.–16. November lieferte technische Vergleichsevidenz bei null Fills. [Rekurrente Forschung #7276](https://github.com/rauterfrank-ui/Peak_Trade/pull/7276) · [Kandidatenvergleich #7277](https://github.com/rauterfrank-ui/Peak_Trade/pull/7277) · [Unabhängiger Shadow und Futures-Abrechnung #7281](https://github.com/rauterfrank-ui/Peak_Trade/pull/7281)

Der lokale LaunchAgent `de.peaktrade.offline-research.v1` ruft den Forschungsworker alle 300 Sekunden mit seiner gebundenen Kampagne auf. Eine isolierte Slotkampagne hat ihren eigenen Quell- und Zustandsbereich. Der GitHub-Workflow PR-J läuft laut Cron täglich um 16:23 UTC und prüft mit Fixtures die Shadow-/Paper-Bereitschaft. Beide Takte haben unterschiedliche Eingaben und Ergebnisse. [Workflow](../../../.github/workflows/prj-scheduled-shadow-paper-features-smoke.yml) · [Einrichtung #7286](https://github.com/rauterfrank-ui/Peak_Trade/pull/7286)

The entry point consumes a completed offline DDO plan and a bounded research
profile or request. It verifies the original DDO state and O4 measurement, exports
LearningEvidence and passes it to the canonical optimization intake. The intake
acknowledges evidence eligibility. The declaration supplies the strategy,
parameter regions, dataset and experimental context.

```bash
./scripts/pt scripts/ops/run_offline_ddo_learning_follow_up_v1.py \
  --root /absolute/offline-state --cycle case-2 research --plan-digest "$plan_digest" \
  --profile /absolute/profile.json --bars /absolute/bars.csv --config /absolute/resolved.json
```

Use `OfflineDdoResearchProfileV1` in the [research worker](../../../src/experiments/offline_ddo_research_cycle_v1.py).
A profile has the request fields except `learning_evidence_digest`. Set
`schema_version` to `offline_ddo_research_profile.v1` and supply `follow_up_times`
with `meta`, `search` and `measurement` in strictly increasing UTC order after
`times.evaluation`. The worker takes the learning digest and instrument from the
verified export, checks the declared instrument and recomputes the input hashes.
It saves the generated request with the profile digest and follow-up clocks before
measurement. Use a clean checkout and an isolated state root outside the repository.

For an explicitly bound two-trial request, use `--request`:

```bash
./scripts/pt scripts/ops/run_offline_ddo_learning_follow_up_v1.py \
  --root /absolute/offline-state --cycle case-2 export-evidence --plan-digest "$plan_digest"

./scripts/pt scripts/ops/run_offline_ddo_learning_follow_up_v1.py \
  --root /absolute/offline-state --cycle case-2 research --plan-digest "$plan_digest" \
  --request /absolute/request.json --bars /absolute/bars.csv --config /absolute/resolved.json
```

The first command returns the `content_hash` used as `learning_evidence_digest`
in the request. The request schema is
`OfflineDdoResearchRequestV1` in
[offline_ddo_research_cycle_v1.py](../../../src/experiments/offline_ddo_research_cycle_v1.py).

- Bind `instrument_id` to the canonical instrument in the exported outcome.
  Supply the source digests for the declared feature and strategy context.
- Supply finalized, timestamp-indexed bars for that instrument. The index is
  bar-open time, `is_final` is boolean and `bar_interval` declares the duration
  of one bar. `bars_known_at` is the declared UTC availability time of the
  complete dataset. Bind the loaded frame and resolved config with
  `native_research_input_hashes_v1`.
- The resolved strategy configuration supplies the reference parameters. Declare
  the first and next search axes, seed and explicit UTC clocks. The baseline
  search starts after the learning evidence was available and after the dataset
  was known. The next search starts after the first measurement and Meta step.
- Supply the observed gap dimensions and threshold-policy digest for the declared
  offline comparison context. Supply the protected digest baseline for the
  scoped GVEF replay. These are caller declarations and retain their provenance.

The worker persists the request and admission, measures the reference, and
runs up to one candidate per search. The first archived measurement feeds
both Meta and search coverage. Search records distinguish prior measured
coverage, failure dispositions and new proposals. Meta proposals influence
search priority when the canonical Meta policy emits them. The DDO outcome
remains lineage evidence. Native scores come from the supplied backtest data.

When both native measurements exist, GVEF retains both original numeric
packets and evaluates their join in the local self-learning domain. The GVEF
replay reference is the first native result. The backtest comparison
reference remains the measured configuration. The result keeps economic
qualification blocked and carries authority `NONE`.

In profile mode, the worker uses the verdict read from the persisted GVEF
receipt and records its follow-up decision under `follow-up-decisions` by receipt
ID. Mechanism `PASS` runs one further search with `next_axes`, a budget of one,
both archived measurements and the existing Meta and failure-memory policies.
The search can finish without a candidate. `BLOCKED` stops the search.
`INCOMPLETE` records a waiting decision and leaves the run open for a retry with
the same profile. A receipt that fails integrity verification stops the worker.
The follow-up and its measured artifact, when present, are returned under
`follow_up`. The economic verdict remains scoped to the evaluated pair.

Outputs are under the cycle directory inside `offline-ddo-research`. A retry
with identical bindings reads the original baseline, owner records and
receipts. A conflicting request for the same cycle is rejected. If either
search is exhausted, the result retains that disposition. An interrupted
native measurement whose original prepared request is missing stays fenced
by the native research owner.

## Recurring offline research

The [campaign command](../../../scripts/ops/run_recurrent_offline_research_v1.py)
performs one bounded tick. Schedule it with the host scheduler at the desired
interval. Each tick discovers finalized Paper archives and completed I17
follow-ups, checks their original evidence, and handles up to the configured
number of jobs. Each admitted learning digest gets one durable job and one
completion record. A retry uses the original paths, exact dataset and
configuration hashes, profile, original logical phase clocks, and selected
history. Blocked sources get a retry time.

The campaign file is local JSON. Set absolute canonical paths for `state`,
`paper_runs`, `shadow_runs`, and `shadow_follow_ups`. Set positive
`jobs_per_tick`, `retry_seconds`, and `history_jobs`. Map each canonical
instrument ID in `research_inputs` to a list of descriptors containing
`template`, `bars`, and `config` paths. Each template is an
`offline_research_input.v1` JSON object with `schema_version`,
`instrument_id`, `bars_csv_sha256`, `backtest_json_sha256`, and `profile`.
The profile uses the existing research profile fields. Set
`gap_dimensions` to an empty list and omit phase clocks. The tick supplies
phase clocks and the actual observed surface. New dataset versions have
distinct `bars_known_at` values. Keep previously selected files available
for restart. New jobs use the latest version already available at the tick.
With no eligible dataset, the source waits. The state is outside the repo
and source archives.

```bash
./scripts/pt scripts/ops/run_recurrent_offline_research_v1.py --campaign /absolute/campaign.json
```

- Paper uses the sealed original decision, fills and Accounting close. The
  learning horizon is `SIMULATED_POSITION_LIFECYCLE`. The research request
  retains net PnL as a decimal string in the original quote currency.
- Shadow verifies the original I17 archive, O4 archive and saved DDO state.
  The binding retains the Mark log return, start/end and bar count. The
  observation has no fills.
- The native provider measures the declared backtest CSV and config. A
  candidate inherits the learning digest as lineage. Meta reads prior
  measured packets of the same instrument and strategy version after the
  earlier jobs have completed. For an identical input descriptor and
  observation surface, the search counts already measured regions as
  covered, including receipts outside the current Meta window. A new
  dataset gets its own measurements.
- A Paper descriptor may supply `paper_fee_tolerance_bps`. The Reality Gap
  compares the backtest taker fee in bps with the original simulated fees
  divided by total simulated fill notional in the same quote currency.
  The comparison measures model parity. Without a comparable observation
  the gap step is `INCOMPLETE`.
- GVEF compares the two new native packets when both exist. Its mechanical
  verdict determines the bounded follow-up. Economic qualification and
  trading authority retain their existing owners. The campaign consumes
  saved observations and research datasets.

The saved Paper and I17 observations precede the new parameter candidate.
A candidate-specific Reality Gap requires a separate, later observation of
that candidate under a comparable measurement contract. The campaign records
exploratory feedback and leaves that comparative evidence open.

## Prospective candidate replay

The [candidate replay command](../../../scripts/ops/run_research_candidate_shadow_v1.py)
freezes both original numeric packets from a passing GVEF mechanism receipt.
It checks the strategy version, effective parameter values, original data
digest and resolved configuration of both packets before registering a
future UTC window. The first packet is the GVEF reference. The second is the
candidate under observation for this experiment. The later follow-up experiment
has its own identity.

```bash
./scripts/pt scripts/ops/run_research_candidate_shadow_v1.py --state /absolute/forward-state prepare \
  --campaign-state /absolute/campaign-state --learning-digest "$learning_digest" \
  --config /absolute/resolved.json --instrument-binding /absolute/instrument-binding.json \
  --start-utc "$window_start_utc" --hours 2
./scripts/pt scripts/ops/run_research_candidate_shadow_v1.py --state /absolute/forward-state observe
./scripts/pt scripts/ops/run_research_candidate_shadow_v1.py --state /absolute/forward-state verify
```

After the registered window closes, `observe` requests original finalized
hourly Last, Mark and Index candles and settled funding-rate history from
public OKX EEA endpoints. The original response bytes, endpoint, query and
receipt time are retained. Both profiles consume the same complete window.
The earlier warmup initializes each replay's simulated state and the existing
hourly research volatility feature. The score starts from the simulated equity
at the window boundary and uses candle-close timestamps. The funding series is
a market context input dated by the funding event. The replay result reports
engine equity before verified funding cashflows, with the execution cost model
from the original experiment, including the engine's closing convention.

This is a forward replay on newly captured market inputs. It records the actual
parameters consumed by the replay, the Master V2 engine signals and the
simulated equity series. The observations needed for an I17 candidate-specific
Reality Gap include which configuration the I17 decision producer actually used
and an independent measurement of the same metric. The replay receipt carries
`reality_gap_status=INCOMPLETE`, `economic_qualification_status=BLOCKED`, and
authority `NONE`. It has no promotion or apply consumer.

### Draft for an economic comparison

The [original self-learning master](../evidence/self_learning_original_layers_restoration_v1_2026_11_04/originals/self_learning_master_core_bound.original.txt)
specifies the sequence from candidate to Shadow evidence, Reality Gap,
research memory and the next hypothesis. GVEF binds the evidence for an
evaluation. The economic judgement needs a versioned owner policy.

The proposed primary metric is net return on beginning equity, measured for both
profiles over the same independent observation horizon. Use fees and slippage
from the measurement's accounting basis and reconcile funding against applied
position quantities and event times. Count each cost once. Specify the position
state at both boundaries, the settlement and price basis, and the unit. Pair the
candidate and reference observations by window and use the difference in returns.
Keep drawdown, sample sizes and an
uncertainty estimate with that difference. A two-hour observation can test the
data flow. The responsible owner must ratify the evaluation horizon, required
sample size, uncertainty method and pass thresholds before a quality claim.
Incomplete or incomparable evidence leaves the verdict `BLOCKED`.

### November 15 candidate comparison evidence

Both archives bind MA 10/30 and MA 10/40 to the same OKX ETH-X-PERP
instrument and USD settlement. The forward replay window was 00:00–02:00
CET. Both profiles produced two neutral hourly engine signals and a 0.00%
modelled equity return before verified funding cashflows. The replay result
body digest is
`5aef5b589331e97ff237cc44b051eb16bfc743f417120248a4c97fd69ab4ff90`.
The recorded funding rates describe market events. An applied cashflow also
requires the position quantity and accounting entry at the event.

The 17:01–19:01 CET I17 Shadow observed 3,007 distinct Mark events.
The two profiles differed in 1,496 raw MA outputs. Both profiles recorded
the same intended action, `NONE`, throughout the window. The paired
bridge ledger SHA-256 is
`231ddecb043b6ae1b8cf15c6e90d544c036e63ef59888520a05f692274579e15`.
The paired analytical equity was constant and the sealed fill ledger was
empty. The I17 reconstruction verifier reconciled the session at zero
fills. The session verdict retained `economic_validity_pass=false`.

SL05 requires comparable economics, including the horizon, model and risk
bindings. SL07 compares an expected and observed measurement of the same
profile. A difference between the two profiles on one surface alone
answers the separate candidate comparison question. This evidence leaves
the economic comparison blocked and the Reality Gap incomplete. A
decision-bound chain through position state, simulated execution and
accounting per profile is still required to measure the proposed return.
The [SL07 consumer](../../../src/experiments/canonical_reality_gap_store_v1.py)
also requires a versioned metric, unit, threshold policy and evidence references.

## Historical I17 candidate comparison

The [I17 comparison command](../../../scripts/ops/run_i17_candidate_comparison_v1.py)
revalidates the frozen GVEF pair and the original sealed I17 decision and
market ledgers. It runs the existing I17 observation bridge twice, starting
each profile in its own local state. The strategy registry in both runs
contains the same canonical `ma_crossover` entry. Both runs use the same
recorded Mark observations, original decision times and I17 safety inputs.
The market observation acceptor evaluates the archived venue event time and
Mark for the same instrument in both arms. A repeated event with a new receive
time does not advance the market observation epoch. The direction confirmation
owner consumes this accepted observation through the integrated replay and
retains its own Long and Short progress separately for each profile.

```bash
./scripts/pt scripts/ops/run_i17_candidate_comparison_v1.py \
  --state /absolute/i17-comparison --pair-plan /absolute/forward-state/plan.json \
  --campaign-state /absolute/campaign-state --base-config /absolute/resolved.json \
  --i17-evidence /absolute/qualified-i17/evidence --capture-public-last
```

The optional capture performs one public OKX EEA request for finalized hourly
Last candles and retains the original response and capture times. Replace
`--capture-public-last` with `--verify` to recompute the result from the saved
inputs. For each cycle, the MA uses only candles that had closed by the
original decision time. The hourly candle index and I17 decision epoch are
different coordinates. The receipt records both, the market observation
epoch and classification, directional confirmation progress, and the strategy
parameter and signal digests. It records the actual Suitability output when
that owner is reached, the decision reasons and the Double Play outcome. The bridge reads the same existing governed parameter
seam for both arms. The comparison carries authority `NONE`.

The hourly Last data was retrieved retrospectively. This fixture shows
historical decision behavior under the specified profiles. A prospective
I17 observation requires the profiles and candle availability to be bound
before the decisions under study, followed by independent, comparable
measurements for any Reality Gap.

### I17 decision-time input preflight

The same command accepts `--decision-time-last-captures` in place of
`--capture-public-last`. Supply a separate sealed JSON archive with schema
`i17_decision_time_last_captures.v1`, the frozen `plan_digest`, the
`original_i17_manifest_sha256` and an ordered `captures` array. Each entry
keeps the request, raw response, response hash, and request and receipt times
in the Last-candle archive format. Use captures that extend a contiguous
prefix of finalized Last hours. Earlier warmup bars must agree where they
overlap.

Both profiles and their research input must be known at preregistration
before the window opens. The I17 mark archive must lie inside that window.
Each decision uses the latest finalized hour from the captures received by
its own decision time. While a just-closed candle is in transit, both arms
continue with the previous available hour. The preflight stops if the first
decision has no available warmup. Each cycle records the selected close time,
receipt time and capture digest along with the consumed strategy material.
`--verify` replays the same inputs and checks the stored result.

The Last-candle capture entry point is `capture_decision_time_last_v1`.
It takes an isolated archive, the frozen plan, the intended I17
preregistration scope digest, an explicit transport and a UTC clock. It
stamps the request and receipt around the transport call, validates the
finalized OHLCV and both MA warmups, and stores one immutable response per
hour. A repeated request for that hour reads the saved response.
`seal_decision_time_last_v1` checks the original I17 manifest and the scope
bound by its preregistration, then writes the archive consumed by
`--decision-time-last-captures`. The comparison verifies the scope again.

This mode reads archived evidence offline and emits
`I17_DECISION_TIME_OFFLINE_PREFLIGHT` with authority `NONE`.

### I17 host comparison

An I17 host can receive an explicit `I17CandidateHostObservationV1` bound to
the frozen plan and its local Last-capture journal. The preregistration's
strategy components must carry the plan digest produced by
`candidate_plan_component_v1`. The existing preregistration scope digest binds
that identity before authorization consumption. A mismatched plan or a
candidate preregistration without its observer stops at preflight.

The observer consumes the host's Mark event and natural receipt time. It
reads the scoped journal and stamps its own paired decision cutoff. Both
profiles then use the latest available finalized Last prefix. The canonical
market observation acceptor handles event identity, and each arm retains its
own direction confirmation and simulation state. The MA value enters
Suitability. The receipt records that owner's actual response when reached
and the subsequent Double Play outcome. Each paired receipt in the bridge
cycle ledger references the original host decision, the original Mark clocks
and the Last close and receipt clocks.

The host also retains `simulated_economics` per profile in the sealed bridge
cycle ledger. This carries the arm's original cycle, decision, risk and
intent identities, the simulated fill where present, and the resulting
position and accounting state. The portfolio hashes identify the pre-cycle
and post-cycle states. The model digest and parameters identify the modelled
fees, slippage and funding. These values belong to the analytical simulation.
Venue funding cashflows and SL07 comparability still require their own
evidence. The historical comparison receipt keeps its existing format.

The [productive observation CLI](../../../scripts/ops/run_integrated_paper_shadow_productive_authorization_issuance_and_real_network_v1.py)
accepts the same sealed `--candidate-plan` at token issuance, preregistration
and run. Set `--earliest-start-unix` explicitly and keep the planned session
inside the frozen plan window. The run also takes a separate
`--candidate-journal` directory. The existing session-bound operator GO and
authorization consumption gate apply before the transport opens.

The candidate session admits only the additional public OKX EEA GET for
ETH-X-PERP Last candles with a UTC-aligned one-hour cutoff. The first poll
loads the previous completed hour before requesting the Mark price. Later
polls capture the newly closed hour and retain the earlier available prefix
while a new candle is unavailable. A failed candle-data validation pauses
capture retries for 15 seconds. The transport's authorization, network and
rate-limit boundaries apply to this request.

Missing initial Last evidence marks the candidate comparison failed for that
session. The ordinary Shadow observation continues through its owners when
the Last data is missing. The comparison carries authority `NONE`.
Economic qualification also requires a comparable measurement.

### Offline readback of simulated I17 accounting

Use the same original GVEF plan, campaign and resolved config with a completed
I17 candidate observation archived with per-profile `simulated_economics`.

```bash
./scripts/pt scripts/ops/run_i17_candidate_comparison_v1.py --host-economics \
  --state /absolute/i17-accounting --pair-plan /absolute/forward-state/plan.json \
  --campaign-state /absolute/campaign-state --base-config /absolute/resolved.json \
  --i17-evidence /absolute/qualified-i17/evidence
```

The readback checks the sealed host archive, the preregistered profile plan
and the original Mark and decision clocks. It applies the archived intents
to the existing isolated analytical portfolio model for each profile. The
calculated fills, fees, slippage and per-cycle portfolio states must match the
sealed records. The resulting `host-economics.json` binds the archive, plan,
model, code revisions and decision window to the reconstructed states. Add
`--verify` to rebuild the result and compare it with the saved receipt.
Archives without the per-profile records fail before a receipt is written.

The receipt carries the analytical portfolio's accounting units and modelled
funding. Its prices and position state support archival reconstruction.
The analytical portfolio multiplies quantity by price without the venue
contract size and debits purchase notional from cash. Its equity is an
analytical trace.

Add `--paper-terms-evidence` with the path of the sealed Paper archive to rebook
the same archived actions with the existing futures fill builder and accounting owner.
The original Paper profile supplies the explicit contract and margin terms.
Its instrument, contract size, lot, tick, settlement currency and leverage
must agree with the instrument metadata bound to the GVEF plan. Candidate
cycles retain the original typed order intent when it exists. Opening fills
require that intent's native contract quantity. A position-derived exit can
reduce the verified position according to the futures owner's size and side
checks. Missing opening quantity provenance prevents a futures receipt.
The separate `host-futures-accounting.json` records the source manifest and
contract digests and the resulting futures portfolios in settlement currency.
The archived decision sequence itself stays fixed during this rebooking.

Add `--funding-evidence` with the original `public-input.json` for the same
frozen plan to also book funding in that replay. The reader checks the
original endpoint, query, response hashes and post-window capture times. The
history page must reach the window start and supplies the timestamps and
realized rates. Settlement frequency follows the archived events. The
simulated price basis is the finalized hourly OKX Mark candle whose close
coincides with the funding timestamp.

Each archived settlement from the first through the last observed decision
uses the native contracts held immediately before it. A fill with the same
timestamp follows the funding event in the simulation. The existing futures
accounting owner posts the signed amount once per instrument and event. The
separate `host-futures-funding.json` retains the realized rate, price basis,
position side and size, applied fill references and source and knowledge
times. An incomplete history or missing finalized settlement Mark stops
before the funded receipt is published. Rates acquired after the window
are used only for this later rebooking.

The funded receipt leaves the economic qualification blocked and the Reality
Gap incomplete. The booking uses the specified simulation basis. SL07 still
requires a comparable expected measurement and a versioned threshold policy.
See the [OKX funding history API](https://www.okx.com/docs-v5/en/#public-data-rest-api-get-funding-rate-history),
the [linear contract funding basis](https://www.okx.com/en-eu/help/funding-fee-mechanism-eea)
and the [adjustable settlement schedule](https://www.okx.com/en-eu/help/perps-funding-fee-mechanism).

### Backtest valuation on the I17 accounting basis

Use `--backtest-economics` with the sealed decision-time Last archive,
Paper terms and the frozen plan's public funding evidence.

```bash
./scripts/pt scripts/ops/run_i17_candidate_comparison_v1.py --backtest-economics \
  --state /absolute/i17-backtest --pair-plan /absolute/forward-state/plan.json \
  --campaign-state /absolute/campaign-state --base-config /absolute/resolved.json \
  --i17-evidence /absolute/verified-market-tape/evidence \
  --decision-time-last-captures /absolute/scoped-last/captures.json \
  --paper-terms-evidence /absolute/sealed-paper-archive \
  --funding-evidence /absolute/forward-state/public-input.json
```

The sealed I17 archive verifies market events and their original decision
clocks. The backtest recomputes the two decisions on those market inputs
with separate replay states. Each decision uses the latest finalized Last
prefix available at its cutoff. Observed actions and fills do not feed
the replay. The same futures-accounting owner used for host readback
handles the replayed fills and settled funding.

Both receipts include net change in equity divided by beginning equity,
a flat opening state, terminal Mark valuation of any open positions,
and model, decision-configuration and governed-seam digests. The backtest
receipt also binds its tape and scoped Last archive. It writes
`backtest-futures-funding.json` and supports deterministic `--verify`.
This is a window-specific expected value. SL07 still needs the independent
observation, admission of matching measurement conditions and the
versioned threshold policy before producing a Reality Gap record.

### Prepare comparable I17 measurements for SL07

Freeze the funded backtest receipt before registering the later Shadow plan.
Pass the versioned policy JSON as `--reality-gap-policy` to the existing
`prepare` command. The plan stores its digest, and the I17 preregistration
scope already binds the plan digest. Use a new forward-state directory for
the later window.

The `i17_reality_gap_policy.v1` JSON includes `schema_version`,
`registered_at_utc`, `expected_plan_digest`, and `expected_receipt_digest`.
Use the `sha256` fields of the original plan and backtest receipt envelopes.
Declare the UTC bounds with `expected_window_start_utc`,
`expected_window_end_utc`, `observed_window_start_utc`, and
`observed_window_end_utc`. Declare `minimum_cycles`,
`minimum_fills_per_profile`, `max_boundary_skew_seconds`, and
`max_abs_net_return_gap`. The windows must have equal planned duration.
The threshold is an absolute difference in net-return fractions, so a
fraction of 0.01 represents one percentage point.

After the later Shadow has its own funded host readback, prepare the dimensions.

```bash
./scripts/pt scripts/ops/run_i17_candidate_comparison_v1.py reality-gap \
  --state /absolute/i17-gap-inputs \
  --expected-plan /absolute/backtest-plan/plan.json \
  --pair-plan /absolute/later-shadow-plan/plan.json \
  --expected /absolute/i17-backtest/backtest-futures-funding.json \
  --observed /absolute/i17-shadow/host-futures-funding.json \
  --policy /absolute/reality-gap-policy.json
```

The reader verifies the precommitment, distinct observation sources,
actual coverage, sample bounds, and matching profile, model, contract,
currency and valuation semantics. It checks the equity arithmetic and
emits one typed `pnl` ratio dimension per profile in
`i17-reality-gap-inputs.json`, with policy and source digests. Run the same
command with `--verify` for deterministic readback.

A durable record still belongs to the
[canonical SL07 store](CANONICAL_REALITY_GAP_STORE_V1.md) and requires an
exactly bound complete experiment record. The next research iteration may
consume a gap after that owner records it under a compatible identity.

### Rückgabe einer späteren gepaarten Messung

Eine neue Forward-Präregistrierung mit Reality-Gap-Policy bindet ihre Ursprungskampagne. Der reguläre I17-Schritt `reality-gap` publiziert nach erfolgreicher Dimensionsprüfung je Profil den SL07-Record. Bei historischen Plänen kann der Aufruf das Ziel mit `--campaign-state` angeben. `--verify` bleibt lesend. Paket, vollständiges Experiment, Parameter, Policy und Wissenszeit identifizieren den Vergleich. Eine Schwellenüberschreitung erzeugt einen gebundenen Failure-Memory-Record. Erst wenn beide Profile vollständig gespeichert sind, wird die Übergabe sichtbar.

Der nächste Forschungsjob friert die verfügbaren Übergaben für seine ausgewählte Experimenthistorie ein. Meta erhält die Originalmessungen und spätere Gap- und Fehlereinträge. Kostenbefunde verwenden die typisierte Kostendimension und ihre Modellidentität. Ein PnL-Gap allein erlaubt keine Attribution an Gebühren. Parameter- und Hypothesenvorschläge werden am Suchkandidaten gebunden. Ein Modelluntersuchungsauftrag trägt den Zielmodelldigest und kann mit dem passenden F2-Szenarioarchiv untersucht werden. Die tatsächliche Auswahl und ihre Messung bleiben am Such- und Ausführungsrecord nachlesbar. Bei einem ausgeschöpften Suchraum bleibt das Ergebnis erschöpft.

Bei einem Meta-Vorschlag zur Kostenuntersuchung speichert der Worker die nächste Forschungshypothese unter `cost-hypotheses` mit Vorschlag, Meta-Identität, Instrument und Lernquelle. Die optionale Kampagnenzuordnung `cost_grids` führt vom Zielmodelldigest zum F2-Archiv (`archive`) und zu dessen `execution_digest`. Sobald ein passendes Archiv vorliegt, berechnet der bestehende F2-Consumer beim Kampagnentick das OOS-Szenarioergebnis. Bis dahin bleibt der gebundene Untersuchungsauftrag offen.
