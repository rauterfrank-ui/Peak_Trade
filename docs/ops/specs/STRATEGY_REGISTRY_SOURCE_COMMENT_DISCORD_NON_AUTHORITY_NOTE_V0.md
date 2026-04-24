---
title: "Strategy Registry Source Comment Discord Non-Authority Note v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-24"
docs_token: "DOCS_TOKEN_STRATEGY_REGISTRY_SOURCE_COMMENT_DISCORD_NON_AUTHORITY_NOTE_V0"
---

# Strategy Registry Source Comment Discord Non-Authority Note v0

## 1) Purpose

This note documents a narrow strategy-authority reading rule:

Inline source comments near strategy registry entries are not authority sources.

They can be useful historical or developer context, but they do not override strategy governance, Master V2 boundaries, Double Play boundaries, readiness contracts, tiering rules, or explicit reconciliation tables.

## 2) Scope

This note applies to source-comment wording in and around the strategy registry and nearby strategy metadata surfaces.

It is docs-only.

It does not change:

- strategy registry entries
- `StrategySpec` fields
- strategy tiering configuration
- strategy runtime behavior
- strategy tests
- Master V2 behavior
- Double Play behavior
- live, testnet, paper, or shadow behavior

## 3) Source Comment Boundary

A source comment can explain intent, background, or an earlier interpretation.

A source comment must not be treated as:

- live readiness
- production readiness
- strategy promotion
- Double Play approval
- Master V2 approval
- evidence approval
- external signoff
- permission to trade
- permission to arm
- permission to bypass strategy tiering or reconciliation

If source-comment wording appears to conflict with a strategy contract, tiering configuration, reconciliation table, or Master V2 document, the conflict must be handled as a documentation or governance ambiguity, not as automatic authorization.

## 4) Registry Metadata Boundary

Registry metadata can support construction, discovery, documentation, and internal strategy classification.

Registry metadata alone is not sufficient to authorize:

- live trading
- testnet trading
- paper or shadow promotion
- Double Play use
- Master V2 handoff acceptance
- strategy readiness
- external signoff

Where registry metadata, tiering configuration, and Master V2 documentation disagree, the disagreement must remain visible until explicitly reconciled.

## 5) Relationship to Existing Strategy Authority Docs

This note is subordinate to the existing strategy authority and reconciliation documents:

- `STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md`
- `STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1.md`
- `STRATEGY_REGISTRY_TIERING_MV2_RECONCILIATION_TABLE_V0.md`

Those documents define the broader separation between strategy metadata, tiering configuration, Master V2 governance, and Double Play interpretation.

This note only clarifies that source comments do not create an independent authority layer.

## 6) Research and R&D Strategy Boundary

Research and R&D strategy surfaces should be retained when they have analytical or future-design value.

Retaining them does not make them live-ready.

Examples of useful research or R&D strategy material can include:

- cycle or signal research
- volatility-model research
- microstructure research
- meta-labeling research
- regime overlays
- strategy-profile drafts
- strategy evaluation notes

These materials can be kept, parked, or adapted later under Master V2-compatible governance. They must not be promoted through source-comment wording alone.

## 7) Safe Operator Reading

Safe reading:

- "A source comment may contain useful historical or developer context."
- "A source comment can point to something that needs reconciliation."
- "A source comment does not override strategy contracts or tiering governance."
- "A registry entry can help locate a strategy but does not itself authorize trading."

Unsafe reading:

- "The comment says this is live-ready, so it is approved."
- "The registry contains the strategy, so Double Play may use it."
- "The comment overrides TOML tiering."
- "The comment overrides Master V2 governance."
- "The comment is enough to promote or arm a strategy."

## 8) Required Handling of Comment Discord

When source-comment wording appears inconsistent with strategy authority documents, use this order:

1. Preserve the evidence of the mismatch.
2. Do not silently reinterpret the comment as authority.
3. Do not silently change registry or tiering metadata.
4. Classify the mismatch as `docs-only clarify`, `needs deeper audit`, or `adapt to Master V2 later`.
5. Only change code or configuration in a separately approved implementation slice.

## 9) Non-Scope

This note does not:

- fix registry metadata
- fix tiering configuration
- declare any strategy live-ready
- declare any strategy not useful
- remove any research strategy
- authorize Double Play selection
- authorize live, testnet, paper, or shadow behavior
- define performance requirements
- define evidence requirements
- replace the reconciliation table

## 10) Validation

For documentation-only changes to this note, run from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project's documented Python environment to execute the same scripts.
