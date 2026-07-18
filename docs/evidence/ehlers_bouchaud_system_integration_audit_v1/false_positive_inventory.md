# False Positive Inventory

Hits that match search terms but are **not** John Ehlers or Jean-Philippe Bouchaud implementations.

| Path / symbol | Matched term | Why FALSE_POSITIVE | Notes |
|---|---|---|---|
| `scripts/automation/README.md`, `docs/ai/PEAK_TRADE_AI_HELPER_GUIDE.md` | „Fehlersuche“ | German „Fehler“ ≠ Ehlers | Debugging docs |
| `templates/peak_trade_dashboard/error.html` | Fehlerseite | German error page | UI |
| `src/backtest/economic_observability_advanced_capabilities_v1.py` `estimated_market_impact` / `participation_rate` | market impact / participation | Generic capacity proxy `participation*10000`; no Bouchaud citation; `diagnostic_only` / `runtime_effect=NONE` | Not square-root law |
| `src/meta/learning_loop/independent_pre_trade_safety_kernel_v1.py` `expected_market_impact_guard` | market impact | Pre-trade BPS guard; no Bouchaud | Risk kernel |
| `config&#47;scenarios&#47;*.toml` `[scenario.price_impact]` | price impact | Scenario fixture keys | Sim |
| `docs/execution/WP0C_COMPLETION_REPORT.md` etc. | market impact | Narrative „no market impact modeling“ | Docs |
| `src&#47;research&#47;cross_sectional_futures_*lead_lag*` | lead-lag | Separate information-diffusion research; **no Bouchaud citation** in score owners | Do not attribute to JP Bouchaud without source |
| Generic `microstructure` wording outside `src&#47;strategies&#47;bouchaud&#47;**` and `*bouchaud*` research owners | microstructure | Domain vocabulary | Require owner proof |
| Typo variants Bochuard/Bouchard/Bouchaurd/Buchaud/Buchard | aliases | **Zero** repo hits as Bouchaud aliases | — |
| `DSP` outside Ehlers module | DSP | Only meaningful when tied to Ehlers strategy text | Avoid standalone DSP claim |
| Doc claims of Hilbert/Bandpass/Propagator as if live | method names | Stubs or unused config — **not** false name hits, but **overclaimed capability** | Treated in method analyses |

## Borderline (kept as real Bouchaud *inspiration*, not false)

- OHLCV proxy feature names (`volatility_normalized_price_impact`, `kyle_lambda_proxy`, …) — real research surface, but **proxy**, not true Bouchaud law.
- Strategy tiering notes calling Bouchaud a „SKELETON“ — partially stale vs code that now emits 0/1 proxies.
