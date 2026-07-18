# Incident report — deleted untracked evidence packs

## What happened
On 2026-07-19, an operator-requested local cleanup ran:

```
git fetch origin && git checkout main && git reset --hard origin/main && git clean -fd
```

This removed six previously **untracked** evidence directories that had never been committed.

## Deleted packs
1. docs/evidence/canonical_chain_post_5337_zero_trade_audit_v1/
2. docs/evidence/ehlers_bouchaud_system_integration_audit_v1/
3. docs/evidence/el_karoui_armstrong_system_integration_audit_v1/
4. docs/evidence/obl_b05_bollinger_entry_side_authority_operator_go_selection_v1/
5. docs/evidence/post_surface_p_canonical_chain_zero_trade_blocker_reaudit_v1/
6. docs/evidence/scope_event_noop_root_cause_audit_v1/ (except preserved `bearish_bar_samples.csv`)

## Why Git could not restore originals
- Paths were untracked → not in object DB / branches / stash
- Trash / Local History searches found no recoverable pack copies
- Therefore recovery is **semantic regeneration**, not byte restore

## Recovery performed
Branch `recovery/reconstruct-deleted-evidence-packs-v1` reconstructs packs from transcripts, PR/branch context, and historical probe re-runs in temporary worktrees.

Recovered_at: 2026-07-18T23:23:43Z
