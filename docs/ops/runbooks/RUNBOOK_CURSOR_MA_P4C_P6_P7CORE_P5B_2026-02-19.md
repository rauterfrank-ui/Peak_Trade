# Peak_Trade — Cursor Multi‑Agent Orchestrator Runbook (P4C → P6 → P7 Core → P5B)
**Runbook ID:** `RUNBOOK_CURSOR_MA_P4C_P6_P7CORE_P5B_2026-02-19`  
**Scope:** L2 Market Outlook (P4C), Shadow stability (P6), Paper simulator core (P7 Core), Evidence pipeline CI truth (P5B)  
**Audience:** Operator running Cursor Multi‑Agent Orchestrator in the Peak_Trade repo  
**Repository root:** `Peak_Trade&#47;`  
**Default branch:** `main`  
**Safety posture:** No Live trading. Everything produces evidence packs and hard gates.

---

## 0) Operating Contract (must-read)

### 0.1 Execution contexts (Git level)
Every command block explicitly states the required Git context:
- **Context A:** `main` (clean, synced to `origin&#47;main`)
- **Context B:** feature branch `feat&#47;<slug>` (based on `origin&#47;main`)
- **Context C:** post-merge cleanup on `main`

### 0.2 Global invariants
- Working tree must be clean before creating PRs.
- `out&#47;` remains untracked unless the repo policy explicitly tracks specific evidence pointers.
- Every bundle produces an **Evidence Pack** with checksums and a validation token.
- CI must be the source of truth: required checks fail on invalid evidence.

### 0.3 Definitions
- **Evidence Pack:** a deterministic folder containing `manifest.json`, `index.json`, checksums, and referenced artifacts.
- **Golden fixture:** stable test input&#47;output used for snapshot&#47;semantic assertions.
- **DoD:** Definition of Done (must be met before merging).

---

## 1) Multi‑Agent Orchestrator plan

### 1.1 Recommended agent set (9 agents)
You can run with 7 agents by merging roles; 9 is clearer and reduces context mixing.

1. **Orchestrator**
   - Owns the plan, assigns work, enforces gates, merges results.
2. **Repo Scout**
   - Locates files, existing runbooks, scripts, schemas, prior work.
3. **Spec Engineer**
   - Writes&#47;updates schemas, contracts, and canonical JSON definitions.
4. **Implementation Engineer**
   - Implements core logic in `src&#47;` + scripts in `scripts&#47;`.
5. **Test Engineer**
   - Adds fixtures, golden tests, invariants, regression tests.
6. **Evidence Engineer**
   - Ensures evidence generation&#47;validation, indexing, checksums.
7. **CI Engineer**
   - Adds required checks, wiring in GitHub Actions, failure modes.
8. **Docs Engineer**
   - Updates runbooks, quickstart snippets, operator guidance.
9. **Auditor**
   - Performs final sanity checks, verifies DoD, prepares merge&#47;closeout tokens.

### 1.2 Agent handoff artifacts (per PR)
Each PR MUST produce:
- `out&#47;ops&#47;<bundle>&#47;PR_<N>_CLOSEOUT_DONE.txt` (or equivalent) + `.sha256`
- Evidence pack folder and validation token (`VALIDATION_OK*.txt`)
- A short PR body section: Change &#47; Reason &#47; Validation &#47; Evidence pointers

---

## 2) Entry points and exit points

### 2.1 Entry criteria (before starting PR1)
All must be true:
- You are in repo root (`pwd` shows Peak_Trade).
- `main` is clean and synced to `origin&#47;main`.
- Tooling available: `python`, `pytest`, `ruff` (or project equivalents).
- No pending local experimental changes.

### 2.2 Global exit criteria (after PR4)
All must be true:
- P4C, P6, P7 Core and P5B merged to `main`.
- Required CI checks enforced: `tests`, `ruff`, `evidence-validate` (names may vary but must be required).
- Evidence packs for each bundle exist and validate locally and in CI.
- Post-merge closeout completed; feature branches deleted locally and (optionally) remotely.
- A final handoff file exists under `out&#47;ops&#47;` summarizing all bundles and hashes.

---

## 3) Preflight (Context A: main)

### 3.1 Preflight commands
**Git context:** `main` (clean, synced)

```bash
cd /path/to/Peak_Trade
git checkout main
git fetch origin --prune
git pull --ff-only origin main
git status -sb
python --version
pytest -q
ruff check .
```

### 3.2 Preflight gate
Pass if:
- `git status -sb` shows `## main...origin&#47;main` and clean
- `pytest` and `ruff` succeed

If this fails: stop and fix before proceeding.

---

## 4) Bundle PR1 — P4C: L2 Market Outlook (Regimes + NO‑TRADE)

### 4.1 Goal
Produce deterministic L2 market outlook output + NO‑TRADE triggers with schemas, fixtures and evidence.

### 4.2 DoD (PR1)
- Canonical `market_outlook.json` schema is defined and enforced.
- ≥3 golden fixtures (regime + no-trade variants).
- Tests validate schema + deterministic&#47;semantic invariants.
- Evidence pack created + validated + indexed.
- `pytest -q` and `ruff check .` green.

