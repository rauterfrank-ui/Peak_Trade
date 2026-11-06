# Peak_Trade — Status-Übersicht & Implementierungsliste


<!-- STATUS_OVERVIEW role note -->
> Role note: Use `docs&#47;ops&#47;STATUS_OVERVIEW_2026-02-19.md` for dated narrative context and operator orientation at that point in time.
> For the compact cross-topic status map, current navigation, and quick lookup, read `docs&#47;ops&#47;STATUS_MATRIX.md`.

**Scope:** Aktueller Projektstatus, Runbook-Landschaft, Implementierungsliste; operativer Snapshot. Für Status-Contract/Evidence-Level siehe [STATUS_MATRIX.md](STATUS_MATRIX.md).

**Stand:** 2026-02-19  
**Zweck:** Aktueller Projektstatus, Runbook-Landschaft, Workflows und konsolidierte Liste offener Implementierungen.  
**Letzte Registry-Downloads:** 2026-02-19 (Phase L, M, Policy Telemetry Real — `out&#47;ops&#47;gh_runs&#47;`)

---

## 0. Registry-Daten (Download-Status)

Die Ops-Registry-Pointer verweisen auf CI-Artefakte. Zum erneuten Herunterladen:

```bash
# Policy Telemetry (Real) — aktuellster Audit-Milestone
scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_POLICY_TELEMETRY_REAL.pointer --download

# Phase L + M Smoke (einzeln)
scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_L_SMOKE.pointer --download
scripts/ops/verify_from_registry.sh docs/ops/registry/LATEST_PHASE_M_SMOKE.pointer --download
```

**Hinweis:** Bei „file exists“-Fehlern zuerst `out&#47;ops&#47;gh_runs&#47;<run_id>` entfernen, dann erneut ausführen.

**Zuletzt heruntergeladen (2026-02-19):**
- Phase L: `out&#47;ops&#47;gh_runs&#47;22156204892` (3× telemetry_summary.json validiert)
- Phase M &#47; Policy Telemetry Real: `out&#47;ops&#47;gh_runs&#47;22156880821` (3× telemetry_summary.json validiert)

---

## 1. Aktueller Projektstatus (Kurzfassung)

| Bereich | Status | Anmerkung |
|---------|--------|-----------|
| **Phase (AI Autonomy)** | P4B abgeschlossen, P4C nächster | L1&#47;L4 operational; L2 Market Outlook Integration geplant |
| **Operating Mode** | Governance-Locked &#47; NO-LIVE | L6 Execution FORBIDDEN |
| **CI Health** | ✅ 9 Required Checks Active | Docs Gates, Policy Critic, Evidence Pack Validator |
| **Evidence Infrastructure** | ✅ Templates, Schema, Validator, Index | Operational |
| **Runner Readiness** | 1 READY, 6 PARTIAL, 6 TODO | Siehe `docs&#47;dev&#47;RUNNER_INDEX.md` |

---

## 2. Runbook-Landschaft

### 2.1 AI Online-Readiness Runbooks (docs&#47;ops&#47;ai&#47;) — 13 Runbooks — Detaillierter Implementierungsstatus

