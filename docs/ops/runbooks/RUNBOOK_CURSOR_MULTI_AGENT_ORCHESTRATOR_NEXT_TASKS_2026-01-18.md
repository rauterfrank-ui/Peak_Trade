# RUNBOOK — Cursor Multi-Agent Orchestrator: Next Tasks (v2026-01-18)

**Mode:** Snapshot-only (kein Watch), governance-safe, **NO-LIVE**  
**Audience:** Operator + Cursor Multi-Agent Chat  
**Goal:** Ein einheitliches “bis-finish” Operating System fuer alle naechsten Aufgaben (Docs, CI, Forensics, Evidence, Phase 16A/B Execution).

---

## Rollen (Cursor Multi-Agent)

- **A0 ORCHESTRATOR**: fuehrt Phasen, stoppt bei Scope-Drift, entscheidet Go/No-Go.
- **A1 SCOPE_KEEPER**: erzwingt erlaubte Pfade, verhindert Live-/Execution-Footguns.
- **A2 CI_GUARDIAN**: Snapshot-only Status, keine Watch-Loops, keine Auto-Merges ohne Gate.
- **A3 EVIDENCE_SCRIBE**: schreibt Evidence exakt (verbatim), keine Semantik-Aenderungen.
- **A4 DOCS_GATES_GUARDIAN**: token-policy / reference-targets / diff-guard Operator.
- **A5 RISK_OFFICER**: bewertet Risiko (LOW/MED/HIGH), definiert Rollback.
- **A6 FORENSICS_KEEPER**: fsck/worktrees/objstore Hygiene, kein destruktives rm ohne Plan.

---

## Global Guardrails

### G0 — Continuation Guard
Wenn du in der Shell `>`, `dquote>`, `heredoc>` siehst: **Ctrl-C**.  
Keine “watch” Kommandos. Nur Snapshot.

### G1 — Repo Anchoring (immer am Anfang)
Pre-Flight Snapshot:
- `pwd`
- `git rev-parse --show-toplevel`
- `git status -sb`

### G2 — Scope Policy (Default)
- **Docs-only**: writes nur unter `docs&#47;**` (oft `docs&#47;ops&#47;**`).
- **Code-Slice**: nur explizit benannte Files/Dirs, minimal-invasive.
- **NO-LIVE**: kein live executor dispatch, keine Exchange API Calls.
- **Additive-first**: bei Docs moeglichst additiv; wenn edit, nur targeted.

### G3 — Evidence-Philosophie
- Evidence ist **verbatim** (copy/paste) und deterministisch.
- Evidence-Dateien sind **klein**, eindeutig datiert, und referenzierbar.

---

## Phase P0 — Pre-Flight & Anchoring Pass (Docs-only)

**Ziel:** Sicherstellen, dass Operator im Repo ist und Basis-Anchor-Pfade existieren.

**Commands (Snapshot-only):**
1) `pwd`
2) `git rev-parse --show-toplevel`
3) `git status -sb`
4) Anchoring Check (python3):
   - `python3 - <<'PY' ... PY`

**Acceptance:**
- Repo root korrekt
- `## <branch>...origin&#47;<branch>` sichtbar
- Anchor-Pfade: alle `OK`

**Evidence Template:**
- `docs&#47;ops&#47;evidence&#47;EVIDENCE_P0_PREFLIGHT_*.md`

---

## Phase P1 — Git Forensics Hygiene (fsck / worktrees / gc)

**Ziel:** Reproduzierbare Diagnose, **kein** destruktives Cleanup ohne Nachweis.

**Snapshot Commands:**
- `git fsck --full --no-reflogs`
- `git worktree list --porcelain`
- `git count-objects -vH`

**Decision Rules:**
- Keine `fatal&#47;error&#47;corrupt&#47;missing` → **FSCK_OK**
- “unreachable” ohne fatal → erwartbar (dangling), dokumentieren.
- Worktree “prunable” → kann per `git worktree prune` bereinigt werden.

**Evidence:**
- `.tmp&#47;git-forensics&#47;fsck_*.txt` + Evidence Doc unter `docs&#47;ops&#47;evidence&#47;`.

---

## Phase P2 — PR Slice Workflow (Docs-only / Code)

**Ziel:** Minimaler PR-Slice, sauberer Scope, deterministische Verifikation.

