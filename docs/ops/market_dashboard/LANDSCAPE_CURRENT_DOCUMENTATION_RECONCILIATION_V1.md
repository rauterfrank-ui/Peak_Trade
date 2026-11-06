# Landscape Current Documentation Reconciliation V1

```text
WP_ID=LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1
DOCUMENT_CLASS=CURRENT_NAVIGATION_AND_POINTER_RECONCILIATION
ATLAS_AUTHORITY=NONE
DASHBOARD_AUTHORITY_EFFECT=NONE
LANDSCAPE_CONSUMER_COMPLETE=true
CONNECTABLE_CURRENT_CONSUMER_GAP_COUNT=0
NEXT_ACTION=STOP_IDLE
RECONCILIATION_BASE_ORIGIN_MAIN_SHA=f3ced3c5ba146b6f7f26f7c6587fa44947270ee1
```

**Purpose:** Close factual documentation / ops-pointer drift after Landscape V2 consumer-closeout and post-closeout Presentation-Ops work (D2–D4). **Not** a new Landscape capability, trading change, or dashboard UI slice.

## Landscape consumer closeout (unchanged semantics)

| Field | Value |
| --- | --- |
| Consumer-closeout PR | **#6690** |
| Merge commit (short) | `b81d03a4e7169b20f212e8cf80bd581e96e19fc4` |
| Census artifact | `MARKET_DASHBOARD_LANDSCAPE_V2_CURRENT_COMPLETION_CENSUS_V1.md` |
| Census base SHA | `b81d03a4e7169b20f212e8cf80bd581e96e19fc4` (**historical evidence base**, frozen) |
| Completion status | `LANDSCAPE_CURRENT_COMPLETION_STATUS=COMPLETE` |
| Next Landscape action | `NEXT_ACTION=STOP_IDLE` |

## Post-closeout Presentation-Ops (separate from Landscape UI)

Archive → projection → MANIFEST handoff and bounded witnesses. **Does not** reopen Landscape consumer gaps (`CONNECTABLE_CURRENT_CONSUMER_GAP_COUNT=0`).

| PR | Merge commit (short) | Label |
| --- | --- | --- |
| #6697 | `62bbe577c` | D2: operational presentation materializer invocation |
| #6698 | `80700cb07` | D3.1: OKX universe/ranking readmodel regeneration witness |
| #6699 | `a0113e539` | D3.2: dynamic scope + canonical decision regeneration witness |
| #6700 | `6e095cd7a` | D3 remaining: universe refresh replay manifest integrity witness |
| #6701 | `d1b1ac898` | D4.1: risk/sizing/capital archive sibling export + presentation witness |
| #6702 | `642dcf7d6` | D4.2: execution/reconciliation archive sibling export + presentation witness |
| #6703 | `536c5d359` | D4.3: explicit STEP29M economic bundle archive binding |
| #6704 | `5dee5b679` | D4.4: safety archive sibling export + presentation witness |
| #6705 | `d30aef8d4` | MANIFEST finalize after readmodel sibling writes |

```text
POST_LANDSCAPE_PRESENTATION_OPS_MERGE_RANGE=#6697-#6705
POST_LANDSCAPE_PRESENTATION_OPS_LAST_MERGED_PR=6705
POST_LANDSCAPE_PRESENTATION_OPS_LAST_MERGE_SHA=d30aef8d4
```

## CURRENT origin/main documentation pointer

```text
CURRENT_ORIGIN_MAIN_DOC_POINTER_SHA=f3ced3c5ba146b6f7f26f7c6587fa44947270ee1
CURRENT_ORIGIN_MAIN_DOC_POINTER_NOTE=CRS historical-default deauthorization merge; no Landscape webui change
```

## Presentation runbook supersession (import-time vs CURRENT)

The ratification table in `PEAK_TRADE_CANONICAL_PRESENTATION_IMPLEMENTATION_RUNBOOK.md` at import / discovery SHA `6a9a3f10…` / `#5712` remains a **frozen inventory snapshot**.

As of `CURRENT_ORIGIN_MAIN_DOC_POINTER_SHA`:

- Governed operational materializer invocation exists (`CAPABILITY_PRESENTATION_PROJECTION_OPERATIONAL_MATERIALIZER_INVOCATION_V1`, PR **#6697**): `scripts/ops/run_operational_presentation_materializer_invocation_v1.py` → `run_operational_presentation_materializer_invocation_v1` → octet orchestrator (Owner-GO gated; `AUTHORITY_EFFECT=NONE`).
- Octet orchestrator CLI: `scripts/ops/run_presentation_projection_octet_orchestrator_v1.py`.
- Archive sibling exporters and D4 witnesses (#6701–#6705) prove bounded non-authoritative writes under operator archive roots; **not** automatic productive activation.
- Landscape dashboard remains `PURE_READ_ONLY_CONSUMER`; missing archive artifacts still correctly render `MISSING_SOURCE`.

Frozen discovery evidence (`market_dashboard_projection_octet_materialization_path_discovery_v1&#47;`) is **historical** at its recorded `origin_main_sha`; do not silently rewrite.

## Explicit non-claims

- No PR numbered **6711** exists on `origin/main` for this reconciliation scope (avoid ambiguous “post-6711” labels).
- Historical CRS fixture literals (25/500/100/10000) remain deauthorized for CURRENT productive paths (merge `f3ced3c5`); not reintroduced via dashboard docs.
- `adverse_exit_distance=80.0` is unrelated to deauthorized CRS sizing fixture defaults.
