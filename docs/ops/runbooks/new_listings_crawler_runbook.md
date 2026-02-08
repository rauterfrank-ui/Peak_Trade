# Runbook — New Listings Crawler (CEX+DEX) + AI Layers Integration (Peak_Trade)

**Status:** Draft → Implementable  
**Scope:** Research/Shadow/Testnet only (NO-LIVE by default).  
**Goal:** Discover newly listed assets (CEX listings + DEX new pairs), normalize, enrich, risk-gate, score, publish events + artifacts, and optionally augment with AI layers (L1/L2/L3).  
**Non-goals:** No automatic execution. No bypass of deterministic risk gates. No financial advice.

---

## 0) Operating Principles (Hard Rules)

### Safety & Governance
- **L6 Execution remains blocked** unless explicitly enabled via existing Peak_Trade gating (enabled/armed/confirm-token + dry-run).
- **LLMs never override deterministic gates** (L5 is final).
- **All outputs are reproducible**: versioned configs, run_id, config hash, source versions, and append-only raw data.

### Data Handling
- **SQLite is the state/audit source-of-truth.**
- **JSONL event feed is the orchestration bus** (append-only, replayable).
- Prefer **read-only APIs**; secrets only via env/secret store, never committed.

---

## 1) Architecture Overview

### Components
1. **Collector/Crawler**  
   - Inputs: CEX listing sources, DEX new pair sources, aggregators  
   - Outputs: raw events + normalized assets + snapshots + risk flags + scores  
2. **Storage**  
   - SQLite DB (audit + state)  
   - Optional DB Views for stable reads  
3. **Event Bus (File-based)**  
   - `events.jsonl` append-only for orchestration triggers  
4. **Orchestrator (L0)**  
   - Runs cycles, schedules jobs, writes artifacts, triggers AI layer jobs  
5. **AI Layers**  
   - L1: Deep research (tagging/summaries/red flags)  
   - L2: Market regime/context  
   - L3: Strategy hypotheses + backtest experiment proposals  
   - L4: Governance critic (policy checks, evidence completeness)  
   - L5: Deterministic risk gate  
   - L6: Execution (blocked/gated)

---

## 2) Artifacts & Interfaces (Contracts)

### 2.1 SQLite DB (Source-of-Truth)
**Default path:** `out/research/new_listings/new_listings.sqlite`

**Tables (minimum):**
- `raw_events(source, venue_type, observed_at, payload_json)` (append-only)
- `assets(asset_id, symbol, name, chain, contract_address, decimals, first_seen_at, sources_json, tags_json)` (upsert)
- `market_snapshots(asset_id, ts, price, fdv, liquidity_usd, volume_24h_usd, holders, age_minutes)` (time series)
- `risk_flags(asset_id, ts, severity, flags_json)` (time series)
- `listing_scores(asset_id, ts, score, breakdown_json, reason)` (time series)

### 2.2 Stable DB Views (Recommended)
Create stable read views to avoid ad-hoc SQL in other components:
- `v_latest_snapshot`: latest snapshot per asset_id
- `v_latest_risk`: latest risk flags per asset_id
- `v_latest_score`: latest score per asset_id
- `v_assets_new`: assets first_seen within last X minutes or not reviewed
- `v_assets_candidates`: assets passing L5 and meeting min thresholds

### 2.3 JSONL Event Feed (Orchestration Bus)
**Path:** `out/research/new_listings/events.jsonl` (append-only)

**Event types (minimum):**
- `asset.discovered` (new asset_id first seen)
- `asset.updated` (metadata/normalization update)
- `risk.flagged` (severity bumped / red flags found)
- `candidate.promoted` (passed gates + crossed score threshold)
- `candidate.rejected` (failed deterministic gate)

**Event schema (recommended):**
```json
{
  "ts": "2026-02-08T12:34:56Z",
  "type": "asset.discovered",
  "run_id": "nl_20260208_123456Z_abcd1234",
  "asset_id": "eth:0x...",
  "symbol": "ABC",
  "chain": "ethereum",
  "source": "dex_foo",
  "meta": { "contract_address": "0x...", "venue_type": "DEX" }
}
```

---

## 3) Phases, Entry Criteria & Exit Criteria

| Phase | Name | Entry criteria | Exit criteria | Owner |
|-------|------|----------------|---------------|--------|
| **P0** | Foundation (DB + Event Bus) | Repo on main, config placeholders exist | SQLite schema applied; events.jsonl writable; one manual event appended and replayed | ops |
| **P1** | CEX Collector (read-only) | P0 done; API credentials in env only | At least one CEX source ingesting; raw_events populated; no secrets in repo | ops |
| **P2** | DEX Collector (read-only) | P0 done; RPC/API config in config only | At least one DEX source ingesting; new pairs → raw_events + assets | ops |
| **P3** | Normalization + Snapshots | P1/P2 have data | assets + market_snapshots populated; v_latest_* views usable | ops |
| **P4** | Risk Flags + Scoring | P3 done; risk/score config in config | risk_flags + listing_scores written; v_assets_candidates defined | ops |
| **P5** | L0 Orchestrator | P4 done | Cyclic runs; run_id + config hash in artifacts; events emitted for asset.discovered, candidate.* | ops |
| **P6** | AI Layers (L1–L4) optional | P5 done; AI config/model endpoints in env | L1/L2/L3/L4 runs on trigger from events; outputs versioned and referenced in artifacts | ops |
| **P7** | L5 Gate + Documentation | P6 or P5 done | L5 deterministic gate documented and run; no L6 without explicit gating | ops |

