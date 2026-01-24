# Gates Overview

## Principles (Scope Lock, No-Live, Evidence, Determinism)

- **Scope lock**: Diese Datei ist die kanonische SSoT für „welche Gates existieren“ + „wo sind sie definiert“ + „wie reproduziere ich lokal deterministisch“.
- **No-live**: Gates sind **Qualitäts-/Policy-Prüfungen** (Docs/CI/Test/Ops). **Keine** Docker-Volumen-Resets, DB-Wipes oder Live/Testnet-Aktionen als „Fix“ ohne explizites Operator-GO.
- **Evidence-first**: Operator-Snapshots schreiben Outputs in ein eindeutiges Evidence-Verzeichnis (keine Watch-Loops).
- **Determinismus**: Wenn möglich: file-backed Inputs, stabile Base-Refs (`origin&#47;main`), keine Pipes in Snapshot-Blöcken.

> Token-Policy Hinweis: Inline illustrative Pfade im Fließtext **nicht** als `a&#47;b&#47;c` schreiben, sondern Slashes als `&#47;` encoden (z.B. `docs&#47;ops&#47;GATES_OVERVIEW.md`). Befehle in Code-Fences sind OK.

## Gate Catalog (Table)

**Legend**

- **Category**: Docs / CI / Test / Ops / Merge / Policy / Dep / Hygiene
- **Trigger**: PR = `pull_request`, MG = `merge_group`, Push = `push`, Schd = `schedule`, Man = `workflow_dispatch`
- **Expected PASS signal**: typischer „✅ …“ Output oder Check-Run „SUCCESS“

