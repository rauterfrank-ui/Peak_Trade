---
docs_token: DOCS_TOKEN_MASTER_V2_CI_REQUIRED_CHECKS_SAFETY_GATE_POINTER_INDEX_V0
status: draft
scope: docs-only, non-authorizing CI / required-checks / safety-gate pointer index
last_updated: 2026-04-27
---

# Master V2 CI / Required-Checks / Safety-Gate Pointer Index V0

## 1. Executive Summary

This document is a **concise pointer index** for CI, required-checks, docs gates, policy/governance gates, and drift/reconciliation **surfaces**. It is **non-authorizing**. **CI green**, docs validation, policy checks, required checks, and reconciliation outputs are **engineering** and **review** surfaces. They are **not** live authorization, **not** trading authority, **not** signoff completion, **not** **strategy** readiness, **not** **autonomy** readiness, **not** Risk/KillSwitch **override**, and **not** Execution/Live **gate bypass**. **CI green** is also **not** **externally authorized** in the enablement sense.

This spec **does not** modify workflows, branch protection, required-checks configuration, source code, tests, registry behavior, runtime behavior, or Master V2 / Double Play semantics.

Planning context (read-only, not merged into this file): the drift scan under `/tmp/peak_trade_ci_required_checks_safety_gate_drift_scan_v0/CI_REQUIRED_CHECKS_SAFETY_GATE_DRIFT_SCAN_V0.md` — do **not** treat that file as a repo contract; this index is the **stable** navigation aid.

## 2. Purpose and Non-Goals

**Purpose**

- Stabilize **where to look** for CI, docs gates, policy gates, and required-checks reconciliation.
- Support operators and reviewers without **claiming** any **gate pass** or **signoff** from reading docs.

**Non-goals**

- No workflow, branch-protection, or required-checks **edits** via this page.
- No **live** enablement, no **go-live** **approval** narrative, no **gate-pass** **claim** in the positive sense.
- No **strategy-ready** or **autonomous-ready** **claim**.

## 3. CI / Required-Checks Pointer Table

| Surface | Path | Role | Read when | Not used for |
| --- | --- | --- | --- | --- |
| Main CI workflow | `.github/workflows/ci.yml` | Main PR/merge CI; includes contract jobs and test matrix. | You need the **central** check layout or job names. | **Not** live authorization; **not** **externally authorized** in the **trading** sense. |
| Docs token policy gate | `.github/workflows/docs-token-policy-gate.yml` | Enforces docs inline-code token policy. | `docs-token-policy-gate` fails. | **Not** signoff, **not** **production-ready** by itself. |
| Docs reference targets gate | `.github/workflows/docs_reference_targets_gate.yml` | Verifies referenced repo paths in Markdown. | `docs-reference-targets-gate` fails. | **Not** signoff **complete**. |
| Docs diff guard | `.github/workflows/docs_diff_guard_policy_gate.yml` | Policy/diff guard for selected docs. | `Docs Diff Guard Policy Gate` fails. | **Not** **approved**; **not** **gate passed** in the **trading** sense. |
| Workflow dispatch guard | `.github/workflows/ci-workflow-dispatch-guard.yml` | Validates `workflow_dispatch` and workflow safety; check name `dispatch-guard`. | Dispatch or workflow posture questions. | **Not** **live enablement**; **not** **live-ready**. |
| Policy Critic Gate (paths-filtered) | `.github/workflows/policy_critic.yml` | Policy / governance **review** for sensitive diffs. | `Policy Critic Gate` blocks or warns. | **Not** a substitute for `MASTER_V2` **gates**; **not** **strategy ready**; **not** **autonomy ready**. |
| Lint Gate (always run) | `.github/workflows/lint_gate.yml` | Ruff/format **engineering** **validation**; visible as `Lint Gate`. | `Lint Gate` fails. | **Not** readiness **approval**; **not** **signoff** **complete**. |
| PR-U / required-checks reconciliation | `.github/workflows/pru-required-checks-drift-detector.yml` | Reconciliation (historical **filename**; job `required-checks-reconciliation-check`) uses reconciler. | Reconciling **SSOT** with branch protection. | **Not** **runtime** safety by itself. |
| Required checks SSOT | `config/ci/required_status_checks.json` | `required_contexts` / `ignored_contexts` **inventory**. | “Which name is (not) in branch protection?” | **Not** the live GitHub **API**; **not** a **go** decision. |
| Reconciler (canonical) | `scripts/ops/reconcile_required_checks_branch_protection.py` | Reconcile/compare branch protection vs config (per workflow **mode**). | Running `--check` locally (same spirit as server path). | **Not** a **trading** **gate**; **not** Risk **override**. |
| Retired drift entrypoint | `scripts/ci/required_checks_drift_detector.py` | **Retired**; points to reconciler. | **Legacy** **naming** confusion only. | **Not** current **SSOT**; do **not** use as the only **truth** without reading error text. |
| Docs token policy (local) | `scripts/ops/validate_docs_token_policy.py` | Reproduce docs **token** **policy** locally. | Pre-PR or triage. | **Not** **approval**; **not** **autonomous-ready**. |
| Docs reference targets (local) | `scripts/ops/verify_docs_reference_targets.sh` | Reproduce **reference-targets** gate locally. | Pre-PR or triage. | **Not** signoff, **not** **live** **authorization**. |
| CI / required-checks tests | `tests/ci/` | Characterization and contracts for check wiring. | Understanding **naming** or **reconciliation** tests. | **Not** **production-ready**; **not** **gate passed** in **ops** terms. |
| Governance tests (if used) | `tests/governance/` | Governance-related test surface (when present). | Policy-related test discovery. | **not** **live** **authority** from tests. |

