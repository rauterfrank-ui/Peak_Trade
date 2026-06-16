# ZAP / DAST SHADOW–STAGING ADOPTION CONCEPT V0

Documentation-only. This file does not authorize scans, installs, CI changes, workflow dispatches, web servers, target URLs, runtime execution, or any trading, broker, exchange, or order activity.

## 1. Purpose

Capture a **manual-first, default-off** adoption model for optional **OWASP ZAP** (or similar **DAST**) against **explicitly approved** **local operator workstations**, **private shadow**, or **non-production staging** HTTP surfaces that represent Peak_Trade **read-only** UIs or companion apps — **without** CI gates, **without** automatic remediation, and **without** touching Master V2 / Double Play execution semantics. The goal is **bounded dynamic-analysis hygiene** complementary to **SAST/static** posture in [`SEMGREP_SAST_ADOPTION_CONCEPT_V0.md`](SEMGREP_SAST_ADOPTION_CONCEPT_V0.md) and **docs-only** CI/secrets governance in [`CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md`](../CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md).

## 2. Non-goals

- No **ZAP install**, **ZAP execution**, or **target scanning** in this markdown slice or as a consequence of merging this doc alone.
- No **live**, **public internet**, or **third-party** targets unless each is **explicitly** named and approved in a **separate** operator charter (outside this v0 file).
- No **required** PR or merge-blocking CI gate in v0; no **`workflow_dispatch`** ZAP automation in v0.
- No **Uvicorn**, **reverse proxy**, or **web server** start instructions in-repo for the purpose of enabling scans.
- No secrets in URLs, headers, configs, prompts, reports, logs, or screenshots; no **real** credential validation or Kraken/account exercise.
- No scheduler, paper, testnet, live, broker, or exchange paths; **Dashboard ≠ Freigabe**; **AI ≠ Authority**, **Signal ≠ Trade**, **Docs ≠ Approval**.

## 3. v0 Adoption Model

- **Phase v0:** concept and operator discipline only — **documented**, not enforced by repo automation.
- **Phase next (explicit future PR):** optional **operator-run** local ZAP (or equivalent) on an **allowlisted** target only, with written scope; still **not** default-on org-wide.
- **Phase later (explicit future PR):** optional **manual-only** CI pattern — never `schedule`-as-default, never required-on-PR unless a separate charter says otherwise.

Installation, execution, target selection, and workflow edits are **out of scope** for this v0 file alone.

## 4. Target Allowlist Model

Future scans (only after explicit operator approval) require **all** of:

- **Written allowlist entry:** hostname/IP (or `127.0.0.1`), port, path prefix, and environment label (`local-dev`, `shadow`, `staging`); **no** wildcards across environments.
- **Ownership:** an operator accountable for the target stack and for **stopping** the scan on scope drift.
- **Data classification:** no production user data, no real trading accounts, no secrets-in-URLs; **dummy/test** posture only unless separately approved with data-handling rules.
- **Prohibition:** any target not on the allowlist is **out of bounds** — including “helpful” surprises against public URLs or shared staging without written approval.

## 5. Passive / Baseline vs Active Scan Boundary

- **Default posture (conceptual):** restrict to **passive** or **baseline / spider-less** reconnaissance until an operator explicitly approves **active** rules (e.g. aggressive fuzzing, forced browsing) for a **specific** window.
- **Separation:** **passive/baseline** evidence informs hygiene; **active** techniques can increase load, noise, and accidental scope expansion — they require **separate** approval and tighter time boxes.
- **Conservative first:** broaden techniques only after false-positive and abort discipline are proven in passive/baseline runs.

## 6. Cursor Boundary

Cursor/agents **may**:

- Maintain or extend **this** conceptual doc and **safe** cross-links under `docs/` when explicitly tasked.
- Provide **checklist headings** and **placeholder** triage sections for humans (no executable scan recipes as mandatory steps).

