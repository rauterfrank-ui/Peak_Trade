# Provenance / source registry

```text
DOCUMENT_CLASS=NON_AUTHORITATIVE_SOURCE_IDENTITY_REGISTRY
ARTIFACT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
SECOND_SSOT=false
MASTER_RUNBOOK_REMAINS_SOLE_SSOT=true
epistemic_class=SOURCE_IDENTITY_AND_PROVENANCE
```

Machine-readable twin: `manifests/source_identities.json`.

Git binding used for this collection (remeasured before worktree create):

```text
HEAD=origin/main=652c2cd4f9e91160a46b86f02014fd019ec33ca5
porcelain=empty
```

## Sources copied into this worktree (RAW_VERBATIM_EVIDENCE)

| Role | SHA256 | SIZE | Worktree copy |
|---|---|---|---|
| TARGET | `08ffe7bce3fd7aa94de20737c3bc1cf1721e08e719fc8d3d00d72e079f6a5092` | 1421764 | `evidence/.../desktop/PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md` |
| PRODUCT_A | `e5da88abc93108001f3a88736ea1503aabf84eb2b094bf4e204385b888729c91` | 36800176 | `evidence/.../desktop/PEAK_TRADE_FORENSIC_STEP21_PRODUCT_A_…json` |
| STEP17 | `f5bf2b0f17fef8a27b5bed8e8d905b1250fff37b6460cfb4e76a8ddbfca55f3a` | 34242423 | `evidence/.../desktop/PEAK_TRADE_FORENSIC_STEP17_…json` |
| STEP15 | `63829882310eac46f0eb45c1a95f959dc001b37aaff6a83bdb016117f7b47b83` | 35647 | `evidence/.../desktop/PEAK_TRADE_FORENSIC_STEP15_…md` |
| STEP13 | `ba1a7d843826b8c008003b46fc48e8aac390ba23e241bd18291db6ed56db40da` | 43022985 | `evidence/.../desktop/PEAK_TRADE_FORENSIC_STEP13_…json` |
| STEP9 | `53a0f29f480cf46bdb9c0a9cf25a15dd701fe9ecbe99e53f1f1822058d4fbdd8` | 43024636 | `evidence/.../desktop/PEAK_TRADE_FORENSIC_STEP9_…json` |
| STEP8 | `824f4c2c881989901bc022204d330ebec1f1db0fbdb822383a92fffcee348d7d` | 11209785 | `evidence/.../desktop/PEAK_TRADE_FORENSIC_STEP8_…json` |
| STEP30 tx | `98deeee7dd1a9b1bc1543403163499164dd94014d1713d9620f1e6d3969d68d9` | 134056 | `evidence/.../transcripts/STEP30_98277650-….jsonl` |
| STEP31 tx | `3d3445289cb20a001101fe5e6ed5c58d039e061b4ea9b3c2160b44a68312eed2` | 97751 | `evidence/.../transcripts/STEP31_bbaf1005-….jsonl` |
| STEP32 tx | `4f9e21e6dd0c6d6591a8ede29375896679ec1fddb2dbf4d9e3fb49f928a0c393` | 75575 | `evidence/.../transcripts/STEP32_2d0440a7-….jsonl` |
| POST32_READINESS tx | `61d04bb80c212ba8765e2e52f9a9538c1651bd4d7ffcb9ed2e5238237229894b` | 48558 | `evidence/.../transcripts/POST32_READINESS_95209de2-….jsonl` |
| DISCOVERY_CASE_2 tx | `09634aa84a684bdfe2f8e04d943a77d144869c28d9897e98cf303a365f5110f2` | 115580 | `evidence/.../transcripts/DISCOVERY_CASE_2_e17bf1e1-….jsonl` |
| PRIOR_PREWRITE tx | `d12a68d0b587c53acbaf4e28adc3e4667c4bdcf52dd50163c40e37a3cf029af7` | 103433 | `evidence/.../transcripts/PRIOR_PREWRITE_9516c97d-….jsonl` |

Desktop originals were **not** modified. Copies are labeled AUTHORITY=NONE.

## Sources bound in-repo (not duplicated under forensic/)

| Role | Class | SHA256 | Path in this worktree |
|---|---|---|---|
| MASTER_RUNBOOK | CANONICAL_AUTHORITY | `65f833565d64517eae496e4cb3289525573dd2d3387429ba8d4ddc189c5b8b98` | `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md` |
| MAP_OF_TRUTH | NAVIGATION_INDEX | `97f8d389fa93d36c09e53c65db21242a6c7f777d6f8d01531e73f6815074ee9d` | `docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md` |

Copying those into `forensic/` would look like a second SSOT / second Map. Binding is by SHA at this worktree checkout.

## Live transcript captured at end of materialization

The collection chat (`78a67012-…`) is copied at the **end** of this operation because it grows while files are written. See `manifests/source_identities.json` after final capture and `evidence/.../transcripts/` for `CASE_A_REVALIDATION_AND_COLLECTION_*`.

## Handover vs local evidence

The Owner handover is not complete evidence. Where handover and local identity disagree, local bound evidence wins. Established imprecisions (already adjudicated in the CASE_A revalidation, not newly invented here):

- Handover FORBID list is an incomplete subset of STEP15 (identity copy has 80 `FORBID_` lines).
- `independent_true=493` holds only under STEP15 P19 (`reason in {KR-8,KR-9} AND model_has_independent_bytes=true`).
