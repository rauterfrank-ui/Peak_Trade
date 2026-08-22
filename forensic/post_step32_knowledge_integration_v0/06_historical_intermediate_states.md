# Historical / intermediate states

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_HISTORICAL_STATE_INVENTORY
ARTIFACT_AUTHORITY=NONE
epistemic_class=HISTORICAL_INTERMEDIATE_STATE
HISTORICAL_IS_NOT_CURRENT=true
FORBID_USING_HEADINGS_AS_CURRENTNESS_PROMOTION=true
```

Machine twin: `manifests/historical_state_inventory.json`.

These states remain recoverable. They are not the current structured
inventory. Deduplicating them into PRODUCT_A would destroy chronology
and, for STEP9, chrome that STEP15 says must not be treated as
nonexistent merely because a later preview omitted it.

| ID | SHA256 | Relation to current |
|---|---|---|
| STEP8 | `824f4c2c…8d7d` | earlier output candidate |
| STEP9 | `53a0f29f…bdd8` | production transformation; independent provenance |
| STEP13 | `ba1a7d84…40da` | preview; superseded as *current inventory* by PRODUCT_A |
| STEP17 | `f5bf2b0f…5f3a` | structured candidate immediately before PRODUCT_A |
| C01–C04, C06 | (in STEP30/31 transcripts) | rejected or blocked markdown candidates |
| M05A JSONL catalog-only | DISCOVERY | REJECT |
| PRIOR_PREWRITE CASE_A transcript | `d12a68d0…29af7` | first CASE_A report; not fused with later revalidation |

Closed numbered/post steps (STEP30–32, POST32_READINESS, DISCOVERY) are
historical *operations* whose results remain **binding**. Binding ≠
current TARGET rewrite.

Identity copies live under `evidence/raw_verbatim_identity_copies_authority_none/desktop/`.
