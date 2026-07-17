# Peak_Trade Product Documentation

> **Zweck:** Kanonische, versionierte Produkt- und Implementierungsdokumentation.  
> **Runtime-Wirkung:** keine.  
> **Trading-/Risk-/Authority-/Economic-/Decision-Ownership:** keine.

---

## Canonical SSOT — Market Dashboard Architecture Reset & Rebuild

| Feld | Wert |
|------|------|
| Document | [Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md](Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md) |
| Version | v1.0 |
| Role | Maßgeblicher Masterplan für den vollständigen Market-Dashboard-Architecture-Reset und anschließenden Rebuild |
| `PRODUCT_DOCUMENT` | `true` |
| `READ_ONLY` | `true` |
| `NO_RUNTIME_EFFECT` | `true` |
| `NO_TRADING_EFFECT` | `true` |
| `NO_LIVE_AUTHORIZATION` | `true` |
| `IMPLEMENTATION_AUTHORIZED_BY_THIS_DOC_ALONE` | `false` |

### Binding statement

```text
MARKET_DASHBOARD_ARCHITECTURE_RESET_REBUILD_SSOT=docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md
MARKET_DASHBOARD_ARCHITECTURE_RESET_REBUILD_VERSION=v1.0
SINGLE_ACTIVE_SSOT_FOR_ARCHITECTURE_RESET_REBUILD=true
HISTORICAL_DASHBOARD_EVIDENCE_NOT_AUTO_DELETED=true
DOES_NOT_SUPERSEDE_HISTORICAL_EVIDENCE_ARTIFACTS=true
DOES_NOT_AUTHORIZE_LIVE_RUNTIME_ORDERS_OR_TRADING=true
IMPLEMENTATION_ONLY_VIA_SUBSEQUENT_BOUNDED_PRS=true
ON_CONFLICT_WITH_OLDER_MARKET_DASHBOARD_DESIGN_PLANS_THIS_RUNBOOK_GOVERNS_RESET_REBUILD_SCOPE=true
DASHBOARD_ROLE=READ_ONLY_CONSUMER_OF_CANONICAL_READ_MODELS
CANONICAL_CORE_OWNER=MASTER_V2
```

Dieses Dokument ist die **einzige aktive Repo-SSOT** für den Market-Dashboard-Architecture-Reset und Rebuild. Es ersetzt nicht automatisch historische Evidence-Dokumente. Es autorisiert keine Live-, Runtime-, Order- oder Trading-Aktivierung. Die Umsetzung erfolgt ausschließlich in nachfolgenden bounded PRs. Bei Widerspruch zwischen älteren Market-Dashboard-Designplänen und diesem Runbook ist dieses Runbook für den neuen Reset-/Rebuild-Scope maßgeblich.

---

## Historical Product Document — Visual Operator Dashboard (pre-reset composition)

| Feld | Wert |
|------|------|
| Document | [Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md](Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md) |
| Version | v1.3 |
| Edition | Canonical Composition + Technical Discovery Edition |
| Role | Historical Dashboard Composition/Landmark Master Runbook (PART I / PART II); retained as evidence |
| Status | `SUPERSEDED_FOR_ARCHITECTURE_RESET_REBUILD_SCOPE` — remains useful historical/reference material |
| `PRODUCT_DOCUMENT` | `true` |
| `IMPLEMENTATION_SPEC` | `true` |
| `READ_ONLY` | `true` |
| `NO_RUNTIME_EFFECT` | `true` |
| `NO_TRADING_EFFECT` | `true` |

### Binding statement

```text
HISTORICAL_DASHBOARD_PRODUCT_SPEC_REFERENCE=docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md
DASHBOARD_PRODUCT_COMPATIBILITY_SURFACE=docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md
DASHBOARD_PRODUCT_SPEC_SCOPE=HISTORICAL_COMPOSITION_LANDMARK_PRE_RESET
ACTIVE_FOR_ARCHITECTURE_RESET_REBUILD_SCOPE=false
SUPERSEDED_FOR_ARCHITECTURE_RESET_REBUILD=true
DERIVED_DOCUMENTS_MAY_NOT_OVERRIDE_ACTIVE_RESET_SSOT=true
CORE_SYSTEM_REMAINS_FUNCTIONAL_SSOT=true
HISTORICAL_PRODUCT_DOCUMENT=true
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
ARCHITECTURE_RESET_REBUILD_GOVERNED_BY=docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md
```

