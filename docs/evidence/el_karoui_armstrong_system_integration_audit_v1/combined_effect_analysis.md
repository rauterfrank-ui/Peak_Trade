# Combined Effect Analysis (El Karoui × Armstrong)

## Is there a joint productive aggregator in Master V2?
**No.** No combined producer feeds Dynamic Scope, Agreement authority, Risk/Sizing quantity, or Execution Eligibility in the canonical chain.

## Research-only combined surface (exists)

| Item | Value |
|---|---|
| Aggregator | `src/experiments/armstrong_elkaroui_combi_experiment.py` (`run_armstrong_elkaroui_combi_experiment`) |
| CLI | `scripts/research_cli.py` subcommand `armstrong-elkaroui-combi` |
| Concept | Cartesian product of Armstrong event-state × El Karoui vol-regime labels; forward-return stats per combo state |
| Weighting | Descriptive aggregation / stats — **not** a live multi-factor score with production weights |
| Order | Labels computed independently, then joined for analysis |
| Conflict resolution | Research reporting only; no trade arbitration |
| Missing values | Experiment-local handling; not MV2 fail-closed authority |
| Long/Short symmetry | Label study; default strategy maps are long/flat asymmetric |
| Authority boundary | Explicit R&D / `ALLOWED_ENVIRONMENTS` research+offline only |
| Zero-trade influence | None on productive zero-trade / MV2 path |

## Other joint mentions
- Playbooks / cross-run findings docs (`ARMSTRONG_ELKAROUI_CROSS_RUN_FINDINGS_V1.md`) — DOC_ONLY / R&D hypotheses
- `nicole_el_karoui_notes.md` wishlist to combine ECM regimes with El Karoui theory — not implemented as productive math
- Promotion gate: no joint promotion authority found

## Composition / Multi-Factor / Regime / Scope / Agreement / Risk / Sizing / Portfolio / Promotion
| Surface | Combined? |
|---|---|
| Composition (MV2) | No |
| Multi-Factor Score (prod) | No |
| Regime Detection (prod) | No (only R&D labels) |
| Dynamic Scope | No |
| Agreement (authority) | No |
| Risk / Sizing (MV2) | No |
| Portfolio live | No |
| Promotion Gate | No |

**COMBINED_INTEGRATION_FOUND** = true for **research combi only**; false for productive MV2.
