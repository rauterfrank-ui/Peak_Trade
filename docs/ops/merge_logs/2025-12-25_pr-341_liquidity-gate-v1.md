# Merge Log — PR #341 — Liquidity Gate v1

> **Note:** This is a historical merge log. File paths referenced may have been relocated or refactored since this PR was merged.

- PR: #341 — feat(risk): liquidity gate v1 (spread/slippage/depth guards + audit)
- Merge: 2025-12-25 → main
- Commit: 5b0c056
- Scope: Risk Layer V1 (pre-trade microstructure protection)
- Diff: +2,538 / −6 (8 files)

## Summary
Liquidity Gate v1 ergänzt den Risk Layer um pre-trade Microstructure-Guards (Spread, Slippage, Depth, Order/ADV) inkl. audit-stabiler Serialisierung und Integration in `RiskGate` (Eval-Order: KillSwitch → VaR → Stress → Liquidity → Order Validation).

## Why
Schützt Execution gegen adverse Marktbedingungen (zu weite Spreads, erhöhte Slippage, zu geringe Orderbook-Depth, oversized Order vs. ADV) bevor Orders validiert/platziert werden.

## Changes
- NEW: `src\&#47;risk_layer\&#47;micro_metrics.py` — tolerante Extraktion von Microstructure-Daten (mehrere Layout-Varianten), audit-stabile Serialisierung
- NEW: `src\&#47;risk_layer\&#47;liquidity_gate.py` — Guards: Spread/Slippage/Depth/ADV
  - Market Orders: 0.7× Thresholds (strenger)
  - Limit Orders: "wide spread" kann BLOCK→WARN downgraden (Exception)
- NEW: `docs/risk/LIQUIDITY_GATE_RUNBOOK.md` — Operator Runbook (Troubleshooting + Manual Smoke)
- NEW: `config/risk_liquidity_gate_example.toml` — Profile (equity/crypto/research)
- UPDATE: `src\&#47;risk_layer\&#47;risk_gate.py` — Liquidity Gate Integration + Violation Codes
- UPDATE: `tests/risk_layer/test_risk_gate.py` — Integration Tests (Order + WARN/BLOCK + Eval-Order)

## Verification
- Tests: `uv run pytest -q tests&#47;risk_layer&#47;` → 194 passed (inkl. 43 neue Liquidity-Gate Tests)
- Lint/Format: `uv run ruff check ...` clean; `uv run ruff format ...` applied

## Risk
LOW
- Gate ist disabled by default → kein Einfluss ohne explizites Enable
- Missing micro metrics → OK (fail-open, keine Crashes/False Blocks)
- Deterministic/Audit-stable output, Violation Codes explizit
- Bestehende Gates (KillSwitch/VaR/Stress) unverändert

## Operator How-To
1) Paper/Shadow enable: `enabled=true`, `require_micro_metrics=true`
2) Audit trail prüfen: `liquidity_gate` section + violation codes
3) Thresholds je Asset Class/Venue tunen; danach Live-Enable (nach ≥1 Woche Monitoring)

## References
- PR #341 — Liquidity Gate v1
- Runbook: `docs/risk/LIQUIDITY_GATE_RUNBOOK.md`
- Config: `config/risk_liquidity_gate_example.toml`
- Related: `docs/risk/VAR_GATE_RUNBOOK.md`, `docs/risk/STRESS_GATE_RUNBOOK.md`
