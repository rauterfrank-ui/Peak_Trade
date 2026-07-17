# OBL_B05 ENTRY_EXIT Producer Side-Authority Decision v1

---
docs_token: DOCS_TOKEN_OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1
STATUS: PRODUCER_SIDE_AUTHORITY_AUDIT_COMPLETE
scope: read-only semantic authority decision, non-authorizing
LIVE_AUTHORIZED: false
ORDERS_ALLOWED: false
SCHEDULER_RUNTIME_ALLOWED: false
PRODUCTIVE_SIDE_EMISSION_CHANGED: false
BOLLINGER_SIDE_ACTIVATED: false
SEMANTIC_ACTIVATION_REQUIRES_SEPARATE_GO: true
---

> **Non-authorizing:** Closed-world audit and disposition for whether each
> `ENTRY_EXIT_EVENT_V1` producer may later emit explicit `entry_side`.
> This slice does **not** activate any producer, does **not** set
> `entry_side=LONG|SHORT` in productive code, and does **not** change DA,
> confirmation, composition, runtime, orders, or live.

## A. Verdict

| Feld | Wert |
|---|---|
| `SLICE_ID` | `OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1` |
| `BASE_SHA` | `5039a9666afefe8b5e18cca2d6be19ae3ded9bc2` |
| `PRODUCER_SIDE_AUTHORITY_AUDIT_COMPLETE` | `true` |
| `ENTRY_EXIT_OWNER_SET_CLOSED` | `true` |
| `PRODUCTIVE_SIDE_EMISSION_CHANGED` | `false` |
| `LEGACY_BEHAVIOR_UNCHANGED` | `true` |
| `BOLLINGER_SIDE_ACTIVATED` | `false` |
| `BOLLINGER_ENTRY_SIDE_DECISION` | `BLOCKED_AMBIGUITY` |
| `SEMANTIC_ACTIVATION_REQUIRES_SEPARATE_GO` | `true` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ENABLED` | `false` |
| `SSOT_JSON` | `config&#47;governance&#47;obl_b05_entry_exit_producer_side_authority_decision_v1.json` |

## B. Closed-world Owner-Liste

Kanonischer Encoding-Owner (einzige Runtime-Map):

`src&#47;backtest&#47;strategy_signal_suitability_agreement_adapter_v1.py::_ENTRY_EXIT_EVENT_OWNERS`

Geschlossene Menge (7):

1. `bollinger_bands`
2. `ecm_cycle`
3. `macd`
4. `mean_reversion`
5. `momentum_1h`
6. `my_strategy`
7. `trend_following`

Keine zweite Owner-Map. `supported_sides`, Suitability und Strategy-Name sind
**keine** Encoding- oder Side-Authority.

## C. Entscheidungsregeln (angewendet)

- ENTRY bedeutet niemals automatisch LONG.
- `cycle_signal_value=+1` ist keine Side-Authority.
- `supported_sides` ist keine Signal-Authority.
- Suitability `ENTRY→AGREE(LONG)` ist keine Producer-Authority.
- Strategie-Name oder ökonomische Intuition allein reichen nicht.
- Exit darf nicht als entgegengesetzte Entry-Side gelesen werden.
- Keine Reklassifikation zu `POSITIONAL_*` in diesem Slice.
- Default `entry_side=NONE` bleibt unverändert.

## D. Producer-Policy (Kurz)

