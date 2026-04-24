---
title: "Current focus — operator-maintained (not auto-generated)"
status: DRAFT
scope: docs-only (NO-LIVE)
last_updated: 2026-04-24
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

- PR #2889: Added a Portfolio CLI subprocess smoke for local OHLCV CSV input with temp `config.toml`, local CSV, and `--no-report`; test-only; no repo-root reports; no Paper/Shadow/Evidence mutation; no gate changes.
- PR #2890: Hardened the Portfolio CLI contract with `--config-path`, explicit `main()` exit codes, `SystemExit(main())`, and subprocess validation for missing CSV/config inputs; J1 local CSV parity is now covered across Generate, Evaluate, and Portfolio paths and is pausierbar.
- PR #2887: Added a Chat-led J1 Forward Scripts operator quick reference to [CLI_CHEATSHEET.md](../../CLI_CHEATSHEET.md), keeping the existing three-column table shape despite the `dummy|kraken` source text in the row; navigation-only and NO-LIVE.
- PR #2885: Added a Chat-led J1 Forward Demo-Stub operator quick reference to [CLI_CHEATSHEET.md](../../CLI_CHEATSHEET.md), with the Demo-Stub link in the existing table cell; navigation-only and NO-LIVE.
- PR #2882: Added CLI cheatsheet discoverability for the full Optuna study CLI (`scripts&#47;run_optuna_study.py --help`), explicitly separated from the J2 placeholder surface and kept NO-LIVE/research-scoped.
- PR #2880: Added CLI cheatsheet discoverability for the forward dummy pipeline demo (`scripts&#47;dev&#47;run_forward_dummy_pipeline_demo.sh`), with NO-LIVE/local-only notes and no broker/exchange-order, Paper/Shadow/Evidence, or gate changes.
- PR #2878: Added CLI cheatsheet discoverability for the unified sweep pipeline (`scripts&#47;run_sweep_pipeline.py --help`), with explicit separation from lower-level grid/preset sweep helpers and NO-LIVE/local-research notes.
- PR #2876: Added CLI cheatsheet discoverability for the J3 placeholder report generator (`scripts&#47;ops&#47;placeholders&#47;generate_placeholder_reports.py --help`, `--prefix src&#47;`, `.ops_local` output), with NO-LIVE/local-only notes and no broker/exchange-order, Paper/Shadow/Evidence, or gate changes.
- PR #2874: Added CLI cheatsheet discoverability for the J2 Optuna placeholder surface (`--help` / `--dry-run` on `scripts&#47;run_study_optuna_placeholder.py`), explicitly separate from `scripts&#47;run_optuna_study.py` and NO-LIVE with no broker/exchange-order, Paper/Shadow/Evidence, or gate changes.
- PR #2868: Added CLI cheatsheet discoverability for the J1 local OHLCV CSV source, including `csv`, `fixture`, `--ohlcv-csv PATH`, `{symbol}` path expansion, and NO-LIVE/local-only notes.
- PR #2869: Added a subprocess smoke for `generate_forward_signals.py` with local CSV OHLCV input; test-only, tempfile/local, no live/broker/order/evidence/gate changes.
- PR #2870: Added a subprocess smoke for `evaluate_forward_signals.py` with local CSV OHLCV input after generated signals; test-only and local-only.
- PR #2871: Added a negative subprocess validation test for `evaluate_forward_signals.py` when `--ohlcv-source csv` is used without `--ohlcv-csv`.
- PR #2872: Added Evaluate + local CSV guidance to the CLI cheatsheet, including `--config-path`, `--output-dir`, and the `as_of`/entry-bar caveat.
- PR #2865: Added deterministic local OHLCV `csv` source with `fixture` alias for J1 forward/portfolio CLIs; requires `--ohlcv-csv PATH`, supports `{symbol}` path expansion, and remains local/file-based with no live, broker, exchange-order, Paper/Shadow/Evidence, or gate changes.
- PR #2857: Added a CLI cheatsheet Bounded Pilot / First-Live navigation box; operator-navigation-only, no live authorization or gate bypass.
- PR #2858: Added a GETTING_STARTED pointer to that CLI cheatsheet navigation box; navigation-only.
- PR #2859: Aligned Readiness Ladder L3 wording with DRAFT entry-contract / boundary-note maturity; no DRAFT status uplift.
- PR #2860: Aligned bounded-pilot L3 entry contract and candidate-flow wording to DRAFT anchor / candidate-scoped review language.
- PR #2861: Aligned the bounded-pilot incident abort triage compass purpose wording to DRAFT orientation-anchor maturity.
- **Unified Truth Core** (`src/ops/truth/`): shared loaders + deterministic evaluators for docs drift and repo truth claims — [TRUTH_CORE.md](../registry/TRUTH_CORE.md).
- **CI:** workflow [.github/workflows/truth_gates_pr.yml](../../../.github/workflows/truth_gates_pr.yml) defines jobs **`docs-drift-guard`** and **`repo-truth-claims`** (PR / merge queue / manual dispatch).
- **Officers:** [Workflow Officer](#how-workflow-officer-and-update-officer-fit) and [Update Officer](#how-workflow-officer-and-update-officer-fit) include **`summary.unified_truth_status`** (read-only diagnostics from the same core).
- **Forward / ops context:** J1 forward-pipeline slices and bounded-pilot / canary-live-entry runbooks merged per prior PRs; posture unchanged (**NO-LIVE** default unless a governed runbook explicitly says otherwise).
- **Stufe J (Forward-Demo-Stub, PR #2297):** ``scripts/dev/run_forward_dummy_pipeline_demo.sh`` — offline Dummy-Pipeline Generate → Evaluate mit ``as_of``-Korrektur (wie Integrationssmoke); Runbook [Operator-Kurzreferenz (J1)](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md#operator-kurzreferenz-j1-forward-no-live) Punkt 6; **NO-LIVE**.
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
- **J1 (Forward Operator-Kurzreferenz, PR #2267):** [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) — „Operator-Kurzreferenz (J1 Forward, NO-LIVE)“ (dummy/kraken, ``--n-bars``/Portfolio, ``scripts/_shared_forward_args.py``, optionaler Integrationssmoke); docs-token-policy-konforme ``&#47;``-Encodings; **NO-LIVE**.
- **CURRENT_FOCUS sync post–#2267 (PR #2268):** „Recently landed“ + Verifikation für PR #2267; **NO-LIVE**.
- **Chat-led §5 J1 Forward row (PR #2269):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile J1 Forward (Scripts); **NO-LIVE**.
- **PLACEHOLDER_POLICY inventory-noise note (PR #2270):** [PLACEHOLDER_POLICY.md](../PLACEHOLDER_POLICY.md) — Hinweis auf erwartete hohe Zähler in der Policy-Datei; **NO-LIVE**.
- **slice_from_backup Task board wording (PR #2271):** `scripts/utils/slice_from_backup.sh` — „Task board“ statt wörtlichem Marker in Restore-Text; **NO-LIVE**.
- **curate + reentry J3 false TODO hits (PR #2272):** `scripts/dev/curate_runner_index.py`, `scripts/ops/reentry_runbook.sh` — Readiness- bzw. rg-Pattern ohne wörtlichen ``TODO``-Token im Quelltext; **NO-LIVE**.
- **Live status report CHECK fixtures (PR #2273):** `tests/test_live_status_report.py` — Checklisten-Beispiele mit ``CHECK:``; **NO-LIVE**.
- **Placeholder report titles + config/tests J3 noise (PR #2274):** `generate_placeholder_reports.py` — neue Markdown-Überschriften für lokale Inventar-Reports (früherer Heading-Prefix mit „TODO“ und Slash entfällt); Smoke + CLI-Fixtures + ``risk_layer_v1_example.toml``; **NO-LIVE**.
- **Chat-led §5 Infostream-Zyklus (PR #2276):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Infostream / Zyklus“ (Run-Cycle-CLI, Delivery-Kontext, lokale Artefakte); **NO-LIVE**.
- **Chat-led §5 Execution C1 (PR #2278):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Execution / Orders (C1)“ (Stufe C1 im geordneten Runbook; ``exchange.py`` und ``paper.py``); **NO-LIVE**.
- **Chat-led §5 Market Outlook (PR #2280):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Market Outlook“ (tägliche Automation: ``generate_market_outlook_daily.py`` und zugehöriger GitHub-Workflow); **NO-LIVE**.
- **Chat-led §5 Learning Loop F2 (PR #2282):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Learning Loop (F2)“ (Emitter und Bridge inkl. Tests; Stufe F2 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Observability H1 (PR #2284):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Observability (H1)“ (HTTP-Session und Metrics-Server; Stufe H1 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Execution Telemetry F5 (PR #2286):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Execution Telemetry (F5)“ (``telemetry.py`` und zugehörige Tests; Stufe F5 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 New Listings F6 (PR #2288):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „New Listings (F6)“ (Collector-Basis ``base.py`` und Contract-Tests; Stufe F6 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Knowledge F4 (PR #2290):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Knowledge (F4)“ (``vector_db.py`` und Memory-Tests; Stufe F4 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Infostream F1 (PR #2292):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Infostream (F1)“ (``evaluator.py`` und ``test_infostream_basic.py``; Stufe F1 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Evidence G1 (PR #2293):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Evidence (G1)“ (``evidence_pack_schema.py`` und ``test_evidence_pack_schema.py``; Stufe G1 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Evidence G2 (PR #2294):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Evidence (G2)“ (``evidence_pack_generator.py`` und ``test_evidence_pack_generator.py``; Stufe G2 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Evidence G3 (PR #2295):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Evidence (G3)“ (``psychology_heuristics.py`` und ``test_psychology_heuristics.py``; Stufe G3 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 Evidence G4 (PR #2296):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „Evidence (G4)“ (``test_health_history.py`` und ``test_test_health_runner.py``; Stufe G4 im geordneten Runbook **DONE**); **NO-LIVE**.
- **Chat-led §5 J1 Forward Demo (PR #2298):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Snapshot-Zeile „J1 Forward (Demo-Stub)“ (``run_forward_dummy_pipeline_demo.sh``, Operator-Kurzreferenz §6); **NO-LIVE**.
- **Chat-led §5 Learning / Promotion vs F2 (PR #2308):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Zeile „Learning / Promotion“: iteratives End-to-End + domänenspezifische Producer vs. **DONE** Kern-API (Verweis auf Zeile **Learning Loop (F2)**); Links zu Architektur-Doku, ``emitter.py``, ``bridge.py``; **NO-LIVE**.
- **Chat-led §5 ML Meta-Labeling (PR #2310):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Zeile „ML / Meta-Labeling“: Research-only, implementierte Oberfläche (u. a. ``apply_meta_model``, ``compute_meta_labels``, ``_create_model`` mit Random Forest und optionalem XGBoost), unbekannte ``model_type`` → ``NotImplementedError``; **NO-LIVE**.
- **Chat-led §5 Infostream, Market Outlook, Live/Safety (PR #2312):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Infostream-Zyklus als implementierter Pfad, MarketSentinel v0 (CLI und Workflow, Test-Flag ohne LLM), ``SafetyGuard`` und Execution-Guards ohne echte Live-Order-Calls; **NO-LIVE**.
- **Chat-led §5 Risk, Execution C1, Research (PR #2314):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Kill-Switch D2 erledigt, C1 STUB/GAP mit Testnet-Abgrenzung, Research-Stubs mit E3 DONE für Bouchaud/Gatheral; **NO-LIVE**.
- **Chat-led §5 J1 Forward Demo path (PR #2316):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Zeile „J1 Forward (Demo-Stub)“: Ausgabe unter **.ops_local** (Unterordner **forward_dummy_pipeline_demo**); Kommentar in ``run_forward_dummy_pipeline_demo.sh`` mit Verweis auf Operator-Kurzreferenz Punkt 6; **NO-LIVE**.
- **Risk D2 + Chat-led (PR #2319):** D2-Hinweise in [KILL_SWITCH.md](../../risk/KILL_SWITCH.md), [KILL_SWITCH_ARCHITECTURE.md](../../risk/KILL_SWITCH_ARCHITECTURE.md), [README_KILL_SWITCH.md](../../../README_KILL_SWITCH.md); [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — §5 Risk-/Kill-Switch-Zeile und Session-Beispielwortlaut; [TODO_KILL_SWITCH_ADAPTER_MIGRATION.md](../../../TODO_KILL_SWITCH_ADAPTER_MIGRATION.md); Deployment-/Support in `README_KILL_SWITCH` auf Markdown-Links und Code-Fences (robust gegenüber Token-Policy und Reference-Targets-Verifier); **NO-LIVE**.
- **Docs Reference Targets entity-unescape fix (PR #2321):** `verify_docs_reference_targets.sh` löst HTML-Entities vor dem `#`-Anchor-Split auf (`html.unescape`), damit token-policy-sichere Pfade wie `&#47;` oder `&#x2f;` nicht mehr in abgeschnittene Pseudo-Pfade mit Restfragment (`&`) zerfallen; neue Pass-Fixture `token_policy_html_entities.md`; **NO-LIVE**.
- **Chat-led §5 C1 + J1 align (PR #2324):** [RUNBOOK_CHAT_LED_OPEN_FEATURES.md](../runbooks/RUNBOOK_CHAT_LED_OPEN_FEATURES.md) — Zeilen „Execution / Orders (C1)“ und „J1 Forward (Scripts)“ an Stufe C1 bzw. Stufe J1 in [RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md](../runbooks/RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md) (u. a. C1: Dry-Run `LiveOrderExecutor`, Stub in `paper.py`, Abgrenzung ``testnet_executor``; J1: gemeinsamer OHLCV-Loader, Slice 4 Kraken opt-in, token-policy-konforme Script-Links); **NO-LIVE**.

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
| 2026-04-06 | Post–PR #2267: J1 Forward Operator-Kurzreferenz im geordneten Runbook; `CURRENT_FOCUS` refresh (this file) | PR #2267 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-02 | Post–PR #2184: `CURRENT_FOCUS` refresh — backtest evidence `symbol` aus Config + Chat-led-Stichprobe §5 | PR #2184 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-02 | Post–chat-led §5: PR #2193 (Scripts) + PR #2194 (Research-Stubs) in `RUNBOOK_CHAT_LED_OPEN_FEATURES` | PR #2193 / #2194 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-07 | Post–PR #2198: J1 Forward/Portfolio CLI NO-LIVE/Epilog + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2198 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-08 | Post–PR #2200: J3 placeholder inventory CLI NO-LIVE/`--help` + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2200 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-09 | Post–PR #2202: J2 Optuna placeholder CLI NO-LIVE/`--help` + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2202 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-10 | Post–PR #2204: `run_optuna_study` CLI NO-LIVE/Placeholder-Abgrenzung + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2204 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-11 | Post–PR #2206: `run_sweep_pipeline` CLI NO-LIVE + help smoke; `CURRENT_FOCUS` refresh (this file) | PR #2206 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PRs #2268–#2274: `CURRENT_FOCUS` + chat-led + runbooks + J3 noise (scripts/tests/config) | PR #2268–#2274 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2276: Chat-led §5 Infostream-Zyklus + `CURRENT_FOCUS` refresh (this file) | PR #2276 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2278: Chat-led §5 C1 Execution + `CURRENT_FOCUS` refresh (this file) | PR #2278 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2280: Chat-led §5 Market Outlook + `CURRENT_FOCUS` refresh (this file) | PR #2280 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2282: Chat-led §5 Learning Loop F2 + `CURRENT_FOCUS` refresh (this file) | PR #2282 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2284: Chat-led §5 Observability H1 + `CURRENT_FOCUS` refresh (this file) | PR #2284 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2286: Chat-led §5 Execution Telemetry F5 + `CURRENT_FOCUS` refresh (this file) | PR #2286 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2288: Chat-led §5 New Listings F6 + `CURRENT_FOCUS` refresh (this file) | PR #2288 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-06 | Post–PR #2290: Chat-led §5 Knowledge F4 + `CURRENT_FOCUS` refresh (this file) | PR #2290 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-12 | Post–PR #2292: Chat-led §5 Infostream F1 + `CURRENT_FOCUS` refresh (this file) | PR #2292 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-12 | Post–PR #2293: Chat-led §5 Evidence G1 + `CURRENT_FOCUS` refresh (this file) | PR #2293 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-12 | Post–PR #2294: Chat-led §5 Evidence G2 + `CURRENT_FOCUS` refresh (this file) | PR #2294 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-12 | Post–PR #2295: Chat-led §5 Evidence G3 + `CURRENT_FOCUS` refresh (this file) | PR #2295 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-12 | Post–PR #2296: Chat-led §5 Evidence G4 + `CURRENT_FOCUS` refresh (this file) | PR #2296 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-12 | Post–PR #2297: Stufe J Forward-Demo-Stub + `CURRENT_FOCUS` + Runbook (this file) | PR #2297 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-12 | Post–PR #2298: Chat-led §5 J1 Forward Demo + `CURRENT_FOCUS` refresh (this file) | PR #2298 merge; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-24 | Post–PRs #2857–#2861: bounded-pilot operator-navigation + DRAFT maturity wording; `CURRENT_FOCUS` refresh (this file) | PR #2857–#2861 merge; `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` |
| 2026-04-24 | J1 local OHLCV CSV source (#2865) | `uv run python -m pytest tests/test_dummy_ohlcv.py tests/test_shared_forward_args_cli.py tests/test_forward_generate_evaluate_integration_smoke.py tests/test_run_portfolio_backtest_v2_cli.py`; `uv run ruff check scripts/_shared_ohlcv_loader.py scripts/_shared_forward_args.py scripts/generate_forward_signals.py scripts/evaluate_forward_signals.py scripts/run_portfolio_backtest_v2.py tests/test_dummy_ohlcv.py tests/test_shared_forward_args_cli.py tests/test_forward_generate_evaluate_integration_smoke.py`; `uv run ruff format` (same paths) | Local/file-based only; no live/broker/order/evidence/gate changes. |
| 2026-04-24 | J1 local CSV follow-up closure (#2868-#2872) | `uv run python -m pytest tests/test_dummy_ohlcv.py tests/test_forward_generate_evaluate_integration_smoke.py -q`; `uv run ruff check tests/test_dummy_ohlcv.py tests/test_forward_generate_evaluate_integration_smoke.py`; `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed` — *Outcome:* J1 local CSV is pausierbar (loader/template tests, Generate/Evaluate subprocess smokes, negative Evaluate validation, runbook/CURRENT_FOCUS and cheatsheet coverage). |
| 2026-04-24 | J2 Optuna placeholder cheatsheet sync (#2874) | `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; docs-only discoverability for placeholder/dry-run surface, NO-LIVE. |
| 2026-04-24 | J3 placeholder reports cheatsheet sync (#2876) | `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; docs-only discoverability for placeholder report generator, NO-LIVE/local-only. |
| 2026-04-24 | Unified sweep pipeline cheatsheet sync (#2878) | `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; docs-only discoverability for `scripts&#47;run_sweep_pipeline.py --help`, NO-LIVE/local-research. |
| 2026-04-24 | Forward dummy pipeline demo cheatsheet sync (#2880) | `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; docs-only discoverability for `scripts&#47;dev&#47;run_forward_dummy_pipeline_demo.sh`, NO-LIVE/local-only. |
| 2026-04-24 | Optuna study CLI cheatsheet sync (#2882) | `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; docs-only discoverability for `scripts&#47;run_optuna_study.py --help`, NO-LIVE/research-scoped. |
| 2026-04-24 | Chat-led Forward Demo cheatsheet sync (#2885) | `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; docs-only navigation link from Chat-led Demo-Stub row to CLI_CHEATSHEET, NO-LIVE. |
| 2026-04-24 | Chat-led Forward Scripts cheatsheet sync (#2887) | `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; docs-only navigation link from Chat-led Scripts row to CLI_CHEATSHEET, three-column table preserved. |
| 2026-04-24 | J1 Portfolio local CSV contract closure (#2889-#2890) | `uv run python -m pytest tests/test_run_portfolio_backtest_v2_cli.py -q`; `uv run python -m pytest tests/test_shared_forward_args_cli.py -q`; `uv run ruff check scripts/run_portfolio_backtest_v2.py tests/test_run_portfolio_backtest_v2_cli.py`; `uv run ruff format --check scripts/run_portfolio_backtest_v2.py tests/test_run_portfolio_backtest_v2_cli.py`; `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`; `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`; `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`; J1 local CSV pausierbar after Generate/Evaluate/Portfolio coverage and portfolio CLI contract hardening. |

---

## Branch / PR pointer (optional)

- **Merged:** [PR #2298](https://github.com/rauterfrank-ui/Peak_Trade/pull/2298) — Chat-led §5 J1 Forward Demo snapshot row on `main`.
- **Merged:** [PR #2297](https://github.com/rauterfrank-ui/Peak_Trade/pull/2297) — Stufe J Forward-Demo-Stub (`run_forward_dummy_pipeline_demo.sh`) on `main`.
- **Merged:** [PR #2296](https://github.com/rauterfrank-ui/Peak_Trade/pull/2296) — Chat-led §5 Evidence G4 snapshot row on `main`.
- **Merged:** [PR #2295](https://github.com/rauterfrank-ui/Peak_Trade/pull/2295) — Chat-led §5 Evidence G3 snapshot row on `main`.
- **Merged:** [PR #2294](https://github.com/rauterfrank-ui/Peak_Trade/pull/2294) — Chat-led §5 Evidence G2 snapshot row on `main`.
- **Merged:** [PR #2293](https://github.com/rauterfrank-ui/Peak_Trade/pull/2293) — Chat-led §5 Evidence G1 snapshot row on `main`.
- **Merged:** [PR #2292](https://github.com/rauterfrank-ui/Peak_Trade/pull/2292) — Chat-led §5 Infostream F1 snapshot row on `main`.
- **Merged:** [PR #2290](https://github.com/rauterfrank-ui/Peak_Trade/pull/2290) — Chat-led §5 Knowledge F4 snapshot row on `main`.
- **Merged:** [PR #2288](https://github.com/rauterfrank-ui/Peak_Trade/pull/2288) — Chat-led §5 New Listings F6 snapshot row on `main`.
- **Merged:** [PR #2286](https://github.com/rauterfrank-ui/Peak_Trade/pull/2286) — Chat-led §5 Execution Telemetry F5 snapshot row on `main`.
- **Merged:** [PR #2284](https://github.com/rauterfrank-ui/Peak_Trade/pull/2284) — Chat-led §5 Observability H1 snapshot row on `main`.
- **Merged:** [PR #2282](https://github.com/rauterfrank-ui/Peak_Trade/pull/2282) — Chat-led §5 Learning Loop F2 snapshot row on `main`.
- **Merged:** [PR #2280](https://github.com/rauterfrank-ui/Peak_Trade/pull/2280) — Chat-led §5 Market Outlook snapshot row on `main`.
- **Merged:** [PR #2278](https://github.com/rauterfrank-ui/Peak_Trade/pull/2278) — Chat-led §5 C1 execution snapshot row on `main`.
- **Merged:** [PR #2276](https://github.com/rauterfrank-ui/Peak_Trade/pull/2276) — Chat-led §5 Infostream cycle snapshot row on `main`.
- **Merged:** [PR #2274](https://github.com/rauterfrank-ui/Peak_Trade/pull/2274) — Placeholder report titles + config/tests J3 noise on `main`.
- **Merged:** [PR #2273](https://github.com/rauterfrank-ui/Peak_Trade/pull/2273) — Live status report CHECK fixtures on `main`.
- **Merged:** [PR #2272](https://github.com/rauterfrank-ui/Peak_Trade/pull/2272) — curate + reentry J3 false TODO hits on `main`.
- **Merged:** [PR #2271](https://github.com/rauterfrank-ui/Peak_Trade/pull/2271) — slice_from_backup Task board wording on `main`.
- **Merged:** [PR #2270](https://github.com/rauterfrank-ui/Peak_Trade/pull/2270) — PLACEHOLDER_POLICY inventory-noise note on `main`.
- **Merged:** [PR #2269](https://github.com/rauterfrank-ui/Peak_Trade/pull/2269) — Chat-led §5 J1 Forward snapshot row on `main`.
- **Merged:** [PR #2268](https://github.com/rauterfrank-ui/Peak_Trade/pull/2268) — CURRENT_FOCUS sync post–#2267 on `main`.
- **Merged:** [PR #2267](https://github.com/rauterfrank-ui/Peak_Trade/pull/2267) — J1 Forward Operator-Kurzreferenz in `RUNBOOK_UNIMPLEMENTED_FEATURES_ORDERED.md` (NO-LIVE) on `main`.
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