### 4.3 Entry point
**Git context:** create feature branch from `main`

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feat/p4c-l2-market-outlook
```

### 4.4 Implementation checklist (agents)
- Repo Scout: find existing L2&#47;L3 docs and any P4B&#47;P4C placeholders.
- Spec Engineer: define schema `market_outlook.json` (canonical fields).
- Implementation Engineer: implement regime computation + no-trade evaluation.
- Test Engineer: add golden fixtures + tests (schema + invariants).
- Evidence Engineer: integrate evidence pack generation for P4C runs.
- Docs Engineer: add short operator doc (how to run P4C and where outputs go).

### 4.5 Required outputs
- `out&#47;ops&#47;p4c_runs&#47;<ts>&#47;market_outlook.json`
- Evidence pack `out&#47;ops&#47;evidence_packs&#47;pack_p4c_<ts>&#47;`
- Validation token `out&#47;ops&#47;VALIDATION_OK_P4C.txt` (or P4C‑scoped)

### 4.6 Local validation (Context B: feat&#47;p4c-l2-market-outlook)
```bash
ruff check .
pytest -q
python scripts/aiops/run_l2_market_outlook.py
python scripts/aiops/generate_evidence_pack.py --input out/ops/p4c_runs --output out/ops/evidence_packs
python scripts/aiops/validate_evidence_pack.py --latest
```

### 4.7 Exit point (ready for PR)
Pass if:
- tests + lint green
- evidence pack validates

Then:
```bash
git add -A
git commit -m "feat(p4c): L2 market outlook regimes + no-trade + evidence"
git push -u origin HEAD
```

Create PR via your canonical safe flow script if present, otherwise with `gh pr create`.

---

## 5) Bundle PR2 — P6: Shadow Mode Stability (Contracts + 3-run gate)

### 5.1 Goal
Freeze shadow session input&#47;output contract and enforce stability with a 3-run regression gate.

