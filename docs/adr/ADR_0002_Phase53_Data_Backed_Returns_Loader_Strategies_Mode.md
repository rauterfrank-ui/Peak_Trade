# ADR 0002: Phase-53 data-backed returns loader for strategies_mode

- Status: ACCEPTED
- Date: 2026-04-15
- Deciders: Peak_Trade maintainers

## Context

For `portfolio_recipes.strategies` presets, the current strategies-mode robustness path still requires `--use-dummy-data`.

In `scripts/run_portfolio_robustness.py`, strategies-mode aborts without dummy data because no data-backed returns loader exists for this path. This means the current gap is not primarily documentation navigation; it is the absence of a defined contract for loading real returns for `strategies = [...]` presets.

The top-N robustness path already has a different loader story via existing loader/building-block patterns such as `build_returns_loader` and `load_returns_for_top_config`. That path does not, by itself, define the source-of-truth contract for Phase-53 strategies-mode.

Before implementing a loader for strategies-mode, Peak_Trade needs a narrow contract for:
- source of truth for one strategy entry's returns
- deterministic mapping from one preset strategy entry to one returns series
- validation expectations for loaded returns
- explicit failure behavior when source data is missing
- strict separation between data-backed mode and `--use-dummy-data`

## Decision

Peak_Trade will treat the missing Phase-53 strategies-mode returns path as a contract-first problem.

A future implementation slice must follow these rules:

1. **Source of truth**
   - One canonical source pattern must be chosen for data-backed returns in strategies-mode.
   - Candidate patterns include:
     - existing experiment/sweep artifact conventions
     - an explicit on-disk returns artifact directory
     - a registry-backed pointer to a returns artifact

2. **Identifier mapping**
   - One deterministic mapping rule must exist from a `strategies = [...]` preset entry to exactly one concrete returns series.
   - The mapping key must be explicit rather than inferred heuristically.

3. **Shape and validation**
   - Loaded returns must be a `pd.Series`.
   - The returned series must be non-empty, numeric, finite, and deterministically ordered.
   - Timestamp/index semantics must be explicit in the implementation slice.

4. **Failure behavior**
   - Missing data-backed returns for any requested strategy entry must fail explicitly with a clear error.
   - No silent skip behavior is introduced by default.
   - No silent fallback from data-backed mode to dummy mode is allowed.

5. **Dummy-data separation**
   - `--use-dummy-data` remains explicit and opt-in.
   - Data-backed mode must not degrade silently into dummy behavior.

## Implementation status

<!-- phase53 implementation status note -->

A manifest-backed `strategies_mode` returns-loader path is now implemented and documented.

Implemented follow-ups:
- `scripts&#47;run_portfolio_robustness.py` supports `--strategy-returns-manifest` for data-backed `portfolio_recipes.strategies`
- `src&#47;experiments&#47;strategy_returns_manifest_loader.py` provides manifest resolution plus explicit failure behavior
- `tests&#47;test_strategy_returns_manifest_loader.py` covers happy-path and negative-path behavior
- `docs&#47;PORTFOLIO_RECIPES_AND_PRESETS.md` documents the manifest pattern and CLI usage

## Consequences

### Positive
- The next implementation slice can stay narrow: one loader path plus one focused test.
- The contract reduces the risk of implementing a loader against the wrong source or wrong ID mapping.
- The strategies-mode gap is framed as a bounded research/robustness contract rather than a broad end-to-end redesign.

### Negative
- This ADR does not, by itself, close the Phase-53 top-gap.
- A follow-up slice is still needed to wire the chosen source pattern into `scripts/run_portfolio_robustness.py`.

## Acceptance criteria for the follow-up slice

A follow-up loader/test implementation slice should be considered correct only if:

- a documented canonical source of truth exists for strategies-mode returns
- one deterministic mapping rule exists from preset strategy entry to returns source
- missing source data fails explicitly
- no silent dummy fallback exists in data-backed mode
- the slice remains narrow:
  - one loader-oriented codepath
  - one focused pytest
  - zero live-path changes

## Alternatives considered

### 1. Implement a loader immediately without an ADR
Rejected because the repo currently lacks an agreed source-of-truth contract for strategies-mode returns.

### 2. Add a large new phase document first
Rejected because the gap is specific and implementation-adjacent; a large phase document would add breadth without reducing ambiguity enough.

### 3. Keep the gap only in `docs/DOCS_AUDIT_TRACKER.md`
Rejected because the tracker records the gap but does not define the contract needed for a safe narrow implementation slice.
