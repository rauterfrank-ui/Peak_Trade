# Peak_Trade Prioritätenplan — Systemaudit 2026-07-17

**Status:** CLOSEOUT — residual gaps reconciled (docs&#47;governance only)  
**Canonical owner:** this file (`docs&#47;audits&#47;Peak_Trade_Prioritaetenplan_Systemaudit_2026-07-17.md`)  
**Machine SSOT:** [`config&#47;governance&#47;system_audit_plan_closeout_ssot_v1.json`](../../config/governance/system_audit_plan_closeout_ssot_v1.json)  
**Closeout SHA (origin&#47;main at plan freeze):** `17febbfd677e8133ce529ddc8db6ad0fab1d0d58`  
**Authority:** operator-directed system-audit closeout; non-authorizing for live&#47;orders&#47;runtime

```
PEAK_TRADE_PRIORITAETENPLAN_SYSTEMAUDIT_2026_07_17=true
SYSTEM_AUDIT_PLAN_CLOSEOUT=true
BASE_SHA=17febbfd677e8133ce529ddc8db6ad0fab1d0d58
CLOSEOUT_UTC=2026-07-17T15:55:00Z
SECOND_ACTIVE_TRUTH=false
THIS_DOCUMENT_IS_THE_CANONICAL_PLAN_SSOT=true
PERMISSION_MODE=docs_governance_only
TRADING_CORE_CHANGED=false
EXECUTION_SEMANTICS_CHANGED=false
GITHUB_SETTINGS_MUTATED=false
EXTERNAL_SYSTEM_MUTATIONS=false
RUNTIME_BRIDGE_ACTIVATED=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
CONFIRMED_DEFECT_COUNT=0
```

## 0. Source and scope

| Field | Value |
|---|---|
| Plan title | `Peak_Trade_Prioritaetenplan_Systemaudit_2026-07-17` |
| Repo SSOT path | `docs&#47;audits&#47;Peak_Trade_Prioritaetenplan_Systemaudit_2026-07-17.md` |
| Prior external&#47;desktop copies | not mutated; not treated as repo SSOT |
| Active duplicate plan in repo | none found at closeout |
| Covered merges | PR `#5291` … `#5299` squash-merged on `main` |
| Covered read-only audits after merges | AWS, OKX, Monitoring, Ruleset&#47;Workflow inventory |

This closeout updates **status / residual-gap / Definition-of-Done** only. It does not change trading-core, strategy&#47;risk&#47;sizing&#47;execution semantics, Economic Gate, promotion state, GitHub settings, rulesets, branch protection, workflows, AWS&#47;IAM, OKX, secrets, schedulers, testnet&#47;shadow&#47;paper&#47;live, or orders.

## 1. Priority status (verified)

### 1.1 P1 — GitHub SSOT / Tombstone / Surface-P

| Item | Status | Evidence |
|---|---|---|
| P1 GitHub-SSOT | **DONE** | PR `#5291` — required checks SSOT synced to live main protection |
| P1 Tombstone documentation | **DONE** | PR `#5292` — market path tombstone normalization |
| P1 Surface-P contract drift | **DONE** | PR `#5293` — Surface P status contract alignment |

### 1.2 P2 — Governance inventories

| Item | Status | Evidence |
|---|---|---|
| P2 Promotion Owner Inventory&#47;SSOT | **DONE** | PR `#5294`; [`PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1.md`](../governance/PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1.md) |
| P2 Risk&#47;Sizing Inventory | **DONE** | PR `#5295`; consolidation **NOT_STARTED** (intentional) |
| P2 Legacy Order Intent Inventory | **INVENTORY DONE** | PR `#5296` squash-merged; [`LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1.md`](../governance/LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1.md) |
| Legacy Order Intent Consolidation | **NOT_STARTED** (`Konsolidierung NOT_STARTED`) | intentional governance debt |
| Legacy Order Intent Decommission | **NOT_STARTED** (`Decommission NOT_STARTED`) | intentional governance debt |
| Authority leak | **false** (`kein Authority Leak`) | inventory marker `AUTHORITY_LEAK_DETECTED=false` |
| Runtime activation in inventory slice | **none** (`keine Runtime-Aktivierung`) | no runtime rewire; bridge remains bound-not-activated |

### 1.3 P3 — External&#47;integration audits

#### AWS — `PARTIAL_READ_ONLY_AUDIT`

| Field | Value |
|---|---|
| Status | **PARTIAL_READ_ONLY_AUDIT** |
| Doc | [`AWS_INFRASTRUCTURE_READ_ONLY_AUDIT_2026-07-17.md`](AWS_INFRASTRUCTURE_READ_ONLY_AUDIT_2026-07-17.md) |
| Canonical account&#47;profile | account `511913187493`; profile `peak-trade-prearm-v3-audit` (operator-pinned) |
| Dual-profile claim | Durable audit used the canonical profile only. Fallback profile `peak-trade-operator-readonly-audit-user` is same-account AssumeRole trust principal; **no durable claim** that a second live STS session was executed in that audit. |
| Private&#47;resource-level completeness | Partially **ACCESS_DENIED** &#47; **NOT_VERIFIABLE** under audit-role IAM scope |
| Secret values | not read |
| AWS mutations | none |
| Full private verification | requires separate Operator-GO for broader read-only IAM |
| Classification | **not** an acute trading-core defect |

#### OKX — `PARTIAL_PASS_PRIVATE_NOT_VERIFIABLE`

| Field | Value |
|---|---|
| Status | **PARTIAL_PASS_PRIVATE_NOT_VERIFIABLE** |
| Doc | [`OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md`](OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md) |
| Public REST | reachable (`MATCH`) |
| Public WebSocket | reachable (`MATCH`) |
| Private Auth | not verified (credentials ABSENT; no live private client) |
| Private Reconciliation | static&#47;fail-closed only (`RECONCILIATION_VERIFIED=static_contract_only`) |
| Futures-only &#47; BTC exclusion | static productive binding&#47;policy `MATCH` |
| Mutations&#47;orders | none |
| Full private verification | requires credentials&#47;access + separate Operator-GO |
| Classification | **not** confirmed integration drift |

#### Monitoring — **DONE**

| Field | Value |
|---|---|
| Status | **DONE** |
| Doc | [`MONITORING_TOPOLOGY_READ_ONLY_AUDIT_2026-07-17.md`](MONITORING_TOPOLOGY_READ_ONLY_AUDIT_2026-07-17.md) |
| Merge | PR `#5299` squash-merged |
| Grafana | removed as designed (`REMOVED_AS_DESIGNED`) |
| Alertmanager | removed as designed |
| CloudWatch (Peak_Trade monitoring deploy) | removed as designed |
| Prometheus | repo-only metrics&#47;scrape SSOT (`VERIFIED_REPO_ONLY`) |
| Alert routing | repo-only in-app (`VERIFIED_REPO_ONLY`) |
| Stale references | not active topology drift |
| Canonical topology | resolved |

### 1.4 P4 — Repository hygiene (Ruleset &#47; Workflow inventory)

| Field | Value |
|---|---|
| Status | **DONE_READ_ONLY** |
| Classic branch protection | active and effective on `main` (`enforce_admins=true`; force-push disabled) |
| Required checks | **11** contexts identical to [`config&#47;ci&#47;required_status_checks.json`](../../config/ci/required_status_checks.json) |
| Disabled ruleset `peak_trade` (id `11192468`) | **SUPERSEDED &#47; REDUNDANT_WITH_BRANCH_PROTECTION &#47; HISTORICAL** — not `UNINTENTIONAL_DRIFT` |
| Local workflows | **73** |
| Remote API workflow records | **80** |
| Remote-only without file on `origin&#47;main` | **7** = `HISTORICAL_API_RECORD` (incl. Copilot dynamic path); not operational drift |
| Actual ruleset drift count | **0** |
| Actual workflow drift count | **0** |
| GitHub mutation required | **no** |
| Optional later disable of historical remote API records | not mandatory; requires separate Operator-GO |

# Verbleibende Restlücken nach Audit-Closeout

### A. CONFIRMED_DEFECT

| ID | Status | Evidenz | Risiko | Voraussetzung | Operator-GO | Priorität | Nächste Aktion |
|---|---|---|---|---|---|---|---|
| _(none)_ | — | Repo closeout evidence shows no confirmed open defect from P1–P4 | — | — | no | — | **NO_ACTION** |

`CONFIRMED_DEFECT_COUNT=0`

### B. ACCESS_OR_CREDENTIAL_BLOCKED

| ID | Status | Evidenz | Risiko | Voraussetzung | Operator-GO | Priorität | Nächste Aktion |
|---|---|---|---|---|---|---|---|
| `AWS_PRIVATE_RESOURCE_FULL_VERIFY` | ACCESS_BLOCKED | AWS audit: many list&#47;get APIs `ACCESS_DENIED`; inventory partial by design | Incomplete private AWS visibility; not proven trading-core defect | Broader read-only IAM on audit role | **yes** | operator-optional | Expand read-only IAM then re-audit; or accept residual ACCESS_BLOCKED |
| `OKX_PRIVATE_AUTH_RECON_BALANCE` | ACCESS_BLOCKED | OKX audit: credentials ABSENT; private auth&#47;recon&#47;balances `NOT_VERIFIABLE` | Incomplete private venue visibility | Read-only credentials + safe probe plan | **yes** | operator-optional | Provide readonly credentials under GO; re-run private probes |

`ACCESS_BLOCKED_GAP_COUNT=2`

### C. INTENTIONAL_GOVERNANCE_DEBT

| ID | Status | Evidenz | Risiko | Voraussetzung | Operator-GO | Priorität | Nächste Aktion |
|---|---|---|---|---|---|---|---|
| `RISK_SIZING_OWNER_CONSOLIDATION` | NOT_STARTED | Risk&#47;Sizing inventory DONE; consolidation explicit NOT_STARTED | Latent multi-owner complexity; not active leak | Separate architecture decision | **yes** (before any rewire) | deferred | **NO_ACTION** until architecture GO |
| `LEGACY_ORDER_INTENT_CONSOLIDATION` | NOT_STARTED | Legacy Order Intent inventory DONE via PR `#5296` | Latent multi-path intent; authority leak false | Separate architecture decision | **yes** | deferred | **NO_ACTION** until architecture GO |
| `LEGACY_ORDER_INTENT_DECOMMISSION` | NOT_STARTED | Inventory markers; decommission not started | Premature decommission risk if forced | Consolidation decision first | **yes** | deferred | **NO_ACTION** until architecture GO |

These are **not** automatic next implementation tasks.

`INTENTIONAL_GOVERNANCE_DEBT_COUNT=3`

### D. OPTIONAL_HYGIENE

| ID | Status | Evidenz | Risiko | Voraussetzung | Operator-GO | Priorität | Nächste Aktion |
|---|---|---|---|---|---|---|---|
| `HISTORICAL_REMOTE_WORKFLOW_API_RECORDS` | OPTIONAL | 7 remote-only API records without file on `origin&#47;main`; no recent operational runs | Cosmetic Actions UI&#47;API noise; no protection loss | Operator decision to disable stale workflow records | **yes** | low | **NO_ACTION** unless operator requests hygiene |
| `DISABLED_HISTORICAL_RULESET_PEAK_TRADE` | OPTIONAL | Ruleset `peak_trade` disabled; classic BP is effective SSOT | None while BP intact | Operator decision to delete&#47;leave disabled | **yes** | low | **NO_ACTION** (leave superseded&#47;disabled) |

`OPTIONAL_HYGIENE_COUNT=2`

### E. INTENTIONAL_BLOCKED_STATE

| ID | Status | Evidenz | Risiko | Voraussetzung | Operator-GO | Priorität | Nächste Aktion |
|---|---|---|---|---|---|---|---|
| `ECONOMIC_GATE_FAIL` | INTENTIONAL_BLOCKED | Gate remains fail-closed by design | — | Explicit live&#47;economic GO (out of scope) | **yes** for any change | n&#47;a | **NO_ACTION** (not a residual defect) |
| `PROMOTION_BLOCKED` | INTENTIONAL_BLOCKED | Promotion remains blocked&#47;non-authorizing outside inventory | — | Separate promotion GO | **yes** | n&#47;a | **NO_ACTION** |
| `RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED` | INTENTIONAL_BLOCKED | Bridge bound, not activated | — | Runtime activation GO | **yes** | n&#47;a | **NO_ACTION** |
| `LIVE_BLOCKED` | INTENTIONAL_BLOCKED | `LIVE_AUTHORIZED=false` | — | Live GO | **yes** | n&#47;a | **NO_ACTION** |
| `ORDERS_BLOCKED` | INTENTIONAL_BLOCKED | `ORDERS_ENABLED=false` | — | Orders GO | **yes** | n&#47;a | **NO_ACTION** |
| `RESEARCH_HOLD` | INTENTIONAL_BLOCKED | Research&#47;promotion hold remains intentional | — | Research release GO | **yes** | n&#47;a | **NO_ACTION** |

These states **must not** be tracked as residual defects.

`INTENTIONAL_BLOCKED_STATE_COUNT=6`

## 3. Definition of Done (reconciled)

System-audit closeout is **DONE** when all of the following hold:

1. **Repo-internal remediable drifts** from the P1–P4 campaign are closed on `main` (GitHub SSOT sync, tombstone docs, Surface-P contract, promotion&#47;risk&#47;legacy inventories, monitoring topology documentation).
2. **External&#47;private surfaces** are either verified under safe read-only probes **or** explicitly classified `ACCESS_OR_CREDENTIAL_BLOCKED` with evidence (AWS private&#47;resource-level; OKX private auth&#47;recon&#47;balances). Completeness is **not** required when access boundaries prevent verification.
3. **Intentional governance debt** (Risk&#47;Sizing consolidation; Legacy Order Intent consolidation&#47;decommission) is inventoried and marked `NOT_STARTED` — not silently treated as open defects or automatic implementation queue.
4. **Intentional blocked runtime&#47;economic states** (Economic Gate FAIL, promotion blocked, Runtime Bridge `BOUND_NOT_ACTIVATED`, live&#47;orders blocked, research hold) are recorded under category E and **are not defects**.
5. **Single plan truth:** this file is the only active repo SSOT for `Peak_Trade_Prioritaetenplan_Systemaudit_2026-07-17`. Desktop&#47;external copies are non-binding. Child audits under `docs&#47;audits&#47;` and inventory SSOTs under `docs&#47;governance&#47;` remain detail owners — not competing priority plans.

Out of scope for this Definition of Done: enabling live&#47;orders, activating Runtime Bridge, mutating GitHub protection&#47;rulesets&#47;workflows, expanding AWS IAM, supplying OKX credentials, or consolidating governance owners.

## 4. Related detail owners (reuse-before-new)

| Surface | Owner |
|---|---|
| Required checks SSOT | `config&#47;ci&#47;required_status_checks.json` |
| Promotion inventory | `docs&#47;governance&#47;PROMOTION_OWNER_AND_GATE_INVENTORY_SSOT_V1.md` |
| Risk&#47;Sizing inventory | `docs&#47;governance&#47;RISK_SIZING_OWNER_INVENTORY_SSOT_V1.md` |
| Legacy Order Intent inventory | `docs&#47;governance&#47;LEGACY_ORDER_INTENT_INVENTORY_SSOT_V1.md` |
| AWS audit | `docs&#47;audits&#47;AWS_INFRASTRUCTURE_READ_ONLY_AUDIT_2026-07-17.md` |
| OKX audit | `docs&#47;audits&#47;OKX_INTEGRATION_READ_ONLY_AUDIT_2026-07-17.md` |
| Monitoring audit | `docs&#47;audits&#47;MONITORING_TOPOLOGY_READ_ONLY_AUDIT_2026-07-17.md` |
| Ruleset&#47;workflow inventory | read-only audit result absorbed in §1.4 (no separate mutation) |

## 5. Next canonical priority

`NONE_PENDING_OPERATOR_DECISION`

No automatic implementation follow-up from this closeout. Any next work must be an explicit operator choice among:

- ACCESS_BLOCKED re-verification (AWS IAM expand / OKX readonly credentials) under GO  
- INTENTIONAL_GOVERNANCE_DEBT architecture decision under GO  
- OPTIONAL_HYGIENE under GO  
- leave intentional blocked states unchanged