### 5.2 DoD (PR2)
- Input schema and output schema exist for shadow sessions.
- `run_shadow_session` produces deterministic core artifacts for identical inputs.
- A 3-run stability test exists (hash&#47;semantic stable) with allowed variance only for timestamps.
- Evidence pack per run + index append-only correctness.
- CI check `shadow-contract` (or equivalent) is required.

### 5.3 Entry point
**Git context:** create feature branch from `main` (after PR1 merged, otherwise rebase on main tip)

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feat/p6-shadow-contract-stability
```

### 5.4 Implementation checklist (agents)
- Spec Engineer: define `shadow_session_config.json` and `shadow_session_result.json` schemas.
- Implementation Engineer: harden `scripts&#47;aiops&#47;run_shadow_session.py` (deterministic run_id, stable paths).
- Test Engineer: add contract tests + 3-run stability gate.
- Evidence Engineer: ensure evidence packs validate and index updates are deterministic.
- CI Engineer: wire `shadow-contract` as required.

### 5.5 Local validation (Context B: feat&#47;p6-shadow-contract-stability)
```bash
ruff check .
pytest -q
python scripts/aiops/run_shadow_session.py --config configs/shadow/default.json --run-tag p6_run1
python scripts/aiops/run_shadow_session.py --config configs/shadow/default.json --run-tag p6_run2
python scripts/aiops/run_shadow_session.py --config configs/shadow/default.json --run-tag p6_run3
python scripts/aiops/validate_shadow_stability.py --runs out/ops/shadow_runs --latest 3
python scripts/aiops/generate_evidence_pack.py --input out/ops/shadow_runs --output out/ops/evidence_packs
python scripts/aiops/validate_evidence_pack.py --latest
```

### 5.6 Exit point
```bash
git add -A
git commit -m "feat(p6): shadow session contracts + 3-run stability gate"
git push -u origin HEAD
```

---

## 6) Bundle PR3 — P7 Core: Paper Simulator Core (fills&#47;slippage&#47;fees) + integration

### 6.1 Goal
Implement deterministic paper execution core (fills&#47;slippage&#47;fees) and integrate into the pipeline so Shadow→Paper produces canonical artifacts.

### 6.2 DoD (PR3)
- Paper fill engine exists with configurable fee&#47;slippage models.
- Canonical `fills.json` and `account.json` produced deterministically.
- Unit tests + regression tests for monotonicity&#47;non-negativity invariants.
- Reconciliation remains green (no regression).
- Evidence pack validates.

### 6.3 Entry point
**Git context:** create feature branch from `main` (after PR2 merged)

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feat/p7-paper-sim-core
```

### 6.4 Implementation checklist (agents)
- Implementation Engineer: implement `PaperFillEngine` (deterministic) + models.
- Spec Engineer: define canonical schemas for `fills.json` and `account.json` if missing.
- Test Engineer: unit + invariant tests, reconciliation regression test.
- Evidence Engineer: evidence packs for P7 runs; stable checksums.
- Docs Engineer: minimal quickstart (run P7 core and locate outputs).

### 6.5 Local validation (Context B: feat&#47;p7-paper-sim-core)
```bash
ruff check .
pytest -q
python scripts/aiops/run_paper_trading_session.py --config configs/paper/default.json --run-tag p7_core
python scripts/aiops/generate_evidence_pack.py --input out/ops/p7_runs --output out/ops/evidence_packs
python scripts/aiops/validate_evidence_pack.py --latest
```

### 6.6 Exit point
```bash
git add -A
git commit -m "feat(p7): paper simulator core fills/slippage/fees + evidence"
git push -u origin HEAD
```

---

## 7) Bundle PR4 — P5B: Evidence pipeline CI truth (required check)

### 7.1 Goal
Make evidence validation a required CI check. Invalid&#47;missing packs must fail the PR.

### 7.2 DoD (PR4)
- Evidence validator is strict and deterministic.
- GitHub Actions job `evidence-validate` runs on PRs and is marked required.
- Failure modes are explicit and reproducible locally.
- Docs updated with “how to generate + validate evidence packs”.

### 7.3 Entry point
**Git context:** create feature branch from `main` (after PR3 merged)

```bash
git checkout main
git pull --ff-only origin main
git checkout -b feat/p5b-evidence-ci-required
```

### 7.4 Implementation checklist (agents)
- Evidence Engineer: confirm generator&#47;validator behavior and deterministic index ordering.
- CI Engineer: add workflow job and mark as required in repo settings (manual step if needed).
- Test Engineer: add a minimal failing fixture&#47;test case for validator.
- Docs Engineer: update runbook snippet.

### 7.5 Local validation (Context B: feat&#47;p5b-evidence-ci-required)
```bash
ruff check .
pytest -q
python scripts/aiops/validate_evidence_pack.py --latest
```

### 7.6 Exit point
```bash
git add -A
git commit -m "ops(p5b): evidence validate CI required check"
git push -u origin HEAD
```

---

## 8) Merge + Post‑Merge Closeout (Context C: main)

### 8.1 Merge gates (must be true in PR)
- CI checks green (tests, lint, evidence validate, shadow contract where applicable)
- Evidence pointers present in PR body
- Auditor signs off DoD

### 8.2 Post‑merge steps
**Git context:** `main` after each PR merge

```bash
git checkout main
git pull --ff-only origin main
python -m pytest -q
ruff check .
```

Then run your canonical closeout script(s) if present:
```bash
scripts/governance/post_merge_closeout.sh
```

Clean up feature branches:
```bash
git branch -D feat/p4c-l2-market-outlook
git branch -D feat/p6-shadow-contract-stability
git branch -D feat/p7-paper-sim-core
git branch -D feat/p5b-evidence-ci-required
```

Optional: delete remote branches after merge:
```bash
git push origin --delete feat/p4c-l2-market-outlook
git push origin --delete feat/p6-shadow-contract-stability
git push origin --delete feat/p7-paper-sim-core
git push origin --delete feat/p5b-evidence-ci-required
```

---

## 9) Final audit (hard exit)

### 9.1 Final verification (Context A: main)
```bash
git checkout main
git fetch origin --prune
git pull --ff-only origin main
git status -sb
pytest -q
ruff check .
python scripts/aiops/validate_evidence_pack.py --all
```

### 9.2 Final handoff artifact (required)
Create a single final summary file under `out&#47;ops&#47;` that includes:
- merged PR numbers + merge SHAs
- evidence pack directories + validation tokens
- sha256 checksums file reference

Template commands:
```bash
ts=$(date -u +"%Y%m%dT%H%M%SZ")
mkdir -p out/ops/final_handoff
printf "%s\n" "RUNBOOK_CURSOR_MA_P4C_P6_P7CORE_P5B_FINAL_HANDOFF ${ts}" > out/ops/final_handoff/HANDOFF_MAIN_${ts}.txt
shasum -a 256 out/ops/final_handoff/HANDOFF_MAIN_${ts}.txt > out/ops/final_handoff/HANDOFF_MAIN_${ts}.txt.sha256
```

Exit is PASS only if:
- `main` clean + synced
- all validations pass
- final handoff file + sha exist

---

## 10) Troubleshooting quick map

### Evidence pack fails validation
- Check generator and validator versions match.
- Ensure deterministic ordering in `index.json` and stable file lists.
- Remove timestamps from hashed “core” artifacts or whitelist timestamp fields.

### Shadow 3-run stability fails
- Identify nondeterminism sources (random seeds, iteration order, time-based IDs).
- Fix run_id generation and output paths.
- Separate allowed-variant fields (timestamps) from hashed core payload.

### Paper fill engine produces nondeterministic fills
- Ensure deterministic tie-breaking.
- Sort orders consistently.
- Seed any stochastic model (prefer removing randomness entirely for paper).

---

## Appendix A — Minimal PR body template
Use this template in each PR description:

- **Change:** <what changed>
- **Reason:** <why now>
- **Validation:** `pytest -q`, `ruff check .`, evidence validate commands
- **Evidence:** `out&#47;ops&#47;evidence_packs&#47;<pack_name>` + `VALIDATION_OK*.txt`

