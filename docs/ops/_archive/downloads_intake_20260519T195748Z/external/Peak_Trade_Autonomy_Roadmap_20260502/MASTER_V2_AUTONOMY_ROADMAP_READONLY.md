# Master V2 — Autonomy Roadmap (Read-only)

**Modus:** Statische Repo-Analyse + Einbindung externer Operator-Artefakte. **Keine** Freigabe für Live/Testnet/Execution. **Keine** Repo-Mutation durch dieses Dokument.

**Zeitpunkt:** 2026-05-02 UTC (ausgeführt gegen `main` nach `git pull --ff-only`).

---

## 1. Executive Summary

Peak_Trade hat eine **breite Master-V2-Spezifikationsfläche**, **implementierte Double-Play-/Pure-Stack-Pfade**, **Paper-/Shadow-/Class-A-CI**, **KillSwitch-/Gate-Infrastruktur** und **Go-Live-/First-Live-Ladder-Dokumentation** — alles unter strikter Trennung von **Signal**, **Evidence**, **Dashboard** und **Execution Authority**.

**24/7 Paper** als **benannte kanonische Produkt-/Workflow-Oberfläche** ist **nicht bestätigt** (verteilt: Offline Suites, scheduled Workflows, Class-A-Probe, Paper/Shadow-Audits, optional P77-Skript+Doku).

**Autonomie Richtung Stage ≥3** ist **blockiert** durch: fehlende kanonische Recurring-Verification-Oberfläche (Owner-Roster **TBD**), **STOP/HOLD** für Runtime-Umbauten, **Snapshot DTO v0** / **PaperExecutionEngine↔Futures** ausdrücklich **RUNTIME_NOT_WIRED**/approval-only, und Governance-Vorgaben (**keine** parallelen Evidence-Surfaces).

**Reuse vor Neuem:** vorhandene Kanonisierung nutzen — `MASTER_V2_GO_LIVE_ROADMAP_V0.md`, `MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`, `MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md`, Truth Map / Ops README — statt neuer Registry-/Handoff-Flächen.

---

## 2. Git State

| Feld | Wert |
|------|------|
| Branch | `main` |
| HEAD | `a81492155e28` (`docs(ops): link recent safe contract anchors v0 (#3239)`) |
| Upstream | `main...origin&#47;main` — zum Abfragezeitpunkt **up to date** |
| Working tree | **clean** |

**Letzte relevante Commits (Auszug):**

