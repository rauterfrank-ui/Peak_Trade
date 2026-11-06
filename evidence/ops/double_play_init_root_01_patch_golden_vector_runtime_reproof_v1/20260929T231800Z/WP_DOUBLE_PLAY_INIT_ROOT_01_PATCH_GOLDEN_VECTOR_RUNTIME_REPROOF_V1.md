# INIT_ROOT_01 Patch + Dual Golden Vector + Runtime Reproof

## Patch

**Surface:** `productive_cycle_bind_seam_v1.py`

- Added `_layered_core_initialization_observations_v1` — historical **finalized 1m close grid** for L1–L5 init observation series (matches `23dccab` closes-only wiring).
- `prepare_productive_layered_core_replay_bind_v1` and `ensure_productive_layered_core_episode_store_v1` use this helper; **CMC `mark_price_m_t`** unchanged for mechanical binding and provenance.
- Removed WP-3 routing of init observations to static CMC `(M_t, M_t)` pair (INIT_ROOT_01 root cause).

## Gates

| Gate | Result |
|------|--------|
| INIT_ROOT_01 patch tests | PASS (`test_init_root_01_*`, cold S7 bootstrap, mark attachment, WP3 contract, G17) |
| Cold-S7 golden vector | PASS (INIT_ROOT_01 CLOSED, 0 wiring divergences) |
| Full E2E golden vector | PASS (`root_divergences_total=0`, forensic enter_long) |
| Runtime GET-only | 1 productive cycle, POST=0, no `INITIALIZATION_INCOMPLETE` |

## Runtime

Bounded run terminated on **MAX_RUN_DURATION** with `no_action` — **BLOCKED_NO_MARKET_ENTER** (not a technical defect).

## Git

No commit/push/PR.
