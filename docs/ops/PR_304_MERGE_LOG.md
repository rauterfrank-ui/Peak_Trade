# PR #304 — feat(risk): portfolio VaR core library (phase 1)

## Summary
Phase-1 Portfolio VaR Core implementiert: Parametric + Historical VaR, PeakConfig-Integration, robustes Symbol-Mapping, strikte Weight-Alignment Validierung, SciPy-optional Fallbacks, deterministische Tests und vollständige Dokumentation.

## Why
Portfolio-Risikolimits als Grundlage für spätere (Safety-gated) Pre-Trade Checks und Validierungs-Backtesting — ohne Live-Integration in Phase 1.

## Changes
- Added: Portfolio VaR Core (parametric/historical) + helpers (symbol normalization, weight alignment, cov/sigma)
- Added: PeakConfig builder: `risk.portfolio_var.*`
- Added: SciPy optional integration (stdlib fallback) + binomial test fallback
- Added: Tests (deterministic) + docs: `docs/risk/PORTFOLIO_VAR_PHASE1.md`

## Verification
- `pytest tests&#47;risk&#47; -v` ✅ (39/39 new tests, 135 total risk tests)
- `ruff check src&#47;risk&#47;` ✅
- `ruff format src&#47;risk&#47;` ✅

## Risk
Low. Phase-1 ist offline/core only; keine Live-Execution Pfade, keine auto-gating hooks.

## Operator How-To
- Config Snippet + Usage: `docs/risk/PORTFOLIO_VAR_PHASE1.md`
- Run tests: `pytest tests&#47;risk&#47; -q`

## References
- Commit: 0da9039
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/304
- Docs: docs/risk/PORTFOLIO_VAR_PHASE1.md