- `a8149215` — Ops README / Truth Map discoverability (#3239)
- `4c329df3` — Observability readmodel tests (#3238)
- `d1fb2105` — Double Play WebUI contract coherence (#3237)
- `aeae7f1e` — Market depth readmodel builder (#3236)

---

## 3. Existing System Inventory

### 3.1 Master V2 Specs

- **Count:** **108** Dateien `docs&#47;**&#47;MASTER_V2*.md` (Glob gegen `&#47;Users&#47;frnkhrz&#47;Peak_Trade&#47;docs`).
- **Steuerungs-Anker:** `docs&#47;ops&#47;specs&#47;MASTER_V2_GO_LIVE_ROADMAP_V0.md`, `docs&#47;ops&#47;specs&#47;MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md`, `MASTER_V2_PROMOTION_STATE_MACHINE_V1.md`, `MASTER_V2_GATE_FILL_VOCABULARY_BOUNDARY_LOCK_V1.md`, Bounded-Pilot L1–L5 Pointer-/Runbook-Crosswalk.
- **Double Play:** `MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md`, Pure-Stack Readiness / Parking Maps, WebUI-Verträge (`MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md`, Display Map).
- **Learning / AI / Autonomy (docs-only inventory):** `MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md`, `MASTER_V2_LEARNING_LOOP_TO_REPO_PATH_MAP_V0.md`, `MASTER_V2_KB_REGISTRY_EVIDENCE_TAXONOMY_V0.md`.

### 3.2 Implementierung (`src&#47;trading&#47;master_v2&#47;`)

- **22** Python-Module u. a. `double_play_state.py`, `double_play_composition.py` (explizit non-authorizing), `double_play_survival.py`, `double_play_suitability.py`, `double_play_capital_slot.py`, `double_play_futures_input*.py`, `double_play_dashboard_display.py`, Decision-Packet-/Replay-/Evaluator-Pfade.

### 3.3 Tests (`tests&#47;trading&#47;master_v2&#47;`)

- **16** Testdateien (Komposition, State, Survival, Suitability, Capital, Futures-Input/Producer, Dashboard Display, Pure-Stack-Contract, lokaler Evaluator/CLI).

### 3.4 Risk / KillSwitch / Gates

- **KillSwitch / State:** `src&#47;ops&#47;gates&#47;risk_gate.py`, `src&#47;risk_layer&#47;kill_switch&#47;cli.py`, `src&#47;execution&#47;risk_hook_impl.py`.
- **Live-/Pilot-Umfeld:** `src&#47;core&#47;environment.py` (`PT_LIVE_CONFIRM_TOKEN_ENV`), `scripts&#47;ops&#47;run_live_pilot_session.sh`, Tests `tests&#47;ops&#47;test_run_bounded_pilot_session.py`.
- **Networked Entry Contract:** `src&#47;execution&#47;networked&#47;entry_contract_v1.py` (`PT_CONFIRM`, `PT_CONFIRM_TOKEN`).
- **Execution Governance:** `src&#47;execution&#47;__init__.py` (live gesperrt), `src&#47;execution&#47;pipeline.py`, `src&#47;execution&#47;orchestrator.py`.

### 3.5 PaperExecutionEngine / Paper / Shadow

- **WP1B:** `src&#47;execution&#47;paper&#47;engine.py`.
- **Futures Accounting / Snapshot DTO v0:** `src&#47;execution&#47;paper&#47;futures_accounting.py` — `FuturesPaperAccountingSnapshotV0`; Spec §7 `MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md`; Tests `tests&#47;execution&#47;paper&#47;test_futures_accounting_snapshot_dto_v0.py`, `test_paper_engine_futures_seam_v0.py`.

### 3.6 CI / Scheduled / Class-A / Offline

- **Workflows:** **73** YAML-Dateien unter `.github&#47;workflows&#47;` — u. a. `offline_suites.yml`, `class-a-shadow-paper-scheduled-probe-v1.yml`, `ci-scheduled-paper-and-export-smoke.yml`, `prj-scheduled-shadow-paper-features-smoke.yml`, `paper_session_audit_evidence.yml`, `paper_tests_audit_evidence.yml`, `shadow_paper_smoke.yml`, `master_v2_dry_smoke.yml`, `prbe-shadow-testnet-scorecard.yml`, `prbj-testnet-exec-events.yml`, Scorecards/Pilot (`prbd-live-readiness-scorecard.yml`, `prbi-live-pilot-scorecard.yml`).
- **Guardrails:** `scripts&#47;ci&#47;scheduled_guardrails.sh`.
- **P77 (manual/script):** `docs&#47;analysis&#47;p77&#47;README.md`, `scripts&#47;ops&#47;online_readiness_daemon_v1.sh` (kein GH-Workflow-Name „24/7 Paper-Test-Daemon“ laut Linkage Review).

### 3.7 WebUI / Readmodels / Dashboard

- **App/Routes:** `src&#47;webui&#47;app.py` (Market/Double-Play SSR, Observability Hub, Paper-Shadow-Summary API).
- **Double Play JSON:** `src&#47;webui&#47;double_play_dashboard_display_json_route_v0.py`.
- **Readmodels:** `src&#47;webui&#47;market_depth_readmodel_v0&#47;`, `src&#47;webui&#47;paper_shadow_summary_readmodel_v0&#47;`.
- **Templates:** `templates&#47;peak_trade_dashboard&#47;` u. a. Market/Observability.

### 3.8 Evidence / Readiness / Registry

- **Gate-/Readiness:** `MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md`, `MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md`, Evidence-Packet-/Navigation-Maps, Session Review Pack Contracts.
- **Registry:** `docs&#47;ops&#47;registry&#47;INDEX.md`, `docs&#47;ops&#47;registry&#47;DOCS_TRUTH_MAP.md`, `config&#47;ops&#47;docs_truth_map.yaml`.

### 3.9 Strategy / Backtest / Research

- **Strategien:** `src&#47;strategies&#47;` (breites Portfolio + Research-Unterpakete).
- **Backtest:** `src&#47;backtest&#47;engine.py`, typischer Bezug zu `ExecutionPipeline.for_paper` (Overview-Dokumentation).

### 3.10 Env / Vars / Secrets (Repo-nachweisbar vs. nicht)

- **Namen** aus Workflows/YAML nachweisbar (`CLASS_A_SHADOW_PAPER_SCHEDULE_ENABLED`, `PT_PRJ_FEATURES_SMOKE_ENABLED`, `PT_SCHEDULED_*`, Export-Vars, `PEAK_KILL_SWITCH*`, `PEAK_TRADE_LIVE_*`, `PEAK_TRADE_PAPER_SHADOW_SUMMARY_*`) — **Werte/Owner nicht repo-provable**.
- **Externes Owner-Roster:** `OPERATOR_OWNER_ROSTER_WORKING_COPY.md` — Owner-Namen gesetzt; **Canonical Surface Clarification** weiterhin **TBD**.

---

## 4. Autonomy Stage Ladder

Jede Zeile: **Ziel** | **Reuse (Repo)** | **Lücken** | **Evidence** | **Tests** | **Ops/Owner** | **Erlaubt** | **Verboten** | **Promotion** | **STOP** | **Reuse statt Parallel-Surface**

**Stage 0 — Research / Backtest only**

- Ziel: Signale/Strategien offline validieren.
- Repo: `src&#47;backtest&#47;`, `src&#47;strategies&#47;`, Robustness-/Stress-Doku in Specs wo vorhanden.
- Lücken: keine Live/Testnet-Anbindung erforderlich.
- Evidence: Backtest-Artefakte, keine Gate-Freigabe.
- Tests: bestehende Unit/Integration je Suite.
- Ops: keine GH-Vars für Autonomie nötig.
- Erlaubt: Offline Compute.
- Verboten: Orders, Secrets, Daemon als „Authority“.
- Promotion zu 1: Governance akzeptiert Shadow-Advisory-Umfang.
- STOP: Gemischung von Report und Gate (Lens).
- Reuse: bestehende Forschungs-/Backtest-Pfade — keine neue Evidence-Registry.

**Stage 1 — Shadow advisory**

- Ziel: Shadow/Paper-Evidenz als **Beratung**, ohne Execution Authority.
- Repo: Shadow/Paper Workflows (`shadow_paper_smoke.yml`, Audit-Evidence), WebUI Read-only Observability.
- Lücken: klare Kennzeichnung „non-authorizing“ in Ops-Prozess (bereits in vielen Specs).
- Evidence: Workflow-/Audit-Artefakte, Paper/Shadow Reports.
- Tests: WebUI-/Readmodel-Contract-Tests wo vorhanden.
- Ops: Owner für Scheduled Vars (extern dokumentiert).
- Erlaubt: Scheduled Smoke **mit** Vars-Gates.
- Verboten: Dashboard als Freigabe; CI als Live-Promotion.
- Promotion zu 2: Operator benennt **kanonische** „recurring verification status“ Oberfläche (aktuell **TBD**).
- STOP: neue parallele Report-Surface ohne Owner.
- Reuse: Class-A + Offline Suites + bestehende Evidence-Pack Gates — keine zweite Handoff-Kette.

**Stage 2 — 24/7 Paper observation**

- Ziel: Dauerhafte **Beobachtung** Paper-Zustände ohne „Autonomous loop authority“.
- Repo: Cron/scheduled Jobs + Offline Suites + optional P77 Script — **aber keine** kanonisch benannte 24/7-Daemon-Produktfläche bestätigt.
- Lücken: Architekturentscheid ob Observation **ein** definierter Kanal oder bewusst verteilt bleibt.
- Evidence: zusammenhängende Zeitserien aus bestehenden Artefakten (ohne neue Index-Surface ohne Owner).
- Tests: Workflow-Contract-Tests (z. B. Export-Pack Verify), Offline-Suite Regression.
- Ops: `PT_SCHEDULED_*`, Export-Secrets policy — Owner roster „Change Process TBD“.
- Erlaubt: kontinuierliche **Monitoring**/Runs unter KillSwitch/Testnet=false Defaults in YAML.
- Verboten: implizite Live-Gates aus Scheduled Flags (Linkage Review Warnung).
- Promotion zu 3: Explizite **human approval** für geschlossenen Paper-Kandidatenloop + erweiterte Tests.
- STOP: Erfindung eines neuen „24/7 Paper Daemon“ Namens als Canonical ohne Architektur-Sign-off.
- Reuse: `offline_suites.yml`, Paper audits — dokumentierte Einordnung statt neuer Daemon-Spec.

**Stage 3 — Paper autonomous candidate loop**

- Ziel: Automatisierte **Kandidaten** (Signals → Paper) unter Risk/Gates — noch keine Live Authority.
- Repo: `PaperExecutionEngine`, Orchestrator-Pfade existieren — **aber** Futures Wiring / Snapshot Promotion aus Governance HOLD.
- Lücken: WP1B↔Futures, Producer↔Runner Integration nur nach Approval; erhöhte Contract-Tests.
- Evidence: gebündelte Session Review / Pure-Stack Evidence nach bestehenden FIRST_LIVE / SRP Contracts (Reuse).
- Tests: execution/paper characterization suites erweitern **ohne** LiveEnv.
- Ops: Freeze auf KillSwitch semantics; klare Rollback Playbooks (Bounded Pilot Runbooks existieren als Pointer-Specs).
- Erlaubt: Automation **innerhalb** Paper boundary + bestehende Risk Hooks.
- Verboten: Entfernen fail-closed Gates; Vermischung PT_* CI Flags mit LIVE_*.
- Promotion zu 4: Testnet bounded charter + Operator Sign-off Paket.
- STOP: Risk/KillSwitch/Execution Gate Code ändern ohne separates Governance-Slice.
- Reuse: `MASTER_V2_FIRST_LIVE_*` Evidence Contracts — keine parallele „Autonomy Evidence Pack“ Familie.

**Stage 4 — Testnet autonomous bounded loop**

- Ziel: Begrenzte echte Venue-Simulation/Testnet nur unter expliziten Workflows und Vars.
- Repo: Workflows mit Testnet im Namen (`prbe-shadow-testnet-scorecard.yml`, `prbj-testnet-exec-events.yml`) — **nicht** automatisch als Production-Live lesen.
- Lücken: Enge Kopplung an externes Sign-off; keine implizite Promotion aus Scorecards (Overview warnt vor Pilot-Workflows).
- Evidence: Testnet-Evidenzklassen laut Go-Live Roadmap Stage 3–4 Mapping.
- Tests: dedizierte CI-Verträge; keine Secrets im Repo.
- Ops: separate Owner für Testnet vs Paper (Roster warnt vor Vermischung).
- Erlaubt: bounded automation gemäß Workflow-Doku.
- Verboten: Testnet ≡ Live Semantik.
- Promotion zu 5: Pre-Live Package / External Decision per `MASTER_V2_GO_LIVE_ROADMAP_V0.md`.
- STOP: Exchange/Provider Secrets oder Order Authority ohne Pilot Charter.
- Reuse: bestehende Scorecard/Exec-Event Workflows auditieren — keine neue Testnet Registry.

**Stage 5 — Gated Live pilot**

- Ziel: Minimal Live Exposure nur mit Confirm Tokens / Bounded Pilot Scripts / Gate Sequence.
- Repo: `run_live_pilot_session.sh`, Gate vocab specs, KillSwitch readiness contracts.
- Lücken: menschliche externe Sign-offs außerhalb Repo.
- Evidence: PRE_LIVE Evidence Bundles / Authority Handoff Pakete (canonical dense specs).
- Tests: bounded/dry Smoke nicht als Authority (`master_v2_dry_smoke.yml`).
- Ops: Live Vars strikt getrennt von Paper CI Flags (Linkage Review).
- Erlaubt: nur explizit dokumentierte Pilot-Schritte.
- Verboten: Dashboard „Go“ Buttons als Authority.
- Promotion zu 6: Post-Pilot Review / Promotion State Machine — menschlich.
- STOP: jedes Gate-Fill ohne dokumentierte Evidence-Klasse.
- Reuse: `MASTER_V2_BOUNDED_PILOT_*` Pointer Contracts + Gate Status Index.

**Stage 6 — Bounded autonomous Live**

- Ziel: Mehr Automation **innerhalb** noch immer aktiver Gates/KillSwitch — nie ohne veto-fähige Stop-Kette.
- Repo: Execution Orchestrator bleibt abschaltbar; Governance locks bleiben.
- Lücken: organisational — kaum zusätzliche Repo-Surfaces ohne Duplikat-Risiko.
- Evidence: kontinuierliche Session Review / Incident Safe Stop Evidence (L5 Pointer Contract vorhanden).
- Tests: erweiterte Charakterisierung; keine Lockerung von `live_order_execution` ohne expliziten Governance-Commit (aktuell locked).
- Ops: On-call + KillSwitch drills dokumentiert.
- Erlaubt: mehr Automatisierung der **routine** nach approvals.
- Verboten: „silent“ widening von Risk Caps ohne Scope/Capital Governance (`MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md`).
- Promotion zu 7: nur nach expliziter Policy für Learning/Model Changes + keine Online-Learning ohne neue Governance (Learning Inventory: online adaptation prohibited).
- STOP: KillSwitch inactive oder ambiguous aliases.
- Reuse: Promotion State Machine Doc — keine neue autonomy-state YAML.

**Stage 7 — Self-improving autonomy with hard gates**

- Ziel: Gesteuerte Verbesserung von Modellen/Policies **offline**, strenge Approval Gates, **keine** Umgehung der Kontrollkette.
- Repo: Learning Inventory dokumentiert **Lücken** bei konsolidiertem Approval-State-Machine — Verbesserungspotenzial liegt in **Konsolidierung bestehender** Evidence Templates (`AI_AUTONOMY_*`), nicht neue Runtime-Schicht.
- Lücken: canonischer „model update approval state machine“ fehlt (Inventory §4).
- Evidence: Evidence Pack Template V2 + KB Registry Taxonomy — erweitern, nicht duplizieren.
- Tests: Replay/Determinism Gates (`l4_critic_replay_determinism*.yml`) als Referenzfamilie.
- Ops: klare Rollen für veto vs propose vs approve (`MASTER_V2_DECISION_AUTHORITY_MAP_V1.md`).
- Erlaubt: Offline Retrain / Candidate Promotion nach Evidence.
- Verboten: Online-Learning Einfluss auf Live ohne neue ausdrückliche Ausnahme (aktuell nicht vorhanden).
- Promotion: nicht automatisch — Periodische externe Auditierung.
- STOP: AI Orchestration als Execution Authority missinterpretiert.
- Reuse: `MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md` als Gap-Tabelle — keine zweite „AI autonomy roadmap“ Surface.

---

## 5. Authority Chain

1. **Signal ≠ Trade:** Strategien/`double_play_*` Outputs sind Inputs — keine Order ohne Execution+RISK Pfad (`pipeline.py`, `risk_hook_impl.py`).
2. **Strategy ≠ Authority:** Strategiewahl dokumentiert — Promotion über Governance nicht über Backtest allein (`MASTER_V2_STRATEGY_VISUAL_MAP_TO_REPO_SURFACE_MAP_V0.md` als Orientierung).
3. **AI ≠ Authority:** Learning Inventory & Governance (`AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`, Bayesian Evidence Decision) — Advisory dominance.
4. **Dashboard ≠ Freigabe:** WebUI Contracts explizit read-only / display (`MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md`, Overview §8).
5. **Paper ≠ Live:** WP1B SPOT_SIM Semantik; `live_order_execution` gesperrt (`src&#47;execution&#47;__init__.py`).
6. **Testnet ≠ Live:** Workflow-Namen warnen; Vars getrennt halten (`PEAK_TRADE_TESTNET_ONLY` in Workflow-Härtung erwähnt).
7. **Kontrollkette:** Master V2 / Double Play Logik → Risk → KillSwitch → Execution Gates → Venue — Reihenfolge fail-closed zu halten ist Implementierungs-/Governance-Pflicht, hier **No-Touch** ohne Approval.
8. **Learning Loop:** darf **Kandidaten** verbessern und Evidence erzeugen — **keine** Gate-Umgehung (`MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md` §5).

---

## 6. Current State Placement

| Frage | Einordnung |
|-------|------------|
| Bereits vorhanden (Code + Tests) | Double Play Pure Stack; WP1B; KillSwitch Hooks; Paper/Shadow/Class-A CI; WebUI Display + Readmodels; Futures Accounting **pure** + Snapshot DTO **implementiert aber nicht wired**. |
| Primär Docs/Specs | Go-Live Roadmap; First Live Ladder; 108× MASTER_V2 Specs; Bounded Pilot Pointer Runbooks; Learning Autonomy Inventory. |
| Pure/offline | Snapshot Builder `futures_accounting.py`; viele Master V2 Composition Tests; Accounting Snapshot Tests. |
| Read-only/reporting | Gate Status Index/Report Surface; WebUI SSR/API wo als read-only spezifiziert; Observability Hub laut aktueller Main-Linie (#3237–3239). |
| Nicht gewired | Snapshot DTO ↔ PaperExecutionEngine / Runner / Provider (`MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md` §7); Double Play Runtime Producer Parking Maps (Overview §11). |
| Nicht Live/Testnet (default posture) | Hauptentwicklung auf Paper/Shadow/Offline; Live/Testnet nur chartered Workflows — keine automatische Promotion. |
| Approval-only | Snapshot DTO Wiring; Futures Class A Completion; Scope/Capital Runtime edits; Risk/KillSwitch/Gate Mutation; Master V2 Runtime Producer Umbau (Governance HIGH-RISK). |

**Grobe Stage-Zuordnung heute:** überwiegend **Stage 0–1 realisiert** (Research + Shadow advisory Evidence); **Stage 2 teilweise technisch** (scheduled/offline Kontinuität) aber **operatorisch/kanonisch offen**; **Stage ≥3 nicht erreicht** wegen Wiring-/Governance-HOLD und fehlender kanonischer Verification-Oberfläche.

---

## 7. Gap Register

### P0 — Authority / Safety

- Dashboard/Report vs Gate-Freigabe Verwechslung (Overview Risk Register).
- CI Scheduled Vars als readiness Proxy nutzen (Linkage Review).
- Fehlende kanonische „single narrative“ für recurring verification → Eskaliert Fehlinterpretation bei Autonomie-Roadmaps.

### P1 — Tests / Contracts

- Vollständige WebUI POST/gated Pfad Abdeckung (Overview §11).
- Erweiterte Charakterisierung vor Producer-Wiring (wenn je genehmigt).

### P2 — Docs / Owner / Discoverability

- Canonical Surface Clarification **TBD** im externen Owner-Roster.
- Große Spec-Menge — Navigation über `MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md` / Ladder erzwingen.

### P3 — Ergonomie

- Viele lokale Branches/Stashes (Overview §1) — organisatorisch.

### HOLD / Approval-only

| Thema | Bewertung |
|-------|-----------|
| Canonical 24/7 Paper surface | **Fehlt / nicht bestätigt** — verteilte Surfaces nutzen statt neue Daemon-Oberfläche zu erfinden. |
| Env/Owner canonical surface | **Partially assigned** (Frank Rauter Namen), **canonical verification surface unresolved** — Roster Tabelle. |
| Snapshot DTO v0 | **HOLD** — RUNTIME_NOT_WIRED; Truth Map Eintrag `DOCS_TRUTH_MAP.md`. |
| PaperExecutionEngine/Futures wiring | **HOLD** bis §7 Freigabe + Mark Price Discipline. |
| Master V2 runtime | **No-touch** ohne Governance. |
| Risk/KillSwitch/Live Gates | **No-touch** ohne Governance. |
| Evidence duplicate-risk | Scorecards/Pilot Workflows „review before parallel surface“. |
| Strategy/Learning Loop evidence | Inventory fordert konsolidierte Approval-State-Machine — **Reuse** Evidence Pack Template statt neue Surface. |

---

## 8. Best Next Moves

### Move 1 — Read-only autonomy roadmap consolidation (**dieses Artefakt**)

- **Nutzen:** gemeinsames Stage-Vokabular für Operator/Cursor Sessions.
- **Risiko:** minimal wenn nur `&#47;tmp` oder externes Wiki.
- **Typ:** read-only.
- **Dateien:** keine Repo — Basis `$BASE`; Referenzen auf Spec-Pfade oben.
- **No-Touch:** gesamtes Runtime `src&#47;execution`, Risk. <!-- pt:ref-target-ignore -->
- **Reuse Owner:** Ops/Docs Governance.
- **Jetzt:** sofort nutzbar; **Später:** einmal mit Repo-Doc Crosswalk mergen wenn STOP lifted.

### Move 2 — Docs-only autonomy ladder crosswalk in `MASTER_V2_GO_LIVE_ROADMAP_V0.md`

- **Nutzen:** Ein Pfad Doc für Stage ↔ bestehende Roadmap-Stufen.
- **Risiko:** Truth-Map Pflicht wenn substanzielle neue Claims zu Codepfaden — nur kurze Crosswalk-Tabelle minimieren.
- **Typ:** docs-only (nach Operator-Freigabe).
- **Dateien:** `docs&#47;ops&#47;specs&#47;MASTER_V2_GO_LIVE_ROADMAP_V0.md`; optional `DOCS_TRUTH_MAP.md`.
- **No-Touch:** Code.
- **Reuse Owner:** Peak_Trade Docs / Ops (bestehendes docs_token).
- **Jetzt:** blockiert wenn STOP/HOLD strikt; **Später:** nach canonical surface Klärung.

### Move 3 — Tests-only Paper/Shadow non-authority contract

- **Nutzen:** Regression für Readmodels/Observability (#3238 Linie fortsetzen).
- **Risiko:** Fixture/Drift wenn Paper-Artefakte berührt werden — nur `tests&#47;fixtures&#47;` reuse.
- **Typ:** tests-only.
- **Dateien:** `tests&#47;webui&#47;test_*`, Fixtures unter `tests&#47;fixtures&#47;`.
- **No-Touch:** Production Paper Daten.
- **Reuse Owner:** CI/WebUI Maintainer.
- **Jetzt:** wenn konkrete Contract-Lücke identifiziert; **Später:** ohne Gap nicht erweitern.

### Move 4 — Read-only 24/7 Paper owner-resolution

- **Nutzen:** entscheidet ob Observation verteilt bleibt oder ein Kanal gewählt wird.
- **Risiko:** falscher Kanal erzeugt operative Blindheit — Operator judgement.
- **Typ:** externes Roster read-only iteration.
- **Dateien:** externes MD — nicht Repo bis Option B aus Decision Pack.
- **No-Touch:** GH Vars Werte.
- **Reuse Owner:** Frank Rauter laut Working Copy (+ Backup gleich).
- **Jetzt:** **prioritär** vor Stage-2 Narrative Commit im Repo.

### Move 5 — Bounded pure-model Snapshot DTO v0 (approval-only slice)

- **Nutzen:** deterministische Hilfen für Offline Replay — bereits Code vorhanden.
- **Risiko:** hoch wenn als Runtime Promotion missbraucht — nur nach §7 Approval.
- **Typ:** Implementation — **nicht** ohne separates Approval Ticket.
- **Dateien:** `src&#47;execution&#47;paper&#47;futures_accounting.py`, Spec §7, Truth Map.
- **No-Touch:** bis Approval — gesamtes Wiring Thema.
- **Reuse Owner:** Execution Governance + Futures Contract Owner.
- **Später:** nach Scope/Mark Price Klärung.

### Move 6 — Strategy/Learning-loop evidence inventory drill-down

- **Nutzen:** schließt Lücken aus `MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md` ohne neue Surface — Mapping zu konkreten Tests.
- **Risiko:** Zeit — rein lesend.
- **Typ:** read-only follow-up memo.
- **Dateien:** Inventory + `tests&#47;` Crosswalk Matrix extern halten bis STOP lifted.
- **No-Touch:** Runtime.
- **Reuse Owner:** Governance AI autonomy docs owner.
- **Jetzt:** parallel möglich.

### Move 7 — CI/offline-suite autonomy gate inventory

- **Nutzen:** explizite Zuordnung scheduled workflow → Gate-artifact vs operational observability — bereits zu Teilen im Linkage Review — vertiefen für Stage 2 Klärung.
- **Risiko:** Missinterpretation wenn ohne Operator Kontext publiziert.
- **Typ:** read-only spreadsheet/Markdown extern.
- **Dateien:** `.github&#47;workflows&#47;offline_suites.yml`, `ci-scheduled-paper-and-export-smoke.yml`, Guardrail scripts.
- **No-Touch:** Workflow YAML ohne Approval unnötig nicht ändern.
- **Reuse Owner:** CI Ops.
- **Jetzt:** unterstützt Move 4.

---

## 9. Recommended Best Next Step

**Genau eine Empfehlung:** Operator schließt zuerst die **„Canonical Surface Clarification“**-Zeilen im externen Owner-Roster (welche Oberfläche für recurring verification maßgeblich ist; ob P77 operativ; ob später Repo docs-only Cross-Link) und legt eine **operative Deckungsgrenze** fest (**empfohlen: operative Planung initial nur Stage 0–2 Narrativ ohne neue Daemon-Oberfläche**). **Keine Repo-Mutation und keine Runtime-Arbeit**, bis diese Klärung und ein explizites **STOP/HOLD-Lifting** für einen kleinen docs-only oder tests-only Slice vorliegt — danach erst optional **Move 2** (ein Abschnitt Crosswalk in `MASTER_V2_GO_LIVE_ROADMAP_V0.md`) oder **Move 3** bei nachgewiesener Contract-Lücke.

---

## 10. Operator Decision Required

- **Target Stage für nächsten Planungszyklus:** empfohlen **≤ Stage 2** bis kanonisches Observation-Modell geklärt ist.
- **Roadmap/Docs:** ja/no — wenn ja, nur bestehende Spec (`GO_LIVE_ROADMAP`) nach STOP-Lifting.
- **Tests-only:** nur bei konkret benannter Lücke (Decision Pack Option C Logik).
- **Paper/Shadow owner-resolution:** **ja — Pflicht** vor Autonomie-Messaging im Repo (Canonical Surface TBD).
- **Snapshot DTO Wiring Approval:** separater expliziter Beschluss — Standard **nein**.
- **STOP/HOLD:** bleibt Default für Implementierung bis Freigabe — konsistent mit `FINAL_SESSION_HANDOFF.md` und Owner-Roster Operator Assignment Record.

---

## 11. Exact Next Prompt If Approved

**Wenn Operator STOP für einen docs-only Slice hebt und Canonical Surface geklärt ist:**

> „Arbeite auf `main`. Änderung nur an `docs&#47;ops&#47;specs&#47;MASTER_V2_GO_LIVE_ROADMAP_V0.md`: füge einen kurzen nicht-autorisierenden Abschnitt **‚Autonomy stage crosswalk (informative only)‘** hinzu: Tabelle Stage 0–7 ↔ bestehende Abschnitte dieser Datei ↔ Zeiger auf `MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md` und `MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md`. Keine neuen Evidence-/Registry-Surfaces; `DOCS_TRUTH_MAP.yaml` nur ergänzen wenn Truth-Map Policy einen neuen Token fordert; sonst nur Markdown. Keine Code-/Workflow-/Secret-Änderungen.“

**Wenn weiter STOP:**

> „Erzeuge nur externes Markdown unter `&#47;tmp&#47;` mit CI/offline-suite Zuordnung zu Observation vs Promotion (Move 7), ohne Repo-Touch.“

---

## 12. STOP Conditions

Implementierung oder Repo-Doku die Folgendes bricht oder impliziert:

- neue parallele Evidence/Readiness/Report/Registry/Handoff Surface ohne Owner
- Runtime-Umbau Master V2 / Double Play / Scope-Capital
- Risk/KillSwitch/Live Gate Semantik ändern
- PaperExecutionEngine oder Shadow/Paper Runner Futures wiring ohne Approval
- Exchange/Provider/Secrets/Testnet/Live Orders aus Repo Prompt heraus
- Paper-Testdaten zerstören/korrumpieren
- benannten **24/7 Paper-Test-Daemon** kanonisieren ohne Architekturentscheid
- Snapshot DTO v0 ohne explizite Approval-Kette promoten

---

## 13. Copy-Paste Handoff

```
Peak_Trade Master V2 Autonomy Roadmap — READ ONLY — 2026-05-02

HEAD: a81492155e28 (main clean)

Summary:
- Inventory: 108 MASTER_V2*.md under docs/; master_v2 code 22 modules; tests 16 files; 73 workflows.
- No canonical named 24/7 Paper daemon confirmed — observation distributed (offline_suites, class-a probe, paper audits, optional P77 script/docs).
- Snapshot DTO v0 exists pure/offline RUNTIME_NOT_WIRED — HOLD wiring (MASTER_V2_FUTURES_CLASS_A_CAPABILITY_CONTRACT_V0.md §7; futures_accounting.py).
- External owner roster: names assigned (Frank Rauter) but Canonical Surface Clarification still TBD — resolve BEFORE repo autonomy messaging.
- Recommended single next step: operator completes roster clarification rows + caps planning at Stage≤2 narrative; HOLD repo mutations until explicit slice approval.

Authority reminders:
Signal≠Trade; Dashboard≠approval; Paper≠Live; Testnet≠Live; Learning improves candidates, cannot bypass gates (MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md).

Artifacts:
- Full: MASTER_V2_AUTONOMY_ROADMAP_READONLY.md (same folder as this export path provided by operator).
- Short: MASTER_V2_AUTONOMY_ROADMAP_SHORT.md

STOP: no parallel surfaces; no execution/risk/killswitch/gate edits without governance.
```
