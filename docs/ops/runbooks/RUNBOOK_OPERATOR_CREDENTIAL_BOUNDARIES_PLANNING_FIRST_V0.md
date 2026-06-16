# Secret Handling — Operator Runbook (Planning-First) v0

**Owner:** ops  
**Mode:** Docs-only orientation — **not** implementation approval, **not** a gate pass, **not** authorization to use live/testnet/broker/exchange credentials.

**Filename note:** Tracked as `RUNBOOK_OPERATOR_CREDENTIAL_BOUNDARIES_PLANNING_FIRST_V0.md` so the path is not excluded by the repo `.gitignore` pattern `*_secret*`.

**Authority:** This runbook does **not** change Master V2 / Double Play semantics, risk/kill-switch posture, or execution gates. **Docs ≠ Approval.** **Dashboard ≠ Freigabe.** **AI/Cursor ≠ Authority.**

---

## 1. Purpose

Peak_Trade **Secret Handling** stays **`YES_PLAN_FIRST`**: clarify **custody**, **boundaries**, and **who does what** before any vault integration or new automation.

**`IMPLEMENT_NOW=false`** unless explicitly superseded by a separate, human-approved change record.

---

## 2. What Cursor / AI May Do

- Draft or extend **docs-only** material: conventions, checklists, **placeholder** examples, links to existing contracts.
- Reference **secret and config names** that already appear in repo docs/tests (e.g. workflow `secrets.*` **identifiers** — **names only**).
- Propose **static** checks that do **not** require secret **values** (shape/ignore rules, reference inventories).

---

## 3. What Cursor / AI Must Never Do

- **Never** see, request, print, validate, rotate, fetch, infer, or “test” **real** secret values.
- **Never** paste tokens, keys, passwords, recovery codes, seed phrases, session cookies, or vault exports into prompts, repo files, tickets, or logs.
- **Never** run `gh secret list/view/set`, vault CLIs with auth, or broker/exchange connectivity that uses real credentials.
- **Never** start Uvicorn, scheduler, runtime, paper, shadow, **testnet**, **live**, broker, exchange, or order paths for the purpose of proving secrets work.

---

## 4. Human-Only (Operator / Account Holder)

- GitHub **billing/plan** checks and feature availability (e.g. Secret Scanning / Push Protection scope).
- **Enabling** org/repo security settings (Secret Protection, branch rules, etc.).
- **Creating, storing, rotating real values** for GitHub Actions Secrets, PATs, vault items, exchange/API keys.
- **Bitwarden Secrets Manager**, **1Password**, or other vault **account** creation and **real** secret entry.
- Any **exchange / API / broker / testnet / live** credential issuance, storage, or rotation.

---

## 5. Placeholder Examples (Not Real Secrets)

Use **only** clearly fake names for illustrations in docs and examples:

| Placeholder (example only) | Use |
|----------------------------|-----|
| `PEAK_TRADE_EXAMPLE_API_KEY` | Docs / training |
| `PEAK_TRADE_EXAMPLE_API_SECRET` | Docs / training |
| `PEAK_TRADE_EXAMPLE_WEBHOOK_SECRET` | Docs / training |
| `PEAK_TRADE_EXAMPLE_DEPLOY_TOKEN` | Docs / training |

**Do not** map these to real services or commit values. Real workflow secret **names** in this repo are frozen for visibility review in `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py` — treat that file as **inventory of names**, not values.

---

## 6. Local `.env` and Examples

- **Untracked:** real `.env`, `.cursor&#47;.env`, `docker&#47;.env`, `.bounded_pilot.env`, `.bounded_launch.env` (see `.gitignore`).
- **Tracked examples only:** placeholder names — e.g. `docker&#47;.env.example`, `.cursor&#47;.env.example` — **no** real credentials.
- **Bounded pilot / acceptance:** follow [LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md](../specs/LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md) and [LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md](LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md).

---

## 7. Kraken credential classification (names-only)

