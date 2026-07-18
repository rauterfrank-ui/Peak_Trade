# False Positive Inventory

| Path / Symbol | Term hit | Why FALSE_POSITIVE | Classification |
|---|---|---|---|
| `scripts/run_full_portfolio.py` (`pi_cycle = np.sin(...)`) | pi cycle | Synthetic price-noise sinusoid, not Armstrong Pi×1000 ECM | FALSE_POSITIVE |
| Generic docs “market cycle” without Armstrong/ECM | market cycle | Generic market language | FALSE_POSITIVE |
| `src/features/__init__.py` “ECM” placeholder banner | ECM | Deferred placeholder; no math; points to strategy layer | DOC_ONLY / FALSE_POSITIVE for feature-engine ECM |
| Unrelated PDF / casino T&C under Documents | Karoui substring noise in deep scans | Not Peak_Trade | FALSE_POSITIVE |
| Cyberkriminalitaet archive awareness docs | incidental string | External archive, not Peak_Trade integration | FALSE_POSITIVE |
| `docs/ops/specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md` “El Kouri / Elkouri” | misspelling note | Explicit unknown-name-alias, not an implementation | DOC_ONLY |
| Graph snapshot JSON path edges | El Karoui / Armstrong | Index of docs links only | EVIDENCE_ONLY / DOC_ONLY |

## Confirmed NOT false positives
- `src/strategies/el_karoui/**` — intentional Nicole-El-Karoui-inspired naming (math is pragmatic, not BSDE)
- `src/strategies/armstrong/**` and `src/strategies/ecm.py` — intentional Martin Armstrong / ECM (8.6y / 3141d)
- `src/experiments/armstrong_elkaroui_combi_experiment.py` — intentional joint R&D experiment