**Note on `lint.yml`:** there is a separate `lint` workflow; **branch-protection**-aligned “Lint **Gate**” in SSOT is the **`lint_gate.yml`** / `Lint Gate` name — confirm **check name** in GitHub, not just filename.

## 4. Docs Gates

Docs gates are **engineering validation** surfaces for the documentation tree.

**Common local reproduction (repo root):**

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

- These commands **reproduce** parts of the docs CI posture; a **pass** is **not** signoff, **not** **gate** passage for trading, and **not** **signoff** **complete** in the operational **authority** sense.

- Operator packaging (when applicable): `scripts/ops/pt_docs_gates_snapshot.sh` and runbooks under `docs/ops/runbooks/` (e.g. **Docs** **Gates** quickstarts) — use those as **process** **pointers**, not **autonomy** **readiness**.

## 5. Policy / Governance / Safety Gates

- **Policy Critic** and related workflows are **governance** and **wording** **review** layers for sensitive areas (`policy_critic.yml` paths, see file). A **block** is a **PR** / **governance** outcome, **not** an Execution or Live **bypass** **authority**.
- **Dispatch guard** and **required-checks** **hygiene** workflows are **CI** and **naming** **safety**; they do not grant **trading** **authority**.

## 6. Required-Checks SSOT and Reconciliation Surfaces

- **SSOT** file: `config/ci/required_status_checks.json` — documents `required_contexts` and `ignored_contexts` (see **inline** `notes` in the JSON; semantics are **not** redefined here).
- **Reconciliation** is invoked in **canonical** form via `scripts/ops/reconcile_required_checks_branch_protection.py` (see `pru-required-checks-drift-detector.yml` for **which** `event` types run **live** branch protection reads — **PR** may **skip** that path per workflow comments). **read-only** triage: trust **workflow** **comments** + `tests/ci/` for behavior.

## 7. Test and Validation Surfaces

- **`tests/ci/`** — `required_checks`, **pr-head** liveness, **reconciliation** narrative tests, and related **contracts** (non-authority; help prevent **naming** **drift**).
- **Root `pytest` / `ci.yml` matrix** — application test matrix is an **engineering** **validation** surface, **not** a **go-live** **signoff** **surface**.

## 8. Master V2 / Double Play / Live Safety Relevance

- **No** CI surface in this table **replaces** Master V2 / Double Play **trading** **logic**, **Risk** / **KillSwitch**, **Execution** / **Live** **Gates**, or **dashboard** / **cockpit** **authority** **contracts** — see [`MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md`](./MASTER_V2_SYSTEM_DATAFLOW_AND_AI_LAYER_OVERVIEW_V0.md) for **positioning** (non-substitutive), [`MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md`](./MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md) for **read-only** **session** **review** **packs**, and [`MASTER_V2_OPERATOR_TRIAGE_OPEN_FIRST_CHECKLIST_V0.md`](./MASTER_V2_OPERATOR_TRIAGE_OPEN_FIRST_CHECKLIST_V0.md) for **triage** **first**.

## 9. Drift and Naming Notes

- **Retired** script `scripts/ci/required_checks_drift_detector.py` — **use** the message / reconciler it points to; do **not** treat the **old** name as the **SSOT** path.
- **Workflow** filename `pru-required-checks-drift-detector.yml` **vs.** job / reconciler **semantics** — “drift” in the name is **legacy**; behavior is **reconciliation**-oriented (see `tests/ci/test_pru_required_checks_drift_detector.py`).
- **Check** **names** in GitHub (job `name:`) are **stability**-sensitive; see [`ci_required_checks_matrix_naming_contract.md`](../ci_required_checks_matrix_naming_contract.md) for **naming** **rules** (pointer only, not re-specified here).

## 10. Authority Boundaries

- **This index** and **all** **CI** ** greens** are **pointers** and **validation** **results**, **not** **live** **authorization**, **not** **signoff** **complete** in the **trading** sense, and **not** **strategy** **ready** or **autonomy** **ready** as **operational** **claims**.

## 11. Safe Use Checklist

- Use this page to **find** workflows and **scripts**; do **not** infer **go** or **not** from green alone.
- For **governance** **blocks** (Policy Critic, docs gates), follow **triage** and **Master** **V2** **specs**; ambiguity ⇒ **not** a **trading** **decision** from **CI** **alone**.
- For **reconciliation** questions, use **SSOT** JSON + reconciler + **tests**, **not** this markdown as **the** **API** **truth** for **branch** **protection** **at** **runtime** **on** **GitHub**.

## 12. Known Ambiguities

- **Exact** set of **required** **checks** on `main` is **enforced** by **GitHub** **branch** **protection**; the JSON is an **intended** **inventory** and may have **intentional** `ignored_contexts` — see `notes` in `config/ci/required_status_checks.json`.
- **Multiple** `lint*`-style workflows may exist; **use** the **check** **name** that **matches** your **failing** **PR** **check**, not the filename **alone**.

## 13. Validation Notes

From repo root (when changing this file or any tracked `docs/**` **Markdown**):

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

- **read-only** **validation** of **documentation** only — **not** a **trading** **gate** **result**.
