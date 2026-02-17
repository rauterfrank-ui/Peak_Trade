# WORKBOOK — EXECUTION WIRING A2Z (v1)

## A) Scope + invariants
- Scope: **paper/shadow only** (no live)
- Default: `DRY_RUN=YES`
- Deny env: `LIVE`, `TRADING_ENABLE`, `EXECUTION_ENABLE`, `PT_ARMED`, `API_KEY`, `*_API_KEY`, `*_API_SECRET`, `*_API_PASSPHRASE`
- No network calls in unit tests.

## B) Current baseline (DONE)
- Adapter Protocol + Capability matrix (P106)
- Provider mocks: coinbase/okx/bybit (P107–P109)
- Registry + selector (P111)
- Router + CLI (P112–P114) + dry-run hard-guard (P115)
- Evidence + ops-loop hook (P116–P118, P117)

## C) Next objective
Produce a **provider wiring plan** that defines:
- `ProviderClientV1` interface (REST+WS placeholders)
- Credential spec + scope mapping (but **no secrets**, no real env names beyond placeholders)
- Rate-limit + retry policy (deterministic backoff config)
- Error taxonomy mapping to `OrderResultV1.message` + typed error codes
- Market-symbol normalization rules (e.g., BTC-USD vs BTCUSDT)

## D) Phase 1: "Networkless wiring"
- Create `src&#47;execution&#47;providers&#47;http_client_v1.py` (interface only)
- Create `src&#47;execution&#47;providers&#47;errors_v1.py` (typed exceptions)
- Create `src&#47;execution&#47;providers&#47;normalization_v1.py`
- Add unit tests: pure functions only.

## E) Phase 2: "Sandbox-ready provider stubs"
- Provider-specific client stubs with **no HTTP**:
  - `src&#47;execution&#47;providers&#47;coinbase&#47;client_v1.py`
  - `src&#47;execution&#47;providers&#47;okx&#47;client_v1.py`
  - `src&#47;execution&#47;providers&#47;bybit&#47;client_v1.py`
- These only validate intents, normalize symbols, simulate responses.

## F) Phase 3: Future integration hooks (no implementation yet)
- Add `TransportAdapter` slot to clients (dependency injection)
- Add `WSFeedAdapter` slot (optional)

## G) Safety gates
- Router: already guards `mode ∈ {shadow,paper}` and `dry_run == YES`.
- Add `ProviderClientV1` guard: reject secrets env vars if present at runtime.

## H) Evidence packs
- Add `scripts&#47;ops&#47;p119_execution_wiring_plan_snapshot_v1.sh` (docs + unit tests + pin)
- Must use `sha256sums_no_xargs_v1.sh`.

## I) DONE criteria
- Docs: wiring plan + taxonomy + normalization spec
- Code: interfaces + normalization + errors + stubs (no network)
- Tests: pass on 3.9/3.10/3.11
- Snapshot: `P119_EXECUTION_WIRING_PLAN_DONE_<TS>.txt` in `out/ops/`