Cursor/agents **must not**:

- Install or run ZAP (or analogous DAST) without explicit operator approval.
- Propose concrete scan URLs, auth headers, cookies, or tokens — **placeholders only**.
- Edit `.github&#47;workflows&#47;**` for ZAP except under a **separate** governance PR.
- Start Uvicorn, any web server, or any scheduler/runtime/paper/testnet/live path to “support” scanning.
- Read `.env*` or vault material to “validate” scans.

## 7. Operator Boundary

Operators:

- Approve **target**, **scope**, **timing**, **mode** (passive/baseline vs active), and **abort** criteria **before** any future scan.
- Run DAST only where **legal**, **contractual**, and **internal policy** allow; **no** unauthenticated surprise scanning of external systems.
- Keep reports **internal**; redact or avoid pastes that could leak secrets, session identifiers, or PII.
- Treat findings as **advisory**; **no** direct merge or runtime authority from scanner output.

## 8. Suggested Future Manual Workflow

Placeholder shape only — **not** runnable approval inside the repo:

1. Charter: allowlisted base URL, path scope, time window, passive vs active decision, owner on-call.
2. Ensure target stack is **non-live**, **non-broker-ordering**, and uses **non-secret** test posture.
3. Run **minimal** passive/baseline first (operator-local tooling install is **outside** v0 doc scope).
4. Store reports **locally** or in internal tickets; **no** raw secret-bearing artifacts in the repo.
5. Triage (§9); open **human-reviewed** PRs only for verified issues; **no** bot auto-fix from ZAP alone.

## 9. Findings Triage

- **Severity:** prioritize credible authZ/authN, injection, and misconfiguration on **in-scope** paths; defer noise.
- **Report-only in v0 mental model:** no pipeline that blocks merge solely on ZAP output unless a **future** explicit governance PR promotes it.
- **Human review:** every remediation goes through normal review; **docs** never approve merges or trading.

## 10. Future CI Considerations

If a separate PR ever adds CI integration for DAST:

- **`workflow_dispatch` only**, **default-off**, **not** on every PR.
- **No** publishing of artifacts that could leak URLs with embedded tokens, cookies, or environment-derived secrets.
- **No** `schedule` as default-on for DAST in the same PR that introduces it unless explicitly chartered.
- Reuse lessons from [`CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md`](../CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md).

## 11. Relationship to Semgrep / SAST Concept

- **SAST** (Semgrep): **static** — source and workflow text **without** serving HTTP from a target.
- **DAST** (ZAP): **dynamic** — HTTP conversation with a **running** application; therefore **higher** operational and scope risk.

The two are **complementary** and **independently optional**. Adopting one **does not** require adopting the other. Both remain **manual-first** and **default-off** in v0.

## 12. Stop Conditions

Suspend or halt expansion if:

- **Real secret exposure** or pressure to embed secrets for “realistic” scans.
- **Targets** outside the explicit **allowlist**, or **live/public production** scope creep.
- **Unauthenticated surprise scans** against external or shared infrastructure.
- **CI gate** or **required merge** blocking based on noisy DAST alone.
- **Service starts** (Uvicorn, proxies, schedulers) proposed solely to feed scans **without** governed charter.
- **Active** scan modes without explicit approval, or any tie-in to **testnet/live/broker/exchange/order** paths.

## 13. Final Status Lines

```
ZAP_DAST_ADOPTION_DOC_VERSION=v0
ZAP_DAST_DEFAULT_OFF=true
ZAP_DAST_REQUIRED_CI_GATE=false
ZAP_DAST_MANUAL_OPERATOR_FIRST=true
ZAP_INSTALLED_REPO=false
ZAP_RUN_IN_THIS_SLICE=false
DAST_TARGET_ALLOWLIST_REQUIRED=true
PASSIVE_OR_BASELINE_DEFAULT=true
AUTOMATIC_FIX=false
```
