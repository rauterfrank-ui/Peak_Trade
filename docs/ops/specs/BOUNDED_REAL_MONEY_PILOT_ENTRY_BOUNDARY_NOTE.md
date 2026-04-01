# Bounded Real-Money Pilot Entry Boundary Note

status: DRAFT  
last_updated: 2026-04-01  
owner: Peak_Trade  
purpose: Grenze zwischen **Dry-Validation / Spec-Flow** und **erstem Bounded-Real-Money-Schritt** klären; keinerlei Erweiterung von Execution Authority.  
docs_token: DOCS_TOKEN_BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE

## 1. Intent

This note clarifies the **operational boundary** between the spec-defined flow through **dry validation** and the **first bounded real-money pilot session**. It does not add execution authority or relax gates.

**Canonical end-to-end procedure (current repo):**  
`docs/ops/runbooks/RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`

---

## 2. Where the Spec Flow Ends vs. Where Real Money Begins

### 2.1 Flow through dry validation (no real orders)

The canonical **non-real-money** flow **ends** after successful dry validation:

| Step | Command / Action | Status |
|------|------------------|--------|
| A1 | `python3 scripts/run_live_dry_run_drills.py` | Implemented |
| A2 | `python3 scripts/ops/pilot_go_no_go_eval_v1.py` | Implemented |
| A3 | `python3 scripts/run_execution_session.py --dry-run` | Implemented (CLI flag: `--dry-run`) |
| B | Ops Cockpit review, gates GREEN | Operator |

### 2.2 First bounded real-money step (invocation path exists)

After all **Entry Contract** prerequisites and **`GO_FOR_NEXT_PHASE_ONLY`**, the **first bounded real-money session** is started via **one** of:

| Path | Command | Notes |
|------|---------|--------|
| **Recommended** | `python3 scripts/ops/run_bounded_pilot_session.py` | Runs go/no-go + cockpit, then hands off to `run_execution_session.py --mode bounded_pilot` unless `--no-invoke`. |
| **Operator-direct** | `python3 scripts/run_execution_session.py --mode bounded_pilot ...` | Same gates must already be satisfied manually. |

**Gate-only check (no session):**  
`python3 scripts/ops/run_bounded_pilot_session.py --no-invoke`

See: `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`, `RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md` (Step 5).

---

## 3. Relationship to Other Wrappers

- **`run_live_pilot_session.sh`:** Remains oriented toward **dry-run / testnet validation** (`PT_LIVE_DRY_RUN=YES` posture per that script). It is **not** the canonical first real-money bounded pilot path; use **`run_bounded_pilot_session.py`** or explicit **`--mode bounded_pilot`** per the runbook above.
- **Broad live** (non-pilot) remains **out of scope** here and stays governance-gated separately (`live_order_execution` **locked**).

---

## 4. Relationship

- Companion to: `BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT`
- Operative runbook: `RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md`
- Historical gap analysis: `BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE.md`
- Companion to: `RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW`
- Dry validation: `RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md`

## 5. Non-Goals

- No execution authority  
- No new gates or relaxation  
- No replacement for operator judgment  
