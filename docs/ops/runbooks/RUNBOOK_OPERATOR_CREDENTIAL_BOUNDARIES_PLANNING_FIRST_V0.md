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

- **Untracked:** real `.env`, `.cursor/.env`, `docker/.env`, `.bounded_pilot.env`, `.bounded_launch.env` (see `.gitignore`).
- **Tracked examples only:** placeholder names — e.g. `docker/.env.example`, `.cursor/.env.example` — **no** real credentials.
- **Bounded pilot / acceptance:** follow [LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md](../specs/LOCAL_BOUNDED_SECRET_ENV_FILE_CONTRACT.md) and [LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md](LOCAL_BOUNDED_SECRET_LAUNCHER_RUNBOOK.md).

---

## 7. GitHub Actions Secrets (Names vs Values)

- Workflows may reference `${{ secrets.NAME }}` — **names** are reviewable in-repo; **values** exist only in GitHub.
- Cursor may adjust workflow **names** or docs **only** with explicit approval for repo edits and **never** to set or read values.

---

## 8. GitHub Secret Protection / Push Protection

- **Intent:** reduce accidental secret commits at the **platform** boundary.
- **Operator:** verify availability and enablement in GitHub UI for **this** org/repo/plan — exact status is **not** asserted here (`unverified` for billing/feature matrix).

---

## 9. Secret Managers (Future, Human-Managed)

**Bitwarden Secrets Manager** and **1Password** (or equivalents) may hold real material **outside** the repo. Target architecture may be documented in planning artifacts; **no** vault login, CLI session, or token setup belongs in this runbook as executable steps with real credentials.

---

## 10. Existing Repo Anchors (Reuse)

- CI / permissions / secrets audit index: [CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md](../CI_GITHUB_ACTIONS_PERMISSIONS_SECRETS_ARTIFACTS_AUDIT_INDEX_V0.md)
- Workflow secret reference visibility (names only): `tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py`
- Governance **NO_SECRETS** discipline: `tests/governance/policy_critic/` (policy packs / rules — **repo-evidenced** surface)

---

## 11. Validation (Docs-Only Changes)

After editing related docs, operators may run:

```bash
uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs
bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs
```

No secret values should appear in command output or committed files.

---

## 12. Stop Conditions

**Stop immediately** if any party requests:

- real secret values in chat or repo,
- pasting tokens into Cursor,
- GitHub/vault **mutation** as “quick proof”,
- testnet/live/broker secret **use** without separate approved controls,
- or treating this document as **signoff** or **gate pass**.

---

## 13. Revision

- **v0:** Planning-first operator runbook; docs-only; aligns with Tailscale **parked_not_discarded** marker and Secret Handling planning layer in the CI audit index.