**`operator-stated`:** Kraken-related credentials may already exist in the operator environment. **Secret Handling** is therefore **active boundary management**, not hypothetical future work. This subsection lists **categories** and **reference ENV identifiers** that appear in **tracked** repo sources — **never** values, never live key material.

**Not derivable from Git (`unverified` in-repo):** Kraken account settings, per-key **permissions** (e.g. trade vs. read-only vs. withdraw), effective **scopes**, **rotation** cadence, and whether **separate** keys are used per use-case. Operators must verify in the **Kraken / account UI** and out-of-band records.

| Category | Reference ENV names (`documented` in repo) | Relative risk | Default / note |
|----------|----------------------------------------------|---------------|----------------|
| Private / authenticated **market data** | May require exchange keys for some feeds; public OHLCV paths often need **none** (`unverified` per deployment) | Medium–High if over-permissioned | Least privilege on Kraken side; do not infer from code alone |
| **Testnet / paper** exchange API | `KRAKEN_TESTNET_API_KEY`, `KRAKEN_TESTNET_API_SECRET` (e.g. `src/exchange/kraken_testnet.py`, CI workflows referencing `secrets.*`) | Medium (real API; not prod cash) | Must stay inside **Research → Shadow → Testnet → Live** ordering |
| Live **read-only** monitoring | No fixed repo-wide convention — operators may use dedicated read-only keys (`operator-stated`) | Medium if keys are not read-only | If introduced, pick **distinct** `*_ENV` names via **human** decision + separate small docs PR — do not overload live-trading names |
| **Live trading** | `KRAKEN_API_KEY`, `KRAKEN_API_SECRET` (e.g. `src/exchange/kraken_live.py`, bounded local launcher contract) | **Highest** | **Unusable by default** for Cursor, agents, or ad-hoc tests; requires separate Peak_Trade **gates** — **not** permitted by reading this runbook |
| Vault / secret-manager **machine** identity (future) | Illustrative only: §5 `PEAK_TRADE_EXAMPLE_*` — not live names | Varies | Real issuance **human-only**; Cursor never holds values |

**Exchange-side order permission ≠ Peak_Trade live approval (`operator-stated` nuance):** An exchange API identity may **intentionally** retain **Kraken-side** permission to **query**, **create/modify**, and **cancel** orders — aligned with a **long-term** Peak_Trade goal of **autonomous** execution **within** this codebase’s governance model. That exchange permission is **only technical capability** at the venue; it does **not**, by itself, constitute **current** live trading authorization, nor does it bypass Peak_Trade.

**What still gates real use:** **Master V2 / Double Play** contracts and semantics, **risk / KillSwitch** posture, **Live Gates**, explicit **enabled / armed** (and related) states where your config/runbooks require them, **confirm-token** requirements, **dry-run vs. non-dry-run** boundaries per the documented live/bounded-pilot flows (including criteria aligned with `is_live_execution_allowed()`), and **operator-approved** operational steps. **AI orchestration is not execution authority** (canonical vocabulary).

**Cursor:** may only work with **ENV / classification / runbook reference names** — **never** secret **values** or exchange key **aliases** recorded only in external systems. The **Live trading** table row remains **highest-risk** and **default unusable** for Cursor, agents, and impromptu validation calls.

**Pipeline guardrail:** Any Kraken credential use must preserve **Research → Shadow → Testnet → Live**; advancing toward **Live** remains **strictly gated** elsewhere (Master V2 / Double Play / risk / kill-switch docs — **not** overridden here).

**Cursor / AI:** Only **placeholders** and **reference names** per §2, §3, and §5 — **no** Kraken login, **no** API test calls, **no** runtime, scheduler, paper, testnet, or live starts to “confirm” keys.

**Vaults (Bitwarden Secrets Manager / 1Password):** Central custody becomes **more plausible** when multiple Kraken key sets exist; **all** setup, login, and secret **values** stay **human-gated** and **outside** Cursor, repo, prompts, and logs.

This is **not** a Kraken setup guide — **no** step-by-step exchange onboarding and **no** commands that authenticate to Kraken or dump environment values.

