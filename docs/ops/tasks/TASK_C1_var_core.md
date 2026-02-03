# TASK SPEC

TITLE: Phase C1 – Risk Core: VaR foundation (offline, deterministic)
SCOPE:
- Implement core VaR computation API (inputs/outputs/units explicit)
- Deterministic behavior (seeded where applicable)
- Evidence-chain integration for the runner(s) that call it
NON-GOALS:
- No live trading / execution
- No exchange-specific features (Nasdaq/Futures intentionally out of scope)
ENTRY CRITERIA:
- Phase B merged (evidence-chain helpers available)
EXIT CRITERIA:
- `compute_var(...)` (or equivalent) implemented with unit tests
- Docs: method, assumptions, failure modes
- Evidence pack produced by a minimal `risk_cli` or integration point
TEST PLAN:
- Unit tests for VaR on known distributions
- Edge cases: NaNs, short series, zero variance, fat tails
EVIDENCE PACK:
- artifacts/risk/<run_id>/meta.json + results (optional)
RISKS:
- Statistical assumptions; guardrails for small samples