| producer | class | disposition | activation eligible? |
|---|---|---|---|
| `bollinger_bands` | `AMBIGUOUS_OR_CONTRADICTORY` | `KEEP_NONE` | no (`BLOCKED_AMBIGUITY`) |
| `macd` | `AMBIGUOUS_OR_CONTRADICTORY` | `KEEP_NONE` | no |
| `momentum_1h` | `RATIFIABLE_PRODUCER_SEMANTICS` | `KEEP_NONE_PENDING_SEPARATE_ACTIVATION_GO` | yes (later GO) |
| `trend_following` | `RATIFIABLE_PRODUCER_SEMANTICS` | `KEEP_NONE_PENDING_SEPARATE_ACTIVATION_GO` | yes (later GO) |
| `mean_reversion` | `RATIFIABLE_PRODUCER_SEMANTICS` | `KEEP_NONE_PENDING_SEPARATE_ACTIVATION_GO` | yes (later GO) |
| `my_strategy` | `RATIFIABLE_PRODUCER_SEMANTICS` | `KEEP_NONE_PENDING_SEPARATE_ACTIVATION_GO` | yes (later GO) |
| `ecm_cycle` | `LEGACY_OR_SPECIALIST_ONLY` | `KEEP_NONE` | no |

Vollständige Felder: siehe SSOT-JSON (`producers[]`).

## E. Bollinger-Spezialentscheidung

`BOLLINGER_ENTRY_SIDE_DECISION=BLOCKED_AMBIGUITY`

Begründung:

1. Klassen-Doc sagt `1 (long)`; Methoden-Return sagt `1=entry`.
2. Decision D: `+1` unter `ENTRY_EXIT_EVENT_V1` ist ENTRY, niemals LONG.
3. `BaseStrategy` ABC beschreibt `±1` als Long&#47;Short-Position — widerspricht Encoding.
4. Registry `supported_sides=(long,short)` trotz long-only Code (kein Upper-Band-Short).
5. `-1` ist ausschließlich Middle-Band-EXIT, nie SHORT.
6. Keine Positionszustand-&#47;Order-Intent-SSOT außerhalb der Series.
7. Suitability `ENTRY→AGREE(LONG)` ist Consumer-Heuristik, keine Producer-Authority.
8. Lower-Band-Cross ist ökonomisch long-biased, aber der Producer-Contract definiert
   Positionseröffnung **nicht** eindeutig als kanonisches LONG unter Decision D.

Daher: **keine** LONG-Aktivierung in diesem Slice; `entry_side` bleibt `NONE`.

## F. Konflikt-&#47;Provenance-Tabelle (Index)

| id | surface | conflict |
|---|---|---|
| `CP01` | `BaseStrategy.generate_signals` | long&#47;short position vocab vs ENTRY&#47;EXIT |
| `CP02` | `bollinger.py` class vs method docs | `1 (long)` vs `1=entry` |
| `CP03` | registry `supported_sides` | capability vs long-only producers |
| `CP04` | suitability ENTRY→AGREE(LONG) | consumer eligibility ≠ producer side |
| `CP05` | macd binding test vocab | implies short vs EXIT-not-short |

Details: SSOT-JSON `conflict_provenance[]`.

## G. Spätere Aktivierungs-Slices (isoliert, separates GO)

Nur nach eigenem Operator-GO; jeweils ein Producer (oder Doc-Alignment zuerst):

- `OBL_B05_MOMENTUM_1H_ENTRY_SIDE_LONG_ACTIVATION_V1`
- `OBL_B05_TREND_FOLLOWING_ENTRY_SIDE_LONG_ACTIVATION_V1`
- `OBL_B05_MEAN_REVERSION_ENTRY_SIDE_LONG_ACTIVATION_V1`
- `OBL_B05_MY_STRATEGY_ENTRY_SIDE_LONG_ACTIVATION_V1`
- `OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1`
- `OBL_B05_MACD_ENTRY_SIDE_DOC_AND_TEST_ALIGNMENT_V1`

Homogene Sammelaktivierung ist **nicht** autorisiert.

## H. Owners

| Surface | Owner |
|---|---|
| Decision SSOT JSON | `config&#47;governance&#47;obl_b05_entry_exit_producer_side_authority_decision_v1.json` |
| Governance narrative | this document |
| Encoding owner map (reuse) | `src&#47;backtest&#47;strategy_signal_suitability_agreement_adapter_v1.py` |
| Static contract tests | `tests&#47;backtest&#47;test_entry_exit_producer_side_authority_decision_v1.py` |
| Parent carrier contract | `docs&#47;governance&#47;OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1.md` |