### SSOT rules (no dual functional truth)

1. Das **Core-System / Master V2** bleibt die einzige fachliche Wahrheit (Trading, Risk, Authority, Economic, Decision).
2. Für den **Architecture-Reset-/Rebuild-Scope** ist ausschließlich [Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md](Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md) die aktive SSOT.
3. Das **Composition-/Landmark-Master-Runbook v1.3** bleibt als historische Produkt-/Presentation-Spec und Evidence erhalten (`STATUS=HISTORICAL_PRE_RESET`, `SUPERSEDED_FOR_ARCHITECTURE_RESET_REBUILD=true`); für den Reset-/Rebuild-Scope darf es **keine** zweite aktive Architecture-SSOT bilden. Die Datei `Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md` bleibt Compatibility-/Contract-Surface (`HISTORICAL_PRODUCT_REFERENCE` / `COMPATIBILITY_REFERENCE`).
4. Innerhalb des v1.3-Runbooks gilt `PART_I_NORMATIVE` / `PART_I_WINS_ON_CONFLICT` **nur** für die historische pre-reset Interpretation; sie überschreiben **nicht** die aktive Architecture-Reset-SSOT. **PART II** bleibt Discovery-/Ist-Referenz.
5. Das Dashboard ist **Consumer-only** — es besitzt keine Trading-, Risk-, Economic-, Decision- oder Authority-Ownership.
6. Abgeleitete Dokumente (Implementation Plan, Patch-Empfehlungen, Index-Pointer, technische Surface-Chronicle) dürfen weder die Architecture-Reset-SSOT noch historische Evidence unkontrolliert überschreiben.
7. `docs/webui/MARKET_SURFACE_V0.md` bleibt die technische Route-/Marker-/Env-Chronicle — nicht die Product Spec und nicht die Architecture-Reset-SSOT.

### Ownership split (reuse, no dual truth)

| Layer | Canonical owner | Scope |
|-------|-----------------|-------|
| Architecture Reset & Rebuild Masterplan | [Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md](Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md) | controlled reset + canonical rebuild of dashboard layer |
| Historical Product / UX Composition Spec | [Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md](Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md) | pre-reset Visual Operator composition/landmark evidence |
| Technical Market Surface contract / IA chronicle | [`docs/webui/MARKET_SURFACE_V0.md`](../webui/MARKET_SURFACE_V0.md) | route, markers, env gates, structure contracts |
| Futures read-only display contract | [`docs/ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md`](../ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) | F5 display boundary |
| Core trading / risk / authority / economic / decision | MASTER_V2 + existing core owners | never owned by dashboard docs or UI |

### Companion bootstrap artifacts (derived / non-canonical / historical)

| Artifact | Role |
|----------|------|
| [RUNBOOK_PATCH_RECOMMENDATIONS.md](RUNBOOK_PATCH_RECOMMENDATIONS.md) | `DOCUMENT_ROLE=NON_CANONICAL_RECOMMENDATION_LOG` — Gap-/Patch-Liste only |
| [VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_PLAN_V1.md](VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_PLAN_V1.md) | `DOCUMENT_ROLE=DERIVED_IMPLEMENTATION_PLAN` — historical; superseded for architecture reset/rebuild scope |
| [Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md](Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md) | Compatibility-/Contract-Surface; historical path-bound references |

### Known implementation gaps (docs-only; not closed here)

```text
SELECTION_CONTEXT_IMPLEMENTED=false
SELECTION_CONTEXT_REQUIRED_BEFORE_PHASE_4C_COMPLETE=true
CURRENT_REPO_OR_DOCS_DEFAULT_MAY_INCLUDE_KRAKEN_OR_BTC=true
CURRENT_DEFAULT_MUST_NOT_BE_CLAIMED_AS_ALREADY_COMPLIANT=true
MARKET_BROWSER_E2E_BASELINE=MISSING
```



