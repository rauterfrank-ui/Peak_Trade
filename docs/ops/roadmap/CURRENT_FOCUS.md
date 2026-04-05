---
title: "Current focus — operator-maintained (not auto-generated)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-04-11
---

# Current focus

**Purpose:** One short, **human-updated** place so chats and operators know **what we are doing now**.  
This is **not** produced by Workflow Officer or Update Officer; officers aggregate checks and summaries — they do not replace this note.

**Related:** [Finish Plan (MVP→v1.0)](FINISH_PLAN.md) · [Truth Core](../registry/TRUTH_CORE.md) · [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) · [Release docs (index)](../release/README.md) · [Chat continuity bootstrap](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md)

---

## Active goal (one sentence)

**Finish Plan PRs 6–8** bilden die **abgeschlossene** Navigations-Spine auf `main` (docs-only / snapshot-only): [PR 6 — Live-Ops runbook pack](FINISH_PLAN.md#pr-6-live-ops-runbook-pack-docs-only) · [PR 7 — Observability / status reports](FINISH_PLAN.md#pr-7-observabilitystatus-report-hardening-code-docs) · [PR 8 — Release checklist / Go–No-Go](FINISH_PLAN.md#pr-8-release-checklist-gono-go-rubric-docs-only) — Einstieg weiter über [Workflow Frontdoor](../../WORKFLOW_FRONTDOOR.md) und [Release docs](../release/README.md); **NO** live unlocks. **Aktueller Fokus:** schmale Slices aus [FINISH_PLAN — Workstreams](FINISH_PLAN.md#workstreams-16--inputs--outputs--contracts--tests) und den Runbooks (z. B. [Stufe J](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#stufe-j--scripts--demo-daten-operativ-niedrig-priorisiert), [Chat-led gaps](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md)) — kein weiterer nummerierter PR 9+ im Finish-Plan. **Truth/docs governance, PR truth gates, officer truth integration, bounded-pilot / canary-live-entry docs, J1 forward-pipeline slices, the J2 Optuna demo-runner slice, and the J3 placeholder-inventory tooling smoke are landed** — see **Recently landed** below.

---

## Recently landed (truth, docs governance, officers)

- **Unified Truth Core** (`src/ops/truth/`): shared loaders + deterministic evaluators for docs drift and repo truth claims — [TRUTH_CORE.md](../registry/TRUTH_CORE.md).
- **CI:** workflow [.github/workflows/truth_gates_pr.yml](../../../.github/workflows/truth_gates_pr.yml) defines jobs **`docs-drift-guard`** and **`repo-truth-claims`** (PR / merge queue / manual dispatch).
- **Officers:** [Workflow Officer](#how-workflow-officer-and-update-officer-fit) and [Update Officer](#how-workflow-officer-and-update-officer-fit) include **`summary.unified_truth_status`** (read-only diagnostics from the same core).
- **Forward / ops context:** J1 forward-pipeline slices and bounded-pilot / canary-live-entry runbooks merged per prior PRs; posture unchanged (**NO-LIVE** default unless a governed runbook explicitly says otherwise).
- **J1 (shared OHLCV loader edge cases, PR #2172):** `scripts/_shared_ohlcv_loader.py` — u. a. `n_bars >= 1` (Dummy), normalisiertes `ohlcv_source`, Tests in `tests/test_dummy_ohlcv.py`; kein neuer Datenquellen-Scope; **NO-LIVE**.
- **J1 (Kraken shortfall observability, PR #2173):** bei weniger Bars als angefordert — `UserWarning`, Meta `kraken_bars_shortfall`, Observability in `generate_forward_signals` / `evaluate_forward_signals`; Runbook-Hinweis in [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md); **NO-LIVE**.
- **J2 (Optuna placeholder slice, PR #2168):** `scripts/run_study_optuna_placeholder.py` — CLI, dry-run default, optional in-memory toy study (`--no-dry-run`); no market/live execution. Full strategy optimization remains `scripts/run_optuna_study.py` (incl. GridSampler / CI alignment with Optuna 3.6).
- **J3 (placeholder inventory tooling, PR #2170):** `scripts/ops/placeholders/generate_placeholder_reports.py` — local inventory Markdown under `.ops_local` (gitignored); smoke `tests/ops/test_generate_placeholder_reports_smoke.py`; no new CI gate; **NO-LIVE**.
- **Finish Plan PR 7 (operator verify, PR #2177):** kanonischer Ablauf in [LIVE_STATUS_REPORTS.md](../../LIVE_STATUS_REPORTS.md#7-operator-verify-finish-plan-pr-7) · `FINISH_PLAN` PR 7; Docs-only; **NO-LIVE**.
- **Finish Plan PR 8 (release / Go–No-Go, PR #2178):** Rubric §4 + `CURRENT_FOCUS`/`FINISH_PLAN`-Anker; [Release checklist & Go/No-Go rubric](../release/runbooks/RELEASE_CHECKLIST_AND_GO_NO_GO_RUBRIC.md); Docs-only; **NO-LIVE**.
- **Chat-led gap sync (PR #2182):** Querverweis [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) → [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) (Stufe J); Docs-only; **NO-LIVE**.
- **Chat-led mini-slice — backtest evidence symbol (PR #2184):** `scripts/run_backtest.py` — `resolve_backtest_symbol()` für Evidence-Chain-Metadaten (Config-first); Runbook-Stichprobe §5 in [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md); **NO-LIVE**.
- **Chat-led Stichprobe §5 — Scripts (PR #2193):** `run_backtest.py` / Evidence-Metadaten `symbol` (`resolve_backtest_symbol`); [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md); **NO-LIVE**.
- **Chat-led Stichprobe §5 — Research-Stubs (PR #2194):** Bouchaud / Gatheral-Cont + zugehöriger Test-Stub; [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md); **NO-LIVE**.
- **J1 (Forward/Portfolio CLI NO-LIVE help, PR #2198):** `scripts/_shared_forward_args.py` — gemeinsamer Epilog/Scope für `generate_forward_signals` / `evaluate_forward_signals` / `run_portfolio_backtest_v2` (`--help`); Smoke `tests/test_shared_forward_args_cli.py`; **NO-LIVE**.
- **J3 (placeholder inventory CLI NO-LIVE help, PR #2200):** `scripts/ops/placeholders/generate_placeholder_reports.py` — `--help`/Epilog (lokales Triage-Tool, keine Orders); erweiterter Smoke in `tests/ops/test_generate_placeholder_reports_smoke.py`; **NO-LIVE**.
- **J2 (Optuna placeholder CLI NO-LIVE help, PR #2202):** `scripts/run_study_optuna_placeholder.py` — `--help`/Epilog (Toy/In-Memory, keine Order-Ausführung; vollständige Optimierung: `run_optuna_study.py`); Smoke in `tests/scripts/test_run_study_optuna_placeholder.py`; **NO-LIVE**.
- **Optuna full study CLI (NO-LIVE help vs. J2 placeholder, PR #2204):** `scripts/run_optuna_study.py` — `--help`/Epilog (Backtest-basierte Strategy-Optimierung; Abgrenzung zu `run_study_optuna_placeholder.py`); Smoke `tests/scripts/test_run_optuna_study_help_smoke.py`; **NO-LIVE**.
- **Unified sweep pipeline CLI (NO-LIVE help, PR #2206):** `scripts/run_sweep_pipeline.py` — `--help`/Docstring (Research-/Backtest-Sweep, keine Live-Orders); Smoke `tests/scripts/test_run_sweep_pipeline_smoke.py`; **NO-LIVE**.
- **Truth (repo claim `TRUTH_BRANCH_PROTECTION`, PR #2256):** `config/ops/repo_truth_claims.yaml` — Claim `truth-branch-protection-registry-present`; Registry [REPO_TRUTH_CLAIMS.md](../registry/REPO_TRUTH_CLAIMS.md) listet Claims; **NO-LIVE**.
- **Truth (docs drift `truth-branch-protection-canonical`, PR #2257):** `config/ops/docs_truth_map.yaml` — Änderungen an `docs/ops/registry/TRUTH_BRANCH_PROTECTION.md` erfordern Mitänderung an `docs/ops/registry/DOCS_TRUTH_MAP.md` im selben Diff; Kurzreferenz in [TRUTH_CORE.md](../registry/TRUTH_CORE.md); **NO-LIVE**.
- **Ideas package docstring (PR #2258):** `src/strategies/ideas/__init__.py` — Wortlaut „offene Punkte“ statt TODO-Token im Docstring; **NO-LIVE**.
- **J3 (`--prefix` scan filter, PR #2259):** `scripts/ops/placeholders/generate_placeholder_reports.py` — wiederholbares `--prefix PATH` für repo-relative Teilbäume; Smoke `tests/ops/test_generate_placeholder_reports_smoke.py`; **NO-LIVE**.
- **Docs sync (CURRENT_FOCUS + J3 runbook, PR #2260):** [CURRENT_FOCUS.md](CURRENT_FOCUS.md) „Recently landed“ für #2256–#2259; [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) — J3 `--prefix` und Beispielbefehl; **NO-LIVE**.
- **Merge log test fixture (PR #2261):** `tests/test_ops_merge_log_generator.py` — eingebettetes Mini-Template mit Ellipsen-Platzhaltern statt `- TODO` (weniger Placeholder-Inventar-Rauschen); **NO-LIVE**.
- **Desktop shortcuts wording (PR #2262):** `scripts/utils/install_desktop_shortcuts.sh` — Nutzer-Text „task board“ statt „TODO board“; Pfade/Dateinamen unverändert; **NO-LIVE**.
- **Runner index curator docstring (PR #2263):** `scripts/dev/curate_runner_index.py` — Readiness **TODO** als fester Status (neben READY/PARTIAL), kein allgemeiner Aufgaben-Marker; **NO-LIVE**.
- **Chat-led snapshot §5 (PR #2265):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Stichprobentabelle aktualisiert (u. a. I1 Backtest/Tracker, Truth #2256/#2257, J3 #2259); **NO-LIVE**.

**GitHub — Truth-Gate Required Checks auf `main`:** Verifiziert (Apr 2026): **`docs-drift-guard`** und **`repo-truth-claims`** sind als Required Status Checks gesetzt (Namen wie `.github/workflows/truth_gates_pr.yml` Job-`name:`). Re-Check lokal: `python3 scripts/ops/ensure_truth_branch_protection.py --check` · ergänzen mit `--apply` nur mit Admin-Rechten; Registry: [`TRUTH_BRANCH_PROTECTION.md`](../registry/TRUTH_BRANCH_PROTECTION.md).

---

## Next three concrete steps

1. For **new work**, start from [FINISH_PLAN](FINISH_PLAN.md) and the Frontdoor; edit **this file** when the active goal or branch context changes.
2. Keep pasting the **bootstrap block** from [PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP](../runbooks/PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md) for new assistant chats.
3. After docs edits, run `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` (changed-scope docs gates).

---

## Next small focus (suggestion)

- **Primary:** [Stufe J — Forward-Pipeline / Demo-Stub](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#stufe-j--scripts--demo-daten-operativ-niedrig-priorisiert) (weiter **STUB**, **NO-LIVE**) oder ein **einzelner** Chat-led Gap aus [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md).
- **Optional:** Bei einem **Release-Kandidaten** die Rubric nutzen — [Release checklist & Go/No-Go rubric](../release/runbooks/RELEASE_CHECKLIST_AND_GO_NO_GO_RUBRIC.md) §4; regelmäßig `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`. Kein Scope-Creep; keine Live-Freigabe durch bloßes Dokumentieren.

---

## Blockers / risks

- None known for **main** at last verification below; reopen if required CI/docs gates regress.

---

## Parked (bewusst nicht aktiv)

- **F3 — Learning/Promotion Roadmap v2** (optional): Wunschliste in `docs&#47;LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md` §12; Runbook-Stufe F und Tag **DOC** in [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md). Kein Lieferzwang bis Priorisierung.

---

## Last verification (evidence-first)

| Date (UTC) | What was verified | Command or artifact |
|------------|---------------------|----------------------|
| 2026-03-26 | PR #2047 merged: `CURRENT_FOCUS.md`, `PEAK_TRADE_CHAT_CONTINUITY_BOOTSTRAP.md`, FINISH_PLAN cross-link | https://github.com/rauterfrank-ui/Peak_Trade/pull/2047 (merged 2026-03-26T18:40:04Z) |
| 2026-03-27 | Finish Plan **PR 6** slice: Live-Ops pack cross-links (Frontdoor, runbooks, safety) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2059 |
| 2026-03-27 | Finish Plan **PR 7** slice: observability / status report navigation | https://github.com/rauterfrank-ui/Peak_Trade/pull/2060 |
| 2026-03-27 | Finish Plan **PR 8** slice: release checklist + Go/No-Go rubric (`docs/ops/release/`) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2061 |
| 2026-03-27 | `CURRENT_FOCUS` refresh post PR 6–8 (this file) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2062 |
| 2026-03-27 | `CURRENT_FOCUS` post-merge finalize (table + branch pointer on `main`) | https://github.com/rauterfrank-ui/Peak_Trade/pull/2063 |
| 2026-04-01 | Post–truth-layer / gates / officers: `CURRENT_FOCUS` human anchor updated (this file); docs gates snapshot PASS locally | `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-01 | Post–J2 (PR #2168): `CURRENT_FOCUS` refresh — J2 landed, pointer cleaned | PR #2168 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-02 | Post–J3 (PR #2170): `CURRENT_FOCUS` refresh — J3 placeholder inventory smoke landed | PR #2170 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-03 | Post–J1 (PR #2172 / #2173): `CURRENT_FOCUS` refresh — J1 loader edge cases + Kraken shortfall observability landed | PR #2172 / #2173 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-02 | Truth-Gate `main` branch protection: required checks **`docs-drift-guard`** + **`repo-truth-claims`** verified; `ensure_truth_branch_protection.py` stdin fix on `main` | `python3 scripts/ops/ensure_truth_branch_protection.py --check` (PASS); PR #2176 |
| 2026-04-02 | Finish Plan **PR 7** operator-verify docs: `CURRENT_FOCUS`, `LIVE_STATUS_REPORTS` §7, `FINISH_PLAN` | PR #2177 |
| 2026-04-02 | Finish Plan **PR 8** post-merge: `CURRENT_FOCUS` + Release Rubric §4 + `FINISH_PLAN` PR 8 | PR #2178 |
| 2026-04-03 | Stufe J / J1: Forward-CLI ``--ohlcv-source`` case-insensitive (`_shared_forward_args`); Runbook-Zeile | PR #2180 |
| 2026-04-03 | Chat-led gaps: Querverweis `RUNBOOK_CHAT_LED_OPEN_FEATURES` → `RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED` (Stufe J) | PR #2182 |
| 2026-04-02 | Post–PR #2184: `CURRENT_FOCUS` refresh — backtest evidence `symbol` aus Config + Chat-led-Stichprobe §5 | PR #2184 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-02 | Post–chat-led §5: PR #2193 (Scripts) + PR #2194 (Research-Stubs) in `RUNBOOK_CHAT_LED_OPEN_FEATURES` | PR #2193 / #2194 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-07 | Post–PR #2198: J1 Forward/Portfolio CLI NO-LIVE/Epilog + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2198 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-08 | Post–PR #2200: J3 placeholder inventory CLI NO-LIVE/`--help` + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2200 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-09 | Post–PR #2202: J2 Optuna placeholder CLI NO-LIVE/`--help` + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2202 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-10 | Post–PR #2204: `run_optuna_study` CLI NO-LIVE/Placeholder-Abgrenzung + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2204 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-11 | Post–PR #2206: `run_sweep_pipeline` CLI NO-LIVE + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2206 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |

---

## Branch / PR pointer (optional)

- **Merged:** [PR #2206](https://github.com/rauterfrank-ui/Peak_Trade/pull/2206) — Unified sweep pipeline CLI NO-LIVE help (`run_sweep_pipeline` + smoke) on `main`.
- **Merged:** [PR #2204](https://github.com/rauterfrank-ui/Peak_Trade/pull/2204) — Optuna full study CLI NO-LIVE help (`run_optuna_study` vs. placeholder + smoke) on `main`.
- **Merged:** [PR #2202](https://github.com/rauterfrank-ui/Peak_Trade/pull/2202) — J2 Optuna placeholder CLI NO-LIVE help (`run_study_optuna_placeholder` + smoke) on `main`.
- **Merged:** [PR #2200](https://github.com/rauterfrank-ui/Peak_Trade/pull/2200) — J3 placeholder inventory CLI NO-LIVE help (`generate_placeholder_reports` + smoke) on `main`.
- **Merged:** [PR #2198](https://github.com/rauterfrank-ui/Peak_Trade/pull/2198) — J1 Forward/Portfolio CLI NO-LIVE help (`_shared_forward_args` + three entrypoints) on `main`.
- **Merged:** [PR #2194](https://github.com/rauterfrank-ui/Peak_Trade/pull/2194) — Chat-led §5 Research-Stubs row (`NO-LIVE`) on `main`.
- **Merged:** [PR #2193](https://github.com/rauterfrank-ui/Peak_Trade/pull/2193) — Chat-led §5 Scripts row (`resolve_backtest_symbol`) on `main`.
- **Merged:** [PR #2184](https://github.com/rauterfrank-ui/Peak_Trade/pull/2184) — Chat-led mini-slice: `run_backtest` evidence `symbol` from config + runbook snapshot row on `main`.
- **Merged:** [PR #2173](https://github.com/rauterfrank-ui/Peak_Trade/pull/2173) — J1 Kraken shortfall observability + style follow-up on `main`.
- **Merged:** [PR #2172](https://github.com/rauterfrank-ui/Peak_Trade/pull/2172) — J1 shared OHLCV loader edge-case hardening on `main`.
- **Merged:** [PR #2170](https://github.com/rauterfrank-ui/Peak_Trade/pull/2170) — J3 placeholder inventory generator smoke + runbook note (`NO-LIVE` tooling).
- **Merged:** [PR #2168](https://github.com/rauterfrank-ui/Peak_Trade/pull/2168) — J2 Optuna placeholder / minimal study runner + related CI fixes on `main`.
- **Doc edits to this file:** short-lived `feat&#47;*` branch as usual; Finish Plan **PR 6–8** spine unchanged; **NO-LIVE** default.

---

## How Workflow Officer and Update Officer fit

- **Workflow Officer** (`src/ops/workflow_officer.py`): runs profiled checks, emits `summary` with follow-up ranking, handoff, next-chat preview, operator/executive views, **sequencing** metadata, and **`unified_truth_status`** (docs drift + repo truth claims via `ops.truth`). Use it to see **repo gate state**, not to replace this file.
- **Update Officer** (`src/ops/update_officer.py` + `UPDATE_OFFICER_V*.md` runbooks): separate evolution of operator-facing consolidation and WebUI wiring; **`summary.unified_truth_status`** uses the same truth integration layer.
