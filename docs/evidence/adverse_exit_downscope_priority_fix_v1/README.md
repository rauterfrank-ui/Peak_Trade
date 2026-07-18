# Adverse Exit / Downscope Priority Fix v1

```text
SLICE=ADVERSE_EXIT_DOWNSCOPE_PRIORITY_FIX_V1
BASE_MAIN=d740ca27689bb2331d2a6d68e1b52ff748bb2adf
PR_5339=MERGED (squash) @ d740ca27…
BRANCH=fix/adverse-exit-downscope-priority-v1
PRODUCTIVE_FILES_CHANGED=true
STATUS=PASS
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
LIVE_AUTHORIZED=false
ORDERS=false
```

## Phase A

PR #5339 squash-merged to `main` after evidence-only / required-check verification.
Merge SHA: `d740ca27689bb2331d2a6d68e1b52ff748bb2adf`.
Remote audit branch deleted. Foreign untracked / stashes untouched.

## Phase B Verdict

Dual-dimension transport restored:

- Generator prefers `DOWNSCOPE`/`UPSCOPE` over `ADVERSE_EXIT` for the SM-facing scope kind.
- Adverse remains in `matched_conditions` → Exit PolicySignal via `derive_scope_adverse_exit_signal_v0`.
- Mapping defense: `ADVERSE_EXIT_CANDIDATE` + matched `downscope` → `DOWNSCOPE_CANDIDATE` (never invents downscope without fact).
- `transition_state` remains sole SideState owner.

## Productive touchpoints

| File | Change |
|------|--------|
| `deterministic_scope_event_generator_v1.py` | `_select_directional_kind` scope-before-exit |
| `integrated_offline_trading_logic_replay_v1.py` | dual-dimension map at `_canonical_scope_event_to_scope_event` |

## Artifacts

| File | Purpose |
|------|---------|
| `root_cause.md` | First value-loss boundary |
| `contract_before_after.md` | Old vs new semantics |
| `authority_and_ordering_proof.md` | Owner / ordering proof |
| `test_results.txt` | Focused suite (133 passed) |
| `ruff.txt` / `diff_check.txt` | Local gates |
| `searched_paths.txt` / `commands.log` | Inventory |

## Safety

No risk/sizing/execution/orders. Runtime bridge not activated. No second authority.