---

## 8. GitHub Actions Secrets (Names vs Values)

- Workflows may reference `${{ secrets.NAME }}` — **names** are reviewable in-repo; **values** exist only in GitHub.
- Cursor may adjust workflow **names** or docs **only** with explicit approval for repo edits and **never** to set or read values.

---

## 9. GitHub Secret Protection / Push Protection

- **Intent:** reduce accidental secret commits at the **platform** boundary.
- **Baseline (no snapshot below):** feature availability depends on GitHub plan/repo type; treat billing/feature matrix as **`unverified`** in-repo until a human confirms in the GitHub UI.

### Operator-verified GitHub UI snapshot (`operator-stated`)

**Method:** Human observation in **GitHub web UI** only — **not** Cursor, **not** `gh`/API reads of secret **values**, **not** automated scanning of credentials by AI in this repo.

- **Repository:** `rauterfrank-ui&#47;Peak_Trade`
- **Recorded (UTC):** `2026-05-12T22:42Z`
- **Secret scanning alerts:** enabled; **open alerts:** `0`; **closed alerts:** `0` (UI: no unresolved secrets / none open).
- **Secret Protection** (Advanced Security area): **enabled** (UI: active; disable control present).
- **Push protection:** **enabled** (UI: active; disable control present).

**Planning slice interpretation:** For **enabling Secret Protection + Push Protection + secret scanning alerts** on this repo, **no further GitHub account/security toggle is required *right now*** — **if** the above UI state still holds. Re-check after plan, org policy, transfers, or GitHub product changes.

**Explicitly not covered here (separate workstreams — do not expand this marker):** Dependabot alerts / security updates / grouped updates / version updates; Code scanning / CodeQL; Copilot Autofix; private vulnerability reporting; repository **Security policy** (`SECURITY.md`) authoring.

**Cursor boundary (unchanged):** Cursor/AI must **never** see, request, print, validate, rotate, fetch, infer, or test **real** secret values. This snapshot does **not** relax that rule and is **not** a gate pass or live approval.

---

## 10. Secret Managers (Future, Human-Managed)

**Bitwarden Secrets Manager** and **1Password** (or equivalents) may hold real material **outside** the repo. Target architecture may be documented in planning artifacts; **no** vault login, CLI session, or token setup belongs in this runbook as executable steps with real credentials.

---

## 11. Existing Repo Anchors (Reuse)

- CI / permissions / secrets audit index: [CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md](../CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md)
- Workflow secret reference visibility (names only): `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py`
- Governance **NO_SECRETS** discipline: `tests/governance/policy_critic/` (policy packs / rules — **repo-evidenced** surface)

---

## 12. Validation (Docs-Only Changes)

After editing related docs, operators may run:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

No secret values should appear in command output or committed files.

---

## 13. Stop Conditions

**Stop immediately** if any party requests:

- real secret values in chat or repo,
- pasting tokens into Cursor,
- GitHub/vault **mutation** as “quick proof”,
- testnet/live/broker secret **use** without separate approved controls,
- or treating this document as **signoff** or **gate pass**.

---

## 14. Revision

- **v0:** Planning-first operator runbook; docs-only; aligns with Tailscale **parked_not_discarded** marker and Secret Handling planning layer in the CI audit index.
- **v0.1:** Added `operator-stated` GitHub UI snapshot (Secret Protection, Push protection, secret scanning alert counts) for `rauterfrank-ui&#47;Peak_Trade`, recorded UTC `2026-05-12T22:42Z`. Docs-only; **non-authorizing**.
- **v0.2:** Added §7 Kraken **credential classification** table (names-only; `operator-stated` custody; active boundary management). No Kraken setup guide; **non-authorizing**.
- **v0.3:** §7 — clarified that **exchange-side** order permissions are **technical capability only** and **not** a Peak_Trade live/gate approval; restated gate stack and **highest-risk** default for Cursor. Docs-only; **non-authorizing**.