| Gate ID / Name | Category | Where defined (file paths) | Trigger (what changes) | How to run locally (command) | Expected PASS signal | Typical FAIL causes (with fix pointers) |
|---|---|---|---|---|---|---|
| **G-DOCS-TOKEN** `docs-token-policy-gate` | Docs | `.github/workflows/docs-token-policy-gate.yml`; `scripts/ops/validate_docs_token_policy.py`; Allowlist: `scripts/ops/docs_token_policy_allowlist.txt` | PR/MG/Man; workflow itself is “not applicable” if no `*.md` changed | `uv run python scripts/ops/validate_docs_token_policy.py --changed --base origin/main` | `✅` (keine Violations) / Exit 0 | **Inline-Code Token enthält `/` aber ist illustrativ** → Slashes encoden als `&#47;` im betroffenen `.md`; ggf. erlauben via Allowlist (nur für generische Tokens) in `scripts/ops/docs_token_policy_allowlist.txt` |
| **G-DOCS-REF-TARGETS** `docs-reference-targets-gate` | Docs | `.github/workflows/docs_reference_targets_gate.yml`; `scripts/ops/verify_docs_reference_targets.sh`; Ignore (full-scan only): `docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt` | PR/MG/Man; not applicable if keine `*.md` changed | `bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main` | `All referenced targets exist.` / Exit 0 | **Docs referenzieren nicht-existente Repo-Pfade** → Pfad korrigieren/umbenennen; falls **nur illustrativ** → encoden als `&#47;` im Inline-Code |
| **G-DOCS-DIFF-GUARD** `Docs Diff Guard Policy Gate` | Docs / Policy | `.github/workflows/docs_diff_guard_policy_gate.yml`; `scripts/ci/check_docs_diff_guard_section.py`; Inserter: `scripts/ops/insert_docs_diff_guard_section.py` | PR/MG/Man; **triggered** wenn Pfade unter `docs/ops/` bzw. `scripts/ops/docs_diff_guard.sh` o.Ä. geändert (siehe `TRIGGER_PREFIXES` im Script) | `python scripts/ci/check_docs_diff_guard_section.py` | `✅ Docs Diff Guard Policy: OK (marker present).` | **Marker fehlt** in required docs (`docs/ops/README.md`, `docs/ops/PR_MANAGEMENT_TOOLKIT.md`, `docs/ops/PR_MANAGEMENT_QUICKSTART.md`) → Insert: `python scripts/ops/insert_docs_diff_guard_section.py --files <comma-separated>` |
| **G-DOCS-SNAPSHOT** `pt_docs_gates_snapshot` (lokaler Wrapper) | Ops | `scripts/ops/pt_docs_gates_snapshot.sh` | Lokal (Operator) | `./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main` | `🎉 All gates passed!` | Wrapper bündelt die 3 Docs-Gates; Failure beheben wie oben in den Einzel-Gates beschrieben |
| **G-REQ-CHECKS-HYGIENE** `required-checks-hygiene-gate` | CI / Hygiene | `.github/workflows/required-checks-hygiene-gate.yml`; `scripts/ci/validate_required_checks_hygiene.py`; Config: `config/ci/required_status_checks.json` | PR/Push(main) | `python scripts/ci/validate_required_checks_hygiene.py --config config/ci/required_status_checks.json --workflows .github/workflows --strict` | `✅ SUCCESS: All N required checks are hygiene-compliant` | **Required check wird nur von path-filtered PR-workflows produziert** → Fix in Workflow YAML: **keine** `on.pull_request.paths` für required checks; statt dessen internal change detection (z.B. `dorny&#47;paths-filter`) |
| **G-CI-CONTEXTS-CONTRACT** `ci-required-contexts-contract` | CI / Hygiene | `.github/workflows/ci.yml` (Job); `scripts/ops/check_required_ci_contexts_present.sh` | PR/Push/MG/Schd/Man (CI workflow) | `bash scripts/ops/check_required_ci_contexts_present.sh` | `✅ CI required context contract looks good.` | **Missing required job names / job-level if** in `ci.yml` → Fix: `name:` für required jobs + **kein** job-level `if:` auf required contexts; Details/Regeln im Script |
| **G-CI-HEALTH-GATE** `CI Health Gate (weekly_core)` | Test / CI | `.github&#47;workflows&#47;test_health.yml`; `scripts&#47;run_test_health_profile.py` | PR/Push (main); (Workflow hat auch Schd/Man, aber dieser Gate-Job läuft nur auf PR/Push) | `python scripts&#47;run_test_health_profile.py --profile weekly_core` | Check-Run SUCCESS / Exit 0 | **Health Profile failures** → Fix: behebe die fehlgeschlagenen Checks aus dem Report; Artefakte/Reports unter `reports&#47;test_health&#47;` (siehe CI Logs) |
| **G-TESTS-MATRIX** `tests (3.9, 3.10, 3.11)` | Test | `.github/workflows/ci.yml` | PR/Push/MG/Schd/Man; intern skip auf docs-only via step-level `if` | Lokal (minimal): `python -m pytest tests/ -v --tb=short` | `=== ... passed ...` / Exit 0 | Test-Failures → Fix in `src&#47;**`/`tests&#47;**`; beachte: CI führt zusätzlich Smoke/Contract Steps aus (`tests/test_stability_smoke.py`, RL checks) |
| **G-STRATEGY-SMOKE** `strategy-smoke` | Test | `.github/workflows/ci.yml`; `scripts/strategy_smoke_check.py`; `tests/test_strategy_smoke_cli.py` | PR/Push/MG/Schd/Man; intern skip auf docs-only via step-level `if` | `python -m pytest tests/test_strategy_smoke_cli.py -v --tb=short` und/oder `python scripts/strategy_smoke_check.py --output-json <file> --output-md <file>` | Pytest pass / erzeugte Output-Files | Strategie-Registry / CLI Regression → Fix in `scripts/strategy_smoke_check.py`, `src&#47;**`, `tests&#47;**` |
| **G-LINT-GATE** `Lint Gate` | CI / Lint | `.github/workflows/lint_gate.yml`; Formatter-Policy Guard: `scripts/ops/check_no_black_enforcement.sh` | PR(types)/MG; intern “not applicable” wenn keine `.py` changed | `python -m pip install ruff` dann `python -m ruff check src/ tests/ scripts/` und `python -m ruff format --check src/ tests/ scripts/` | `✅ Ruff check passed` + `✅ Code formatting check passed` | **Ruff Lint/Format Fail** → Fix code; **black enforcement drift** → Fix in `.github&#47;workflows&#47;**` oder `scripts&#47;**` (siehe `scripts/ops/check_no_black_enforcement.sh`) |
| **G-DISPATCH-GUARD** `dispatch-guard` | CI / Hygiene | `.github/workflows/ci-workflow-dispatch-guard.yml`; `scripts/ops/validate_workflow_dispatch_guards.py`; Tests: `tests/ops/test_validate_workflow_dispatch_guards.py` | PR always; Push(main) nur bei Workflow-Änderungen (paths) | `python scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --fail-on-warn` | `✅` / Exit 0 | **github.event.inputs.* referenziert, aber nicht deklariert** → Fix direkt im betroffenen Workflow YAML unter `on.workflow_dispatch.inputs` |
| **G-POLICY-CRITIC** `Policy Critic Gate` | Policy | `.github/workflows/policy_critic_gate.yml`; `scripts/run_policy_critic.py` | PR(types)/MG; intern “not applicable” wenn keine policy-sensitiven Pfade geändert | Lokal: `python scripts/run_policy_critic.py --pr-mode` | `✅ Policy Critic analysis passed` | Policy-Check-Fail → Fix in policy-sensitiven Pfaden (siehe `POLICY_PATHS` im Workflow), ggf. `scripts&#47;run_policy_critic.py` |
| **G-REPORTS-NO-TRACKED** `Guard tracked files in reports directories` | Policy / Hygiene | `.github/workflows/policy_tracked_reports_guard.yml`; `scripts/ci/guard_no_tracked_reports.sh` | PR/Push/MG (always) | `bash scripts/ci/guard_no_tracked_reports.sh` | `✅ PASS: No tracked files found ...` | **Tracked files in `reports&#47;` oder `docs&#47;reports&#47;`** → Fix: `git rm --cached <file>` und Artefakte unter `docs/` ablegen (siehe Script Output) |
| **G-REPORTS-IGNORED** `guard-reports-ignored` | Policy / Hygiene | `.github/workflows/guard-reports-ignored.yml` | PR/Push/MG (paths: `.gitignore`, `reports&#47;**`) | Lokal: `git ls-files reports` muss leer sein; `.gitignore` muss `/reports/` enthalten | Check output: Tracked files under reports/: 0 | **`.gitignore` fehlt `/reports/`** oder `reports/` tracked → Fix in `.gitignore` + `git rm --cached` |
| **G-DEPS-SYNC** `guard` (Workflow: `deps-sync-guard`) | Dep / Hygiene | `.github&#47;workflows&#47;deps_sync_guard.yml`; `scripts&#47;ops&#47;check_requirements_synced_with_uv.sh`; `uv.lock`, `requirements.txt`, `pyproject.toml` | PR (paths-filtered), MG, Man | `bash scripts&#47;ops&#47;check_requirements_synced_with_uv.sh` | `✅ requirements.txt matches uv.lock export.` | **requirements.txt drift vs uv.lock** → Fix: regenerate via `uv export ...` (Script zeigt Normalisierung + diff) |
| **G-MERGE-LOGS-SANITY** `merge-logs-sanity` | Merge / Hygiene | `.github/workflows/merge-logs-sanity.yml`; `scripts/ops/check_merge_log_hygiene.py` | PR types; conditional auf Änderungen unter `docs/ops/merge_logs/` | Lokal: `python scripts/ops/check_merge_log_hygiene.py docs/ops/merge_logs/PR_<N>_MERGE_LOG.md` | `✅` / Exit 0 | **Verbotene lokale Pfade** (`/Users/`, `/home/`, `C:\`, `~/`) oder **Unicode-Hygiene** → Fix direkt im betroffenen Merge-Log Markdown |
| **G-MERGE-LOG-HYGIENE (info)** `Check Merge Logs Hygiene` | Merge / Hygiene | `.github/workflows/merge_log_hygiene.yml`; `scripts/ops/check_merge_log_hygiene.py` | PR (paths-filtered, informational), Man | Lokal wie oben | Workflow läuft informational; lokal Exit 0 wenn sauber | Gleiches Fix wie bei `G-MERGE-LOGS-SANITY`; wichtig: Workflow ist **informational** (siehe YAML Kommentar) |
| **G-AUDIT** `audit` | CI / Security | `.github/workflows/audit.yml` | PR/Push/MG/Schd/Man | Lokal: (CI-only) – siehe Workflow | Check-Run SUCCESS | Audit findings → Fix abhängig von Tooling im Workflow (`audit.yml`) |
| **G-EVIDENCE-PACK** `evidence-pack-validation-gate` | CI / Validation | `.github/workflows/evidence_pack_gate.yml`; Scripts: `scripts/validate_evidence_pack_ci.py`, `scripts/run_layer_smoke_with_evidence_pack.py` | PR/Push/MG/Man; internal “skip” wenn keine evidence-pack Änderungen | Lokal (smoke): `python scripts/run_layer_smoke_with_evidence_pack.py --layer L0 --autonomy REC --verbose` | Script exit 0; Artefakte unter `.artifacts&#47;evidence_packs&#47;` | Evidence pack schema/validation fail → Fix in `scripts/validate_evidence_pack_ci.py` / `src&#47;ai_orchestration&#47;**` / tests |

> Hinweis: Weitere Workflows existieren unter `.github/workflows/` (Scheduled/Automation, Reports, AIOps, VaR, Replay, Quarto). Siehe CI-Map unten für vollständige Inventarisierung.

## CI Workflows Map

### Always-run vs Path-filtered (PR)

- **Always-run PR workflows** (keine `on.pull_request.paths`): erzeugen immer Check-Runs → wichtig für Branch-Protection und „required contexts“. Beispiele:
  - `.github/workflows/ci.yml` (Workflow: `CI`)
  - `.github/workflows/required-checks-hygiene-gate.yml`
  - `.github/workflows/lint_gate.yml`
  - `.github/workflows/policy_critic_gate.yml`
  - `.github/workflows/docs-token-policy-gate.yml` (läuft PR immer, macht intern „not applicable“ ohne `*.md`)
  - `.github/workflows/docs_reference_targets_gate.yml` (läuft PR immer, macht intern „not applicable“ ohne `*.md`)
  - `.github/workflows/docs_diff_guard_policy_gate.yml`
  - `.github/workflows/policy_tracked_reports_guard.yml`

- **Path-filtered PR workflows** (`on.pull_request.paths` gesetzt): werden nur gestartet, wenn Pfade matchen; **dürfen nicht** die einzige Quelle für required checks sein (siehe `G-REQ-CHECKS-HYGIENE`).
  - `.github/workflows/merge_log_hygiene.yml` (informational)
  - `.github/workflows/deps_sync_guard.yml`
  - `.github/workflows/guard-reports-ignored.yml`

### Workflow → Jobs (Check-Namen) → Definition

Die wichtigsten PR-relevanten Checks (inkl. required contexts config) sind in `config/ci/required_status_checks.json` definiert; die Workflows, die diese Checks erzeugen, sind in den YAMLs implementiert.

- **Workflow `CI`** (`.github/workflows/ci.yml`)
  - Job/Check: `ci-required-contexts-contract` (runs always)
  - Job/Check: `tests (3.9)`, `tests (3.10)`, `tests (3.11)` (runs always; step-level skip auf docs-only)
  - Job/Check: `strategy-smoke` (runs always; step-level skip auf docs-only)

- **Workflow `Required Checks Hygiene Gate`** (`.github/workflows/required-checks-hygiene-gate.yml`)
  - Job/Check: `required-checks-hygiene-gate`

- **Workflow `Lint Gate (Always Run)`** (`.github/workflows/lint_gate.yml`)
  - Job/Check: `Lint Gate`

- **Workflow `Policy Critic Gate (Always Run)`** (`.github/workflows/policy_critic_gate.yml`)
  - Job/Check: `Policy Critic Gate`

- **Workflow `Docs Token Policy Gate`** (`.github/workflows/docs-token-policy-gate.yml`)
  - Job/Check: `docs-token-policy-gate`

- **Workflow `Docs Reference Targets Gate`** (`.github/workflows/docs_reference_targets_gate.yml`)
  - Job/Check: `docs-reference-targets-gate`

- **Workflow `Docs Diff Guard Policy Gate`** (`.github/workflows/docs_diff_guard_policy_gate.yml`)
  - Job/Check: `Docs Diff Guard Policy Gate`

- **Workflow „CI / Workflow Dispatch Guard“** (`.github/workflows/ci-workflow-dispatch-guard.yml`)
  - Job/Check: `dispatch-guard`

- **Workflow `Policy Guard - No Tracked Reports`** (`.github/workflows/policy_tracked_reports_guard.yml`)
  - Job/Check: `Guard tracked files in reports directories`

- **Workflow `Merge Logs Sanity`** (`.github/workflows/merge-logs-sanity.yml`)
  - Job/Check: `merge-logs-sanity` (conditional auf `docs/ops/merge_logs/`)

## Optional/Scheduled/Informational Gates (Appendix)

Diese Checks werden von Workflows erzeugt, sind aber **nicht** Teil der Branch-Protection-required contexts. Die vollständige, maschinenlesbare Inventarisierung (Workflows + Trigger + produced checks + Diffs) wird als Evidence in `.local_tmp&#47;gates_audit_<STAMP>&#47;` erzeugt (siehe `REPORT.md` dort).

### Canonical Gates Completeness Audit (Verification procedure)

**Kanonische Verifikation** ist „evidence-first“ und basiert auf 3 Artefakt-Sets:

- **Branch protection required contexts** (best-effort via `gh api`)
- **Repo contract required contexts** aus `config&#47;ci&#47;required_status_checks.json`
- **Workflow-produced checks** aus `.github&#47;workflows&#47;*` (inkl. Schedule/Dispatch-only), plus Klassifizierung (always-pr vs path-filtered vs schedule-only etc.)

Der Audit wird als Evidence unter `.local_tmp&#47;gates_audit_<STAMP>&#47;` abgelegt; dort sind insbesondere `required_contexts_effective.txt`, `workflows_index.json`, `produced_checks_all.txt` und `REPORT.md` die SSoT für den Snapshot. (Siehe auch Appendix-Listen unten für eine kuratierte, menschenlesbare Klassifizierung.)

### Always-run PR (non-required, informational)

- `PR Merge State Signal` — `.github&#47;workflows&#47;ci-pr-merge-state-signal.yml`
- `evidence-pack-smoke-run` — `.github&#47;workflows&#47;evidence_pack_gate.yml`
- `L4 Critic Replay Determinism` / `L4 Critic Determinism Tests` — `.github&#47;workflows&#47;l4_critic_replay_determinism.yml`

### PR path-filtered (informational / scoped)

- `lint` — `.github&#47;workflows&#47;lint.yml`
- `Generate Docs Integrity Snapshot` — `.github&#47;workflows&#47;docs-integrity-snapshot.yml`
- `Check Docs Link Debt Trend` — `.github&#47;workflows&#47;docs_reference_targets_trend.yml`
- `Recon Audit Gate Smoke` — `.github&#47;workflows&#47;ci_recon_audit_gate_smoke.yml`
- `Render Quarto Smoke Report` — `.github&#47;workflows&#47;quarto_smoke.yml`
- `replay-compare-report` — `.github&#47;workflows&#47;replay_compare_report.yml`
- `VaR Report Tools (Compare + Index)` / `VaR CLI Smoke Tests` / `VaR Report Gate Summary` — `.github&#47;workflows&#47;var_report_regression_gate.yml`
- `Detect Changes` / `Run Promptfoo Evals` / `Skip Evals (No Relevant Changes)` — `.github&#47;workflows&#47;aiops-promptfoo-evals.yml`
- `Format-Only Verifier` / `Policy Critic Review` — `.github&#47;workflows&#47;policy_critic.yml`

### Schedule/Dispatch/Workflow-run (automation)

- `Full Audit (Security + Quality)` — `.github&#47;workflows&#47;full_audit_weekly.yml`
- `InfoStream Cycle` — `.github&#47;workflows&#47;infostream-automation.yml`
- `Test Knowledge DB with ChromaDB` — `.github&#47;workflows&#47;knowledge_extras_chromadb.yml`
- `market_outlook_daily` — `.github&#47;workflows&#47;market_outlook_automation.yml`
- `Daily Test Suite` / `Weekly Test Suite` / `Notify on Failure` — `.github&#47;workflows&#47;offline_suites.yml`
- `dashboard` — `.github&#47;workflows&#47;ops_doctor_dashboard.yml`
- `build` / `deploy` — `.github&#47;workflows&#47;ops_doctor_pages.yml`
- `Generate Trend Seed` — `.github&#47;workflows&#47;aiops-trend-seed-from-normalized-report.yml` (workflow_run)
- `Generate Trend Ledger` — `.github&#47;workflows&#47;aiops-trend-ledger-from-seed.yml` (dispatch)
- `Health Check: ...` / `Nightly Health Suite` / `R&D Experimental Check` — `.github&#47;workflows&#47;test-health-automation.yml`

## Merge Guard Gate (Operator-controlled)

### Required conditions (Stop Rules)

Ein Merge ist nur zulässig, wenn **alle** Bedingungen erfüllt sind:

- **PR state** ist `OPEN`
- **mergeable** ist `MERGEABLE`
- **mergeStateStatus** ist `CLEAN`
- **required checks**: keine Non-OK check-runs auf dem PR head commit
- **Approval gate**: Kommentar existiert, dessen Body **exakt** `APPROVED` ist (oder alternative Policy in Runbook)
- **Guarded merge**: `--match-head-commit <head_sha>` wird verwendet (Race-Condition Schutz)

### Canonical guarded-merge snippet (snapshot-only)

```bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

PR="${PR:?Setze PR (z.B. export PR=123)}"

echo "== Repo snapshot =="
pwd
git status -sb

echo "== Repo owner/name =="
REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "repo=$REPO"

echo "== PR snapshot =="
STATE="$(gh pr view "$PR" --json state -q .state || true)"
MERGEABLE="$(gh pr view "$PR" --json mergeable -q .mergeable || true)"
STATESTATUS="$(gh pr view "$PR" --json mergeStateStatus -q .mergeStateStatus || true)"
HEAD_EXPECTED="$(gh pr view "$PR" --json headRefOid -q .headRefOid || true)"
echo "state=$STATE mergeable=$MERGEABLE mergeStateStatus=$STATESTATUS head_expected=$HEAD_EXPECTED"

if [[ "$STATE" != "OPEN" ]]; then echo "STOP: state != OPEN"; exit 0; fi
if [[ "$MERGEABLE" != "MERGEABLE" ]]; then echo "STOP: mergeable != MERGEABLE"; exit 0; fi
if [[ "$STATESTATUS" != "CLEAN" ]]; then echo "STOP: mergeStateStatus != CLEAN"; exit 0; fi
if [[ -z "${HEAD_EXPECTED:-}" ]]; then echo "STOP: head_expected empty"; exit 0; fi

echo "== Required checks: check-runs on head commit (robust) =="
NONOK_JSON_PATH=".local_tmp/pr_${PR}_nonok_checkruns.json"
mkdir -p .local_tmp
gh api -H "Accept: application/vnd.github+json" "repos/${REPO}/commits/${HEAD_EXPECTED}/check-runs" \
  --jq '[.check_runs[] | select((.conclusion != "success") and (.conclusion != "skipped") and (.conclusion != "neutral")) | {name: .name, status: .status, conclusion: .conclusion, url: .html_url}]' \
  > "$NONOK_JSON_PATH"

NONOK_COUNT="$(python3 - <<'PY' "$NONOK_JSON_PATH"
import json,sys
arr=json.load(open(sys.argv[1],"r",encoding="utf-8"))
print(len(arr))
PY
)"
echo "nonok_checks=$NONOK_COUNT (file=$NONOK_JSON_PATH)"
if [[ "$NONOK_COUNT" != "0" ]]; then
  echo "STOP: non-ok required checks != 0"
  python3 - <<'PY' "$NONOK_JSON_PATH"
import json,sys
arr=json.load(open(sys.argv[1],"r",encoding="utf-8"))
for x in arr[:50]:
    print(f"- {x.get('name')} status={x.get('status')} conclusion={x.get('conclusion')} {x.get('url')}")
PY
  exit 0
fi

echo "== Approval gate (exact comment body: APPROVED) =="
APPROVAL_ID_PATH=".local_tmp/pr_${PR}_approval_id.txt"
gh api "repos/${REPO}/issues/${PR}/comments" --paginate --jq '.[] | select(.body=="APPROVED") | .id' > "$APPROVAL_ID_PATH" || true
APPROVAL_ID="$(python3 - <<'PY' "$APPROVAL_ID_PATH"
import sys
s=open(sys.argv[1],"r",encoding="utf-8").read().strip()
print(s.splitlines()[0] if s.splitlines() else "")
PY
)"
echo "approval_exact_comment_id=${APPROVAL_ID:-NOT_FOUND} (file=$APPROVAL_ID_PATH)"
if [[ -z "${APPROVAL_ID:-}" ]]; then
  echo "STOP: APPROVED comment not found"
  echo "Optional (if YOU intend to approve now): gh pr comment $PR --body \"APPROVED\""
  exit 0
fi

echo "GATE: YES -> merging PR #$PR (guarded --match-head-commit=$HEAD_EXPECTED)"
gh pr merge "$PR" --squash --delete-branch --match-head-commit "$HEAD_EXPECTED"
```

### Known footguns

- **zsh reserved vars**: In zsh ist `UID` ein read-only special parameter. Verwende in Scripts Variablen wie `DASH_UID` statt `UID`.
- **Missing check-run JSON**: Nutze die `check-runs` API (Snippet oben) statt fragile `gh pr checks --json` Ausgaben.
- **Paths-filtered required checks**: `required-checks-hygiene-gate` verhindert, dass Branch-Protection auf „missing checks“ läuft.

## Change Impact Matrix

„Wenn du X änderst, erwarte Y“ (PR-Gates).

| Change touched | Expect these gates (minimum) | Why / Notes |
|---|---|---|
| `docs&#47;**` | `docs-token-policy-gate`, `docs-reference-targets-gate`, `Docs Diff Guard Policy Gate` (wenn `docs&#47;ops&#47;` betroffen), ggf. `docs-integrity-snapshot` | Markdown policies + ref validation; Diff-Guard marker requirement bei ops-doc changes |
| `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;**` | `docs-token-policy-gate` + `docs-reference-targets-gate` nur wenn `*.md` betroffen; sonst typischerweise keine Python-Lint/Test gates | JSON dashboards sind docs-only; Markdown-Gates nur bei Markdown-Änderungen |
| `docs&#47;ops&#47;merge_logs&#47;**` | `merge-logs-sanity` (conditional), plus ggf. `docs` gates wenn Markdown-Refs im Merge-Log existieren | Merge-Log Hygiene + Unicode/Local-path guard |
| `.github&#47;workflows&#47;**` | `dispatch-guard`, `required-checks-hygiene-gate`, plus je nach Workflow: `CI`/`Lint Gate`/`Policy Critic Gate` | Workflow dispatch inputs + required contexts reliability |
| `src&#47;**` oder `tests&#47;**` | `CI` (tests matrix + strategy-smoke), `Lint Gate`, ggf. `Policy Critic Gate`, ggf. `Evidence Pack` | Code changes trigger test/lint/policy validators |
| `scripts&#47;**` | `CI` (code_changed), `Lint Gate` (wenn `.py`), ggf. `Policy Critic Gate`, ggf. spezifische gates (evidence/deps/etc.) | Scripts zählen zu „code_changed“ in CI |
| `requirements.txt` / `uv.lock` / `pyproject.toml` | `deps-sync-guard`, häufig auch `CI` | Dependency sync and install health |
| `reports&#47;**` oder `.gitignore` | `guard-reports-ignored` (paths-filtered) und `Guard tracked files in reports directories` (always) | No tracked reports policy |

## Operator Snapshot (Copy/Paste)

Ein einzelner Snapshot-Block (kein Pipe, file-backed). Er läuft sicher (kein merge), sammelt Evidence in `.local_tmp&#47;`.

```bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT=".local_tmp/gates_snapshot_${STAMP}"
mkdir -p "$OUT"

echo "== 0) Repo preflight ==" > "$OUT/00_preflight.txt"
pwd >> "$OUT/00_preflight.txt"
git rev-parse --show-toplevel >> "$OUT/00_preflight.txt" 2>&1 || true
git status -sb >> "$OUT/00_preflight.txt" 2>&1 || true

echo "== 1) Ensure base ref present ==" > "$OUT/01_base_ref.txt"
git fetch -p origin >> "$OUT/01_base_ref.txt" 2>&1 || true

echo "== 2) Changed files vs origin/main ==" > "$OUT/02_changed_files.txt"
git diff --name-only origin/main...HEAD >> "$OUT/02_changed_files.txt" 2>&1 || true

python3 - "$OUT/02_changed_files.txt" "$OUT/03_scope_flags.json" "$OUT/03_flags.env" <<'PY'
import json,sys
changed_path=sys.argv[1]
out_path=sys.argv[2]
env_path=sys.argv[3]
raw=open(changed_path,"r",encoding="utf-8",errors="replace").read().splitlines()
files=[x.strip() for x in raw if x.strip() and not x.strip().startswith("==")]
def any_prefix(pfx): return any(f.startswith(pfx) for f in files)
def any_suffix(sfx): return any(f.endswith(sfx) for f in files)
flags={
  "has_markdown_changes": any_suffix(".md"),
  "has_docs_ops_changes": any_prefix("docs/ops/"),
  "has_merge_logs_changes": any_prefix("docs/ops/merge_logs/"),
  "has_python_changes": any_suffix(".py"),
  "has_workflow_changes": any_prefix(".github/workflows/"),
  "has_deps_changes": any(f in files for f in ["requirements.txt","uv.lock","pyproject.toml"]),
  "has_reports_or_gitignore_changes": any_prefix("reports/") or any_prefix("docs/reports/") or any(f==".gitignore" for f in files),
}
json.dump({"changed_files": files, "flags": flags}, open(out_path,"w",encoding="utf-8"), indent=2)
print("Wrote", out_path)

def b(x): return "1" if x else "0"
env_lines = [
  f"HAS_MARKDOWN_CHANGES={b(flags['has_markdown_changes'])}",
  f"HAS_MERGE_LOGS_CHANGES={b(flags['has_merge_logs_changes'])}",
  f"HAS_PYTHON_CHANGES={b(flags['has_python_changes'])}",
  f"HAS_WORKFLOW_CHANGES={b(flags['has_workflow_changes'])}",
  f"HAS_DEPS_CHANGES={b(flags['has_deps_changes'])}",
  f"HAS_REPORTS_OR_GITIGNORE_CHANGES={b(flags['has_reports_or_gitignore_changes'])}",
]
open(env_path,"w",encoding="utf-8").write("\n".join(env_lines) + "\n")
print("Wrote", env_path)
PY

echo "== 3) Docs gates snapshot (only if markdown changed) ==" > "$OUT/10_docs_gates_snapshot.log"
set -a
source "$OUT/03_flags.env"
set +a
echo "HAS_MARKDOWN_CHANGES=$HAS_MARKDOWN_CHANGES" >> "$OUT/10_docs_gates_snapshot.log"
if [[ "${HAS_MARKDOWN_CHANGES}" == "1" ]]; then
  ./scripts/ops/pt_docs_gates_snapshot.sh --changed --base origin/main >> "$OUT/10_docs_gates_snapshot.log" 2>&1 || true
else
  echo "Docs gates: not applicable (no markdown changes)." >> "$OUT/10_docs_gates_snapshot.log"
fi

echo "== 4) Merge-log hygiene (only if merge_logs changed) ==" > "$OUT/20_merge_log_hygiene.log"
echo "HAS_MERGE_LOGS_CHANGES=$HAS_MERGE_LOGS_CHANGES" >> "$OUT/20_merge_log_hygiene.log"
if [[ "${HAS_MERGE_LOGS_CHANGES}" == "1" ]]; then
  # file-backed list (no pipes)
  python3 - "$OUT/02_changed_files.txt" "$OUT/21_merge_log_files.txt" <<'PY'
import sys
src=sys.argv[1]
dst=sys.argv[2]
lines=[l.strip() for l in open(src,"r",encoding="utf-8").read().splitlines() if l.strip()]
ml=[l for l in lines if l.startswith("docs/ops/merge_logs/") and l.endswith(".md")]
open(dst,"w",encoding="utf-8").write("\n".join(ml)+("\n" if ml else ""))
print("merge_log_files =", len(ml))
PY
  python3 - "$OUT/21_merge_log_files.txt" <<'PY'
import sys
files=[l.strip() for l in open(sys.argv[1],"r",encoding="utf-8").read().splitlines() if l.strip()]
if not files:
    print("No merge-log markdown files changed.")
else:
    for f in files:
        print("Checking", f)
        # run per-file to keep output localized
        import subprocess
        raisecode=subprocess.call(["python3","scripts/ops/check_merge_log_hygiene.py",f])
        if raisecode!=0:
            raise SystemExit(1)
PY
else
  echo "Merge-log hygiene: not applicable (no merge_logs changes)." >> "$OUT/20_merge_log_hygiene.log"
fi

echo "== 5) Required checks hygiene (always safe) ==" > "$OUT/30_required_checks_hygiene.log"
python3 scripts/ci/validate_required_checks_hygiene.py \
  --config config/ci/required_status_checks.json \
  --workflows .github/workflows \
  --strict >> "$OUT/30_required_checks_hygiene.log" 2>&1 || true

echo "== DONE =="
echo "Evidence dir: $OUT"
```

## Troubleshooting Index

### Token policy violations (inline paths)

- **Symptom**: `docs-token-policy-gate` FAIL, Violations zeigen Inline-Code Tokens mit `/`.
- **Fix**: betroffene Markdown-Datei editieren: illustrative Pfade encoden (z.B. `docs&#47;ops&#47;GATES_OVERVIEW.md`). Quelle/Regeln: `scripts/ops/validate_docs_token_policy.py`. Allowlist: `scripts/ops/docs_token_policy_allowlist.txt`.

### Reference targets failures

- **Symptom**: `docs-reference-targets-gate` FAIL, “missing targets”.
- **Fix**: Pfade in Markdown korrigieren; wenn Pfad nur illustrativ, encode als `&#47;`. Full-scan ignore patterns: `docs/ops/DOCS_REFERENCE_TARGETS_IGNORE.txt` (CI `--changed` ist absichtlich strikt).

### Diff guard marker issues

- **Symptom**: `Docs Diff Guard Policy Gate` FAIL: Marker fehlt.
- **Fix location(s)**: Required docs laut `scripts/ci/check_docs_diff_guard_section.py` (`REQUIRED_DOCS`).
- **Fix command**: `python scripts/ops/insert_docs_diff_guard_section.py --files <comma-separated>`.

### Merge-log hygiene failures

- **Symptom**: `merge-logs-sanity` bzw. lokaler `check_merge_log_hygiene.py` FAIL.
- **Fix**: Entferne lokale Pfade (`/Users/`, `/home/`, `C:\`, `~/`) und problematische Unicode-Zeichen. Quelle: `scripts/ops/check_merge_log_hygiene.py`.

### Nonok_checks parsing issues (robust patterns)

- **Symptom**: CI/Operator Scripts melden “UNKNOWN” oder JSON parse errors.
- **Fix**: Verwende file-backed JSON und die `check-runs` API wie im Merge-Guard Snippet (siehe Abschnitt „Merge Guard Gate“). Keine fragile Parsing-Pipes.