**Standard Ablauf:**
1) Branch erstellen (benannt, datiert)
2) Aenderungen minimal
3) Pre-commit (lokal)
4) Push + PR
5) CI Snapshot (no-watch)
6) Merge (squash) + Post-Merge Snapshot

**CI Snapshot (no-watch):**
- `gh pr checks <PR> --json name,state,link --jq ...` (oder Standard-Helper)

**Gates:**
- docs-token-policy-gate
- docs-reference-targets-gate
- docs-diff-guard-policy-gate
- lint/tests (wenn Code)

---

## Phase P3 — Evidence + Evidence Index Updates

**Ziel:** Neue Evidence Artefakte in `docs&#47;ops&#47;evidence&#47;` erstellen und in `docs&#47;ops&#47;EVIDENCE_INDEX.md` eintragen.

**Rules:**
- Evidence Entry: kurze Claim + Verifikation + Source (PR/Merge Log/Commit)
- Token-Policy: illustrative slashes als `&#47;` wenn in inline code.

**Acceptance:**
- Evidence Files existieren
- Evidence Index hat neue Entries und Links resolven

---

## Phase P4 — Merge-Log PR Chain (Standard)

**Ziel:** Nach Merge eines PRs einen Merge Log PR erstellen (docs-only), nach Muster.

**Template Sections (kompakt):**
- Summary / Why
- Changes
- Verification (CI Snapshot + merge readiness)
- Risk
- Operator How-To
- References (PR Link, mergeCommit oid)

---

## Phase P5 — ExecutionPipeline Phase 16A/B Slice: Fill Dedupe / Idempotency (CODE)

**Problem Statement:**
- `DuplicateFillConflictError` existiert, wird aber nicht verwendet.
- `OrderFill` hat kein `fill_id`. Executors setzen `execution_id` in `metadata`.
- Risiko: Duplicate fills bei Replays/Retry -> doppelte Position/Fee.

**Scope (minimal):**
- `src&#47;execution&#47;pipeline.py` (ExecutionPipeline)
- evtl. Tests unter `tests&#47;test_execution_pipeline_governance.py` oder neues `tests&#47;test_execution_pipeline_dedupe.py`

**Design (deterministic):**
- Ableitung eines `idempotency_key` pro Fill:
  - bevorzugt: `request.client_id + ":" + str(result.metadata["execution_id"])`
  - fallback: nur `execution_id` oder Hash aus (symbol,side,qty,price,timestamp)
- Pipeline fuehrt einen In-Memory Index:
  - `self._seen_fills: Dict[str, Dict[str, Any]]`
- Nach `executor.execute_orders(...)`:
  - pro filled result: berechne key
  - wenn key neu: speichern
  - wenn key existiert:
    - wenn payload identisch: **skip append** (idempotent)
    - wenn payload konflikt: raise `DuplicateFillConflictError`

**Acceptance:**
- Duplicate identical fills werden idempotent ignoriert (kein Double-Count)
- Conflicting duplicates raise deterministisch
- Tests decken beide Faelle ab
- NO-LIVE bleibt garantiert (nur paper/shadow/testnet)

**Evidence:**
- Minimaler Test Output Snapshot in Evidence (optional)

---

## Phase P6 — CI Triage (Snapshot-only)

**Rules:**
- Kein watch.
- Immer “root cause first” (ein Fix-Commit, kein PR-Spam).
- Token-Policy / Reference-Targets: targeted patch, keine mass edits.

---

## Phase P7 — Post-Merge Verify + PASS Evidence (Shadow MVS etc.)

**Ziel:** Deterministischer PASS Snapshot (bounded retries) als Evidence.

**Contract SSOT:**
- `docs&#47;webui&#47;observability&#47;SHADOW_MVS_CONTRACT.md`

**Verify Command:**
- `bash scripts&#47;obs&#47;shadow_mvs_local_verify.sh`

**Evidence Extract Lines:**
- `INFO|targets_retry=...`
- `EVIDENCE|exporter=...`
- `EVIDENCE|prometheus=...`
- `EVIDENCE|grafana=...`
- `EVIDENCE|dashboard_uid=...`
- `RESULT=PASS`

---

## Operator Decision Matrix (A0)

- **Docs-only** + gates clean → merge fast + merge-log PR.
- **Code-slice** (Phase 16A/B) → tests required + CI green before merge.
- **Forensics**: kein destructives cleanup ohne FSCK_OK Evidence.