**Entry rule for any phase:** Previous phase exit criteria met and documented (e.g. in runlog or checklist).  
**Exit rule:** All exit criteria verified and signed off (e.g. runlog + evidence path).

---

## 4) Multi-Day Tasks (Implementation Order)

### Day 1–2: Foundation
- [ ] Create `out/research/new_listings/` and add to .gitignore (or use existing research out layout).
- [ ] Implement SQLite schema (raw_events, assets, market_snapshots, risk_flags, listing_scores).
- [ ] Implement stable views (v_latest_snapshot, v_latest_risk, v_latest_score, v_assets_new, v_assets_candidates).
- [ ] Implement append-only events.jsonl writer and run_id/config_hash in event meta.
- [ ] Document run_id format and config hash algorithm (e.g. SHA256 of sorted config keys/values).

### Day 3–4: CEX Collector
- [ ] Add config section for CEX sources (e.g. listing endpoints, rate limits).
- [ ] Implement read-only CEX fetcher; write to raw_events; normalize into assets (idempotent).
- [ ] Env-only secrets; no API keys in config or repo.
- [ ] Unit test: mock response → raw_events + assets row.

### Day 5–6: DEX Collector
- [ ] Add config for DEX sources (RPC, subgraph or API).
- [ ] Implement new-pair discovery; write raw_events + assets (contract_address, chain, decimals).
- [ ] Unit test: mock new pair → raw_events + assets.

### Day 7–8: Normalization + Snapshots
- [ ] Job: from raw_events / assets → market_snapshots (price, fdv, liquidity_usd, volume_24h_usd, holders, age_minutes).
- [ ] Ensure v_latest_snapshot is correct and used by downstream.

### Day 9–10: Risk Flags + Scoring
- [ ] Define risk flag rules (e.g. low liquidity, no audit, new contract); write risk_flags.
- [ ] Define scoring formula (breakdown_json + score + reason); write listing_scores.
- [ ] Implement v_assets_candidates (L5 pass + min thresholds).

### Day 11–12: L0 Orchestrator
- [ ] Cyclic run: crawl → normalize → risk/score → emit events (asset.discovered, asset.updated, risk.flagged, candidate.promoted/rejected).
- [ ] Artifacts: run_id, config_hash, timestamp, pointer to DB and events.jsonl segment.

### Day 13+ (Optional): AI Layers
- [ ] L1: Trigger on asset.discovered/candidate.promoted; write research summary/tags to artifact store; reference in DB or event meta.
- [ ] L2: Regime/context job; output versioned.
- [ ] L3: Hypothesis/backtest proposals; output versioned.
- [ ] L4: Governance critic run on candidate set; output versioned.
- [ ] L5: Deterministic gate doc and run; block L6 unless explicit gating.

---

## 5) Pre-Flight Checklist (Before First Run)

- [ ] Config versioned (e.g. in config/research/new_listings/ or similar).
- [ ] No live execution enabled (L6 blocked; no armed/confirm-token for execution).
- [ ] Secrets in env or secret store only; verified with dry-run or read-only test.
- [ ] SQLite path writable; events.jsonl path writable.
- [ ] Run_id and config hash documented and reproducible.

---

## 6) Operator Commands (Stub)

*(Replace with actual CLI/entrypoints when implemented.)*

```bash
# Create DB and schema (one-time)
# python -m research.new_listings.db_init --config config/research/new_listings/default.toml

# Single crawl cycle (CEX + DEX → raw_events, assets, snapshots, risk, score, events)
# python -m research.new_listings.run_cycle --config ... --dry-run

# Replay events from events.jsonl (e.g. for testing consumers)
# python -m research.new_listings.replay_events --path out/research/new_listings/events.jsonl --from-ts ...
```

---

## 7) Verification

- **DB:** Row counts in raw_events, assets, market_snapshots, risk_flags, listing_scores; v_assets_candidates returns only L5-passed assets.
- **Events:** Each run appends to events.jsonl; no duplicate run_id; event types match contract.
- **Reproducibility:** Same config + run_id → same artifacts (where deterministic); config hash in artifact meta.

---

## 8) Troubleshooting

| Issue | Check | Action |
|-------|--------|--------|
| No new raw_events | CEX/DEX rate limits, API keys in env | Check logs; back off; verify credentials |
| Duplicate asset_id | Normalization key (chain + contract) | Idempotent upsert; fix key definition |
| v_assets_candidates empty | L5 rules; min thresholds | Tune risk/score config; verify L5 logic |
| Events not consumed | Path and permissions; consumer running | Verify path; replay_events test |
| Config drift | config_hash in artifact | Re-run with same config; document drift |

---

## 9) References

- Peak_Trade governance: `src/governance/`, docs/governance/
- Risk layer (L5): docs/risk/, RISK_LAYER_*.md
- AI orchestration (L1–L4): src/ai_orchestration/
- Runbook conventions: [docs/ops/runbooks/README.md](README.md)
- Research/Shadow scope: NO-LIVE by default; no execution without explicit gating.

---

**Last Updated:** 2026-02-08  
**Maintainer:** ops