| Runbook | Phase | Zweck | Implementierung | Code-Pfad &#47; Script |
|---------|-------|-------|-----------------|--------------------|
| `online_readiness_runbook_v1.md` | P61 | Online Readiness Definition | ✅ Implementiert | `src.ops.p61.run_online_readiness_v1` |
| `online_readiness_operator_runbook_v1.md` | P66 | Operator Entrypoint (single-shot + loop) | ✅ Implementiert | `src.ops.p66.run_online_readiness_operator_entrypoint_v1` |
| `online_readiness_shadow_runner_runbook_v1.md` | P63 | Shadow Runner (P61 + P62 kombiniert) | ✅ Implementiert | `src.ops.p63.run_online_readiness_shadow_runner_v1` |
| `online_readiness_supervisor_service_runbook_v1.md` | P82&#47;P84 | Supervisor Service (launchd&#47;systemd) | ✅ Implementiert | `scripts&#47;ops&#47;online_readiness_supervisor_v1.sh`, `docs&#47;ops&#47;services&#47;` |
| `online_readiness_supervisor_health_gate_runbook_v1.md` | P79 | Supervisor Health Gate (ticks, pidfile, P76 artifacts) | ✅ Implementiert | `scripts&#47;ops&#47;p79_supervisor_health_gate_v1.sh` |
| `online_readiness_health_gate_runbook_v1.md` | P71 | Health Gate (P71) | ✅ Implementiert | `scripts&#47;ops&#47;p71_health_gate_v1.sh`, `src.ops.p71` |
| `online_readiness_go_no_go_runbook_v1.md` | P76 | Go&#47;No-Go (READY&#47;NOT_READY, exit codes) | ✅ Implementiert | `scripts&#47;ops&#47;online_readiness_go_no_go_v1.sh` |
| `shadow_loop_runbook_v1.md` | P62–P67 | Shadow Loop (Scheduler) | ✅ Implementiert | `src.ops.p67.shadow_session_scheduler_cli_v1` |
| `shadowloop_pack_runbook_v1.md` | P72 | Shadow Loop Pack (P71 + P68) | ✅ Implementiert | `scripts&#47;ops&#47;p72_shadowloop_pack_v1.sh`, `src.ops.p72` |
| `switch_layer_paper_shadow_runbook_v1.md` | P57 | Switch-Layer Paper&#47;Shadow | ✅ Implementiert | `src.ops.p57.switch_layer_paper_shadow_v1` |
| `live_data_ingest_readiness_runbook_v1.md` | P85 | Live Data Ingest Readiness | ✅ Implementiert | `scripts&#47;ops&#47;p85_live_data_ingest_readiness_v1.sh`, `src.ops.p85` |
| `ai_model_enablement_runbook_v1.md` | P50 | AI Model Enablement (enable&#47;arm&#47;token) | ✅ Implementiert | `src.ops.p50.ai_model_policy_cli_v1` |
| `ai_guardrails_runbook_v1.md` | P49&#47;P50 | AI Guardrails (deny-by-default) | ✅ Implementiert | `src.ops.p50.ai_model_policy_cli_v1` (P49 Hard Gate, P50 Policy) |

**Fazit:** Alle 13 AI-Runbooks in `docs&#47;ops&#47;ai&#47;` haben eine vollständige Code-Basis. Die Pipeline P57→P61→P62→P63→P64→P65→P66→P67 sowie P71, P72, P76, P79, P85, P50 sind implementiert und getestet.

### 2.2 Haupt-Runbook-Index (docs&#47;ops&#47;runbooks&#47;README.md)

- **Letzte Aktualisierung:** 2026-01-18
- **Kategorien:** Tech Debt, Docs Gates, AI Autonomy, Phase-Specific, Execution Gates (B), CI & Ops, Incident Response
- **~108+ Runbook-Dateien** im Repo (inkl. Subordner)

### 2.3 Zentrale Runbooks für „Finish“

- `RUNBOOK_AI_AUTONOMY_BIS_FINISH_2026.md` — Master-Roadmap P4B → P13
- `RUNBOOK_TO_FINISH_MASTER.md` — Docs-only Branch → PR → DoD
- `RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md` — Offene Features (Blöcke A–J)

---

## 3. Workflows (GitHub Actions)

| Workflow | Zweck | Status |
|----------|-------|--------|
| `ci.yml` | Main CI (PR gate, fast-lane) | ✅ |
| `aiops-trend-seed-from-normalized-report.yml` | Phase 5A Trend Seed | ✅ |
| `aiops-trend-ledger-from-seed.yml` | Phase 5B Trend Ledger | ✅ |
| `docs_reference_targets_gate.yml` | Docs Reference Targets | ✅ |
| `docs-token-policy-gate.yml` | Docs Token Policy | ✅ |
| `docs_diff_guard_policy_gate.yml` | Docs Diff Guard | ✅ |
| `l4_critic_replay_determinism*.yml` | L4 Critic Determinism | ✅ |
| `paper_session_audit_evidence.yml` | Paper Session Audit | ✅ |
| `evidence_pack_gate.yml` | Evidence Pack Validation | ✅ |
| `shadow_paper_smoke.yml` | Shadow + Paper Smoke | ✅ |

---

## 4. Implementierungsliste — Was noch offen ist

### 4.1 AI Autonomy Phasen (RUNBOOK_AI_AUTONOMY_BIS_FINISH_2026)

| Phase | Thema | Offene Punkte |
|-------|-------|---------------|
| **P4C** | L2 Market Outlook | L2 Runner existiert; Regime-Szenarien + NO-TRADE-Trigger dokumentieren; Evidence Pack Fixtures; Tests |
| **P5A** | L3 Trade Plan Advisory | L3 Runner existiert (PARTIAL); L3 Evidence Pack Fixtures; Capability Scope; L3 Operator Cheatsheet; L3→L5 Handoff |
| **P5B** | Evidence Pack Automation | `generate_evidence_pack.py` existiert; CI-Integration; Evidence Index Auto-Update; Operator Cheatsheet |
| **P6** | Shadow Mode Stability | `run_shadow_session.py` existiert; Inputs&#47;Outputs + Schema bestätigen; Scaffolding + Tests; >=3 Sessions ohne Regression |
| **P7** | Paper Trading | Reconciliation ✅; Paper Simulator Core (fills + slippage + fees) fehlt; Integration in Shadow Pipeline |
| **P8** | Governance Approval | Governance Approval Checklist; Multi-Stakeholder Sign-Off Prozess |
| **P9** | Kill-Switch Drills | Kill-Switch Drill Procedure; Incident Response Playbook; >=3 Drills |
| **P10** | Testnet Bounded-Live | Testnet Environment; Bounded-Live Config; Session Runner |
| **P11** | Live Readiness Review | Live Readiness Checklist; Live Activation Playbook |
| **P12** | Bounded-Live Phase 1 | Live Activation (CRITICAL) |
| **P13** | Mature Operations | Weekly Health Discipline; Continuous Improvement |

### 4.2 Fehlende Features (RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES)

| Block | Slug | Status |
|-------|------|--------|
| A | sweep-pipeline-cli | ✅ erledigt |
| B | heatmap-template-2x2 | ✅ erledigt |
| C | vol-regime-universal-wrapper | ❌ offen |
| D | corr-matrix-param-metric | ❌ offen |
| E | rolling-window-stability | ❌ offen |
| F | sweep-comparison-tool | ❌ offen |
| G | metrics-ulcer-recovery | ✅ erledigt |
| H | nightly-sweep-automation | ❌ offen |
| I | feature-importance-wrapper | ❌ offen |
| J | feature-engine-skeleton | ❌ offen |

**Nächster logischer Schritt:** Block C (Vol-Regime Universal Wrapper).

### 4.3 Runner Readiness (RUNNER_INDEX)

| Runner | Readiness | P1 |
|--------|-----------|-----|
| run_backtest.py | ✅ READY | MUST |
| research_cli.py | 🟡 PARTIAL | MUST |
| live_ops.py | ❌ TODO | MUST |
| run_execution_session.py | 🟡 PARTIAL | SHOULD |
| run_l3_trade_plan_advisory.py | 🟡 PARTIAL | LATER |
| preview_live_portfolio.py | ❌ TODO | LATER |
| report_live_sessions.py | ❌ TODO | LATER |
| … | … | … |

**Top 3 P1:** research_cli.py, run_backtest.py, live_ops.py

### 4.4 AI-Runbooks (docs&#47;ops&#47;ai) — Verifizierung ✅ erledigt (2026-02-19)

- [x] Welche P6x-Module sind vollständig implementiert? → P57, P61–P67, P71, P72, P76, P79, P85, P50
- [x] Welche Runbooks haben noch keine Code-Basis? → Keine; alle 13 haben vollständige Implementierung
- [ ] Integration der AI-Runbooks in den Haupt-Runbook-Index (README.md) — optional

### 4.5 Evidence Pack CI

- [ ] **CI workflow blocks PRs with invalid Evidence Packs** — laut RUNBOOK_AI_AUTONOMY_BIS_FINISH noch als `[ ]` (nicht getestet)

### 4.6 Dokumentation

- [ ] Runbook-Index (README.md) aktualisieren — letzte Aktualisierung 2026-01-18
- [ ] AI-Runbooks (docs&#47;ops&#47;ai) in docs&#47;ops&#47;runbooks&#47;README.md verlinken

---

## 5. Priorisierte Nächste Schritte

1. **P4C abschließen:** L2 Regime-Szenarien + NO-TRADE-Trigger dokumentieren; Evidence Pack Fixtures; Tests
2. **P5A vorbereiten:** L3 Evidence Pack Fixtures; L3 Capability Scope; L3 Operator Cheatsheet
3. **P6 stabilisieren:** run_shadow_session.py Inputs&#47;Outputs bestätigen; >=3 Sessions ohne Regression
4. **Feature Block C:** Vol-Regime Universal Wrapper (RUNBOOK_CURSOR_MA)
5. **live_ops.py:** Evidence Chain integrieren (P1 MUST Runner)
6. ~~**AI-Runbooks:** 13 Runbooks durchgehen~~ → ✅ erledigt (siehe Abschnitt 2.1)

---

## 6. Referenzen

- `docs&#47;ops&#47;registry&#47;README.md` — Ops Registry (Pointer, Download, Verify)
- `docs&#47;FEHLENDE_FEATURES_PEAK_TRADE.md` — Fehlende Features (2026-02-10)
- `docs&#47;ops&#47;STATUS_MATRIX.md` — Status-Werte (planned, stub, configured, implemented, enforced)
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_AI_AUTONOMY_BIS_FINISH_2026.md` — Phasen-Roadmap
- `docs&#47;ops&#47;runbooks&#47;RUNBOOK_CURSOR_MA_FEHLENDE_FEATURES_OPEN_POINTS_2026-02-10.md` — Feature-Blöcke A–J
- `docs&#47;dev&#47;RUNNER_INDEX.md` — Runner Readiness
- `docs&#47;ops&#47;EVIDENCE_INDEX.md` — Evidence Pack Index
