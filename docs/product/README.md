# Peak_Trade Product Documentation

> **Zweck:** Kanonische, versionierte Produkt- und Implementierungsdokumentation.  
> **Runtime-Wirkung:** keine.  
> **Trading-/Risk-/Authority-/Economic-/Decision-Ownership:** keine.

---

## Canonical Product Document — Visual Operator Dashboard

| Feld | Wert |
|------|------|
| Document | [Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md](Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md) |
| Version | v1.3 |
| Edition | Canonical Composition + Technical Discovery Edition |
| Role | Dashboard Master Runbook (PART I normative Composition/Landmark; PART II technical discovery snapshot) |
| `PRODUCT_DOCUMENT` | `true` |
| `IMPLEMENTATION_SPEC` | `true` |
| `READ_ONLY` | `true` |
| `NO_RUNTIME_EFFECT` | `true` |
| `NO_TRADING_EFFECT` | `true` |

### Binding statement

```text
DASHBOARD_PRODUCT_SPEC_SSOT=docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md
DASHBOARD_PRODUCT_COMPATIBILITY_SURFACE=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
DERIVED_DOCUMENTS_MAY_NOT_OVERRIDE_PRODUCT_SPEC=true
CORE_SYSTEM_REMAINS_FUNCTIONAL_SSOT=true
CANONICAL_PRODUCT_DOCUMENT=true
PRODUCT_DOCUMENT=true
IMPLEMENTATION_SPEC=true
READ_ONLY=true
NO_RUNTIME_EFFECT=true
NO_TRADING_EFFECT=true
DASHBOARD_IS_CONSUMER_ONLY=true
DASHBOARD_OWNS_NO_TRADING_SEMANTICS=true
DASHBOARD_OWNS_NO_DECISION_STATE=true
DASHBOARD_OWNS_NO_RISK_STATE=true
DASHBOARD_OWNS_NO_ECONOMIC_STATE=true
DASHBOARD_OWNS_NO_AUTHORITY_STATE=true
CORE_SYSTEM_SINGLE_SOURCE_OF_TRUTH=true
CANONICAL_CORE_OWNER=MASTER_V2
DASHBOARD_ROLE=PRESENTATION_LAYER
```

### SSOT rules (no dual functional truth)

1. Das **Core-System / Master V2** bleibt die einzige fachliche Wahrheit (Trading, Risk, Authority, Economic, Decision).
2. Das **Composition-/Landmark-Master-Runbook** ist die **Dashboard-Produkt-/Presentation-Spec** und innerhalb der Dashboard-Produktdokumentation die **einzige kanonische Produktspezifikation**. Die Datei `Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md` ist nur Compatibility-/Contract-Surface und delegiert an das Master-Runbook.
3. Innerhalb des Runbooks: **PART I** ist normativ (Composition-/Landmark-/Governance-/UX-Ziel); **PART II** ist die technische Discovery-/Ist-Referenz. Bei Abweichungen gilt PART I.
4. Das Dashboard ist **Consumer-only** — es besitzt keine Trading-, Risk-, Economic-, Decision- oder Authority-Ownership.
5. Abgeleitete Dokumente (Implementation Plan, Patch-Empfehlungen, Index-Pointer, technische Surface-Chronicle) dürfen das Master-Runbook **nicht** überschreiben und keine zweite vollständige Produktspezifikation bilden. Eigenständige Discovery-Exporte sind im Master-Runbook PART II absorbiert und dürfen nicht als konkurrierende Wahrheit verbleiben.
6. `docs/webui/MARKET_SURFACE_V0.md` bleibt die technische Route-/Marker-/Env-Chronicle — nicht die Product Spec.

### Ownership split (reuse, no dual truth)

| Layer | Canonical owner | Scope |
|-------|-----------------|-------|
| Product / UX / Implementation Spec | [Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md](Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md) | what the Visual Operator Dashboard must look like and how to ship slices |
| Technical Market Surface contract / IA chronicle | [`docs/webui/MARKET_SURFACE_V0.md`](../webui/MARKET_SURFACE_V0.md) | route, markers, env gates, structure contracts |
| Futures read-only display contract | [`docs/ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md`](../ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) | F5 display boundary |
| Core trading / risk / authority / economic / decision | MASTER_V2 + existing core owners | never owned by dashboard docs or UI |

### Companion bootstrap artifacts (derived / non-canonical)

| Artifact | Role |
|----------|------|
| [RUNBOOK_PATCH_RECOMMENDATIONS.md](RUNBOOK_PATCH_RECOMMENDATIONS.md) | `DOCUMENT_ROLE=NON_CANONICAL_RECOMMENDATION_LOG` — Gap-/Patch-Liste only |
| [VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_PLAN_V1.md](VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_PLAN_V1.md) | `DOCUMENT_ROLE=DERIVED_IMPLEMENTATION_PLAN` — dem Runbook untergeordnet |

### Known implementation gaps (docs-only; not closed here)

```text
SELECTION_CONTEXT_IMPLEMENTED=false
SELECTION_CONTEXT_REQUIRED_BEFORE_PHASE_4C_COMPLETE=true
CURRENT_REPO_OR_DOCS_DEFAULT_MAY_INCLUDE_KRAKEN_OR_BTC=true
CURRENT_DEFAULT_MUST_NOT_BE_CLAIMED_AS_ALREADY_COMPLIANT=true
MARKET_BROWSER_E2E_BASELINE=MISSING
```

### Bootstrap provenance

```text
GO_TOKEN=GO_CONSOLIDATED_COMPOSITION_LANDMARK_MASTER_RUNBOOK_REPO_SSOT_V1
PRODUCT_IMPLEMENTATION_GO_TOKEN=GO_PEAK_TRADE_VISUAL_OPERATOR_DASHBOARD_PRODUCT_V1_3
SOURCE_DOWNLOADS_PATH=/Users/frnkhrz/Downloads/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md
SOURCE_SHA256=1c77fc3bdbcc9d05c6d2e7f07bd84e962ea81d738f431207481d21bb2b558c0e
CANONICAL_TARGET=docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md
COMPATIBILITY_SURFACE=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
RUNBOOK_SHA256=b5c4ac394fd41b9ab5cc9bc84fecee04bce72376b7b21ce640e70874aa7ac57b
SOURCE_TARGET_IDENTICAL=false
HASH_DEVIATION_REASON=inserted_business_ssot_boundary;inserted_6a_browser_policy_from_product_contract;docs_token_policy_illustrative_path_encoding
PRIOR_BOOTSTRAP_GO_TOKEN=GO_PEAK_TRADE_VISUAL_OPERATOR_DASHBOARD_RUNBOOK_REPOSITORY_BOOTSTRAP_V1
DISCOVERY_BASELINE_HEAD=20969b4a155ffbdc0e1a9a55657311aa061511be
DISCOVERY_BASELINE_PR=5244
```