---

## Market Dashboard SSOT consistency matrix (reset/rebuild scope)

Maschinenlesbare Rollenklärung. Bei Widerspruch steuert ausschließlich die Architecture-Reset-SSOT den Reset-/Rebuild-Scope.

| DOCUMENT | ROLE | ACTIVE_FOR_RESET_SCOPE | NORMATIVE_AUTHORITY | SUPERSEDED_BY | NOTES |
|----------|------|------------------------|---------------------|---------------|-------|
| `docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md` | Architecture Reset & Rebuild Master SSOT | `true` | Architecture reset/rebuild product plan | — | Sole active SSOT for reset/rebuild; does not authorize Live/Orders |
| `docs/product/README.md` | Product docs index / binding | `true` (binding only) | Points to Reset SSOT for reset scope | — | Declares `SINGLE_ACTIVE_SSOT_FOR_ARCHITECTURE_RESET_REBUILD=true` |
| `docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md` | Historical composition/landmark product reference | `false` | Pre-reset historical PART I only | Reset Runbook v1.0 (reset scope) | `STATUS=HISTORICAL_PRE_RESET`; may not override Reset SSOT |
| `docs/product/Peak_Trade_Visual_Operator_Dashboard_Product_Runbook_v1.3.md` | Compatibility / browser-policy surface | `false` | Browser verification policy only | Reset Runbook v1.0 (reset scope) | `COMPATIBILITY_REFERENCE`; Chrome/Playwright preserved |
| `docs/product/VISUAL_OPERATOR_DASHBOARD_IMPLEMENTATION_PLAN_V1.md` | Derived historical implementation plan | `false` | None for reset scope | Reset Runbook v1.0 (reset scope) | `STOP_BEFORE_IMPLEMENTATION` / `NONE_AUTHORIZED` are historical pre-reset; do **not** block Reset PR-A |
| `docs/webui/MARKET_SURFACE_V0.md` | Technical route/marker/env chronicle | `false` | Marker/IA chronicle ownership only (not Product SSOT) | Reset Runbook v1.0 (architecture target) | `TECHNICAL_CHRONICLE_NOT_PRODUCT_SSOT`; pre-reset IA/defaults/static display paths are historical facts |
| `docs/ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md` | F5 display contract owner | `true` (F5 display semantics) | F5 display boundary / non-authority | — | Orthogonal **ownership** to Market Surface; may be hosted on `GET &#47;market` without transferring F5 authority into WebUI |
| `docs/ops/specs/FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md` | Futures provenance display requirements | `true` (provenance display) | Provenance / fail-closed display | — | Read-only dashboard must not call write-enabled fetch paths |
| `docs/ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md` | Lane/authority taxonomy | `true` (authority lane rules) | `dashboard`=`review_input_only`; projection non-authority | — | DP authority boundaries remain protected even if path redirects |
| `docs/ops/specs/SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md` | Env/label non-authority policy | `true` (label semantics) | Labels ≠ capability/authority | — | Preserved |
| `docs/ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md` | DP pure-stack display planning map | `false` (planning lens) | Display-only; no DP authority | Reset Runbook for `/market` consumer rebuild | Canonical DP read-model projection on `/market` allowed; inventing DP truth in WebUI forbidden |
| `docs/ops/specs/MASTER_V2_DASHBOARD_COCKPIT_OBSERVER_SURFACE_INVENTORY_V0.md` | Observer surface inventory | `false` (inventory) | Inventory only | — | Dashboard/cockpit observation ≠ order authority |

```text
DUAL_ACTIVE_ARCHITECTURE_RESET_SSOT_FORBIDDEN=true
V1_3_MAY_NOT_OVERRIDE_RESET_SSOT=true
MARKET_SURFACE_V0_IS_NOT_PRODUCT_OR_RESET_SSOT=true
HISTORICAL_STOP_NONE_AUTHORIZED_DOES_NOT_BLOCK_RESET_PR_A=true
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
