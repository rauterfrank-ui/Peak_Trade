---
title: "Strategy ECM and Armstrong Name Surfaces Non-Authority Note v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-24"
docs_token: "DOCS_TOKEN_STRATEGY_ECM_AND_ARMSTRONG_NAME_SURFACES_NON_AUTHORITY_NOTE_V0"
---

# Strategy ECM and Armstrong Name Surfaces Non-Authority Note v0

## 1) Purpose

This note documents the authority boundary for ECM and Armstrong-style cycle naming surfaces.

The goal is to prevent naming, epoch, or configuration drift from being misread as strategy readiness, live readiness, Master V2 authority, Double Play authority, or evidence approval.

## 2) Scope

This note is docs-only.

It does not change:

- strategy registry entries
- strategy implementation files
- strategy configuration
- strategy tiering
- strategy aliases
- strategy tests
- strategy runtime behavior
- Master V2 behavior
- Double Play behavior
- live, testnet, paper, or shadow behavior

## 3) Observed Name Surfaces

The current name surfaces include at least the following:

| Surface | Observed name | Role | Authority boundary |
|---|---|---|---|
| Strategy registry key | `armstrong_cycle` | Registered strategy identifier | Registry presence is not live readiness or Double Play approval. |
| Registry class mapping | `ArmstrongCycleStrategy` | Implementation mapping for the registered key | Mapping is not promotion or execution authority. |
| Registry config section | `strategy.armstrong_cycle` | Configuration section associated with the registered key | Config association is not readiness approval. |
| Strategy helper/module surface | `src/strategies/ecm.py` | Functional or historical ECM-related surface | File existence is not a separate registry key. |
| Config surface | `strategy.ecm_cycle` | Separate configuration-name surface requiring further audit | Config-name presence is not registry authority. |
| Strategy overview wording | `ECM` | Historical or example-oriented documentation label | Overview wording is not current registry completeness. |

This table is a reading aid. It is not a registry correction and not a naming migration.

## 4) Registry-Key Boundary

The observed registered key is `armstrong_cycle`.

This note does not create:

- an `ecm` registry key
- an `ecm_cycle` registry key
- an alias between ECM and Armstrong
- a naming migration
- a runtime compatibility layer

Any future alias, rename, registry change, or config migration requires a separate implementation design, tests, and review.

## 5) ECM Surface Boundary

ECM-related names can carry historical, mathematical, or helper-module meaning.

They must not be treated as:

- a separate live-ready strategy
- a hidden registry entry
- a strategy promotion signal
- Double Play authorization
- Master V2 handoff approval
- evidence approval
- an instruction to change tiering
- an instruction to execute a strategy

If ECM-related naming appears to overlap with Armstrong-related naming, the overlap must be treated as a naming and epoch issue until a dedicated audit resolves the relationship.

## 6) Wiring Status

The relationship between `src/strategies/ecm.py`, `strategy.ecm_cycle`, and the registered `armstrong_cycle` surface remains a needs-deeper-audit topic.

This note does not claim that the wiring is correct, incorrect, complete, unused, or redundant.

No code, registry, TOML, or runtime conclusion should be inferred from this note.

## 7) Master V2 / Double Play Boundary

Name alignment is not authority alignment.

Even if ECM and Armstrong naming are later clarified, that does not imply:

- live readiness
- testnet readiness
- paper or shadow promotion
- Master V2 readiness
- Double Play selection authority
- leverage approval
- external signoff
- evidence approval

Any future use of cycle-related strategy material in Master V2 or Double Play requires a separate adapt-to-Master-V2 design and review.

## 8) Safe Operator Reading

Safe reading:

- "`armstrong_cycle` is the observed registry key."
- "ECM-related surfaces exist and require naming/wiring interpretation."
- "The ECM and Armstrong relationship remains a read-only audit topic."
- "Historical strategy ideas can be retained without being promoted."

Unsafe reading:

- "ECM and Armstrong are automatically interchangeable."
- "`strategy.ecm_cycle` creates a registry key."
- "`src/strategies/ecm.py` proves a live-ready strategy."
- "The registry key implies Double Play approval."
- "This note authorizes an alias, rename, migration, or strategy execution."

## 9) Required Handling

When ECM / Armstrong naming appears inconsistent:

1. Preserve the mismatch.
2. Do not silently rename.
3. Do not silently add aliases.
4. Do not silently change registry or tiering configuration.
5. Classify the issue as `docs-only clarify`, `needs deeper audit`, or `adapt to Master V2 later`.
6. Only change code or configuration in a separately approved implementation slice.

## 10) Non-Scope

This note does not:

- implement an alias
- rename a strategy
- edit registry metadata
- edit TOML tiering
- edit config defaults
- delete ECM material
- delete Armstrong material
- declare any strategy live-ready
- declare any strategy Double Play-ready
- resolve performance or evidence claims
- run or validate any strategy

## 11) Validation

For documentation-only changes to this note, run from the repository root:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

If `uv` is not available, use the project's documented Python environment to execute the same scripts.
