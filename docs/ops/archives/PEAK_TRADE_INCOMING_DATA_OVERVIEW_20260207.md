# Peak_Trade — Incoming Data & Egress / Governance Overview (2026-02-07)

> Zweck: Konsolidierte, audit-taugliche Übersicht über **alle relevanten Incoming-Datenpfade**, **Egress-Pfade**, **Sensitive Data (Health/Psych)**, **Risk/Strategy Learning Surface**, sowie die **umgesetzte Härtung** (Orchestrator No-Bypass + Outbound Redaction) inkl. Merge-Evidence.

---

## 0) Executive Summary

### Was wir erreicht haben
- **InfoStream “No Commit”** ist evidenzbasiert erklärt und als Evidence-Pack abgelegt (**SUCCESS_NOOP**: kein Commit, weil keine Änderungen entstehen).
- **Data-Egress-Audit** erstellt (Workflows, Code, Telemetrie, Secrets→Logs) inkl. Domain-Ranking + Fundstellen.
- **Sensitive-Data-Lens (Health/Psych)** ergänzt, dann **de-noised** → **Runtime Hi-Confidence** und **Top-30 True-Risk**.
- **Remediation-Pack** erstellt (Buckets, Guardrails pro Datei, Patch-Templates, Apply-Readiness, Secret-Print-Lint Regeln).
- **Orchestrator-Audit** durchgeführt: Routing vorhanden, aber **Bypass** erkannt.
- **No-Bypass** konzipiert und **tatsächlich umgesetzt**: direkte LLM-Calls außerhalb `src/ai_orchestration/**` entfernt; Orchestrator/ModelClient ist jetzt **Single Egress Boundary**.
- **Risk/Strategy “Max Info lokal, minimal safe outbound”** als Policy + Hotspots + CI-Regeln dokumentiert.
- Änderung ist **gemerged** (PR **#1205** → Merge-Commit **3492f35e…**) und **Merge-Evidence** unter `out/ops/` persistiert.

### Kernprinzip (Design Target)
- **Maximale Detailtiefe lokal** (Evidence, Debug, Repro) unter `out/ops/`.
- **Minimaler, sicherer Outbound**: vor jedem externen Sink (LLM/Webhook/Telemetry) wird ein **redacted envelope** mit Allowlist-Fields verwendet.
- **Single Ingestion / Single Egress** über den Orchestrator + `model_client` — keine Bypässe (CI enforced).

---

## 1) Artifact Index (Entry Points)

### 1.1 InfoStream “No Commit” Evidence Set
**Index / Einstieg**
- `out/ops/INFOSTREAM_EVIDENCE_INDEX_20260207.md`

**Packs / Integrity**
- `out/ops/INFOSTREAM_EVIDENCE_PACK_20260207.tgz` + `.sha256`
- `out/ops/INFOSTREAM_EVIDENCE_PACK_20260207.zip` + `.sha256`
- `out/ops/INFOSTREAM_EVIDENCE_INTEGRITY_VERIFY_20260207.txt`
- `out/ops/INFOSTREAM_EVIDENCE_MANIFEST_20260207.txt`

**Close-out / Verify**
- `out/ops/infostream_audit_verify.sh`
- `out/ops/INFOSTREAM_AUDIT_DONE_20260207.txt`
- `out/ops/INFOSTREAM_AUDIT_TAG_ARCHIVE_20260207.tgz` + `.sha256`
- `out/ops/INFOSTREAM_AUDIT_TAG_ARCHIVE_REPORT_20260207.txt`
- `out/ops/INFOSTREAM_AUDIT_TAG_ARCHIVE_20260207.tgz.sha256`
- `out/ops/INFOSTREAM_AUDIT_VERIFY_RUN_SAMPLE_20260207.txt`

### 1.2 Data-Egress Audit (Workflows / Code / Telemetry / Secrets)
- `out/ops/DATA_EGRESS_AUDIT_REPORT_20260207.md`
- `out/ops/DATA_EGRESS_AUDIT_ACTIONS_INVENTORY_20260207.txt`
- `out/ops/DATA_EGRESS_AUDIT_WORKFLOW_EGRESS_20260207.txt`
- `out/ops/DATA_EGRESS_AUDIT_CODE_EGRESS_20260207.txt`
- `out/ops/DATA_EGRESS_AUDIT_TELEMETRY_20260207.txt`
- `out/ops/DATA_EGRESS_AUDIT_SECRETS_RISK_20260207.txt`

**Domains + Where**
- `out/ops/DATA_EGRESS_DOMAINS_TOP_20260207.txt`
- `out/ops/DATA_EGRESS_DOMAINS_WHERE_20260207.txt`

**Candidates**
- `out/ops/DATA_EGRESS_AI_EGRESS_CANDIDATES_20260207.txt`
- `out/ops/DATA_EGRESS_TELEMETRY_EGRESS_CANDIDATES_20260207.txt`
- `out/ops/DATA_EGRESS_SECRETS_TO_LOGS_CANDIDATES_20260207.txt`

### 1.3 Sensitive Data (Health/Psych) Lens + De-noise
**Lens / Candidates**
- `out/ops/DATA_EGRESS_SENSITIVE_HEALTH_PSYCH_KEYWORDS_20260207.txt`
- `out/ops/DATA_EGRESS_SENSITIVE_HEALTH_PSYCH_CANDIDATES_20260207.txt`
- `out/ops/DATA_EGRESS_SENSITIVE_HEALTH_PSYCH_ENDPOINTS_20260207.txt`
- `out/ops/DATA_EGRESS_SENSITIVE_HEALTH_PSYCH_RISK_MAP_20260207.md`

**De-noised Runtime**
- `out/ops/SENSITIVE_RUNTIME_HICONF_SHORTLIST_20260207.txt`
- `out/ops/SENSITIVE_RUNTIME_HICONF_CONTEXT_20260207.txt`
- `out/ops/SENSITIVE_WORKFLOWS_HICONF_SHORTLIST_20260207.txt`

**True-Risk Ranking**
- `out/ops/SENSITIVE_RUNTIME_SCORING_RULES_20260207.md`
- `out/ops/SENSITIVE_RUNTIME_TOP30_TRUE_RISK_20260207.txt`

### 1.4 Remediation Pack (Sensitive Runtime)
- `out/ops/SENSITIVE_RUNTIME_TOP30_BUCKETS_20260207.md`
- `out/ops/SENSITIVE_RUNTIME_TOP30_FILE_GUARDRAILS_20260207.md`
- `out/ops/SENSITIVE_RUNTIME_TOP3_PATCH_TEMPLATES_20260207.diff`
- `out/ops/PATCH_TEMPLATE_APPLY_READINESS_20260207.txt`
- `out/ops/SECRET_PRINT_LINT_RULES_20260207.txt`
- `out/ops/REMEDIATION_INDEX_SENSITIVE_RUNTIME_20260207.md`
- `out/ops/REMEDIATION_DONE_HANDOFF_20260207.txt`

### 1.5 AI Training Data / Provider-Egress (repo-grounded)
- `out/ops/AI_TRAINING_DATA_CURRENT_STATE_20260207.md`
- `out/ops/AI_EGRESS_CALL_SITES_20260207.txt`
- `out/ops/AI_EGRESS_PAYLOAD_HINTS_20260207.txt`

### 1.6 AI Layers / Orchestrator Audits
**AI Layers**
- `out/ops/AI_LAYERS_INVENTORY_20260207.md`
- `out/ops/AI_LAYERS_ENTRYPOINTS_20260207.txt`
- `out/ops/AI_LAYERS_INPUT_CHANNELS_20260207.txt`
- `out/ops/AI_LAYERS_EXTERNAL_EGRESS_20260207.txt`
- `out/ops/AI_LAYERS_DATA_FLOW_MAP_20260207.md`

**Orchestrator**
- `out/ops/ORCH_DATA_ARRIVAL_POINTS_20260207.txt`
- `out/ops/ORCH_ROUTING_CALLGRAPH_20260207.txt`
- `out/ops/ORCH_LAYER_CONTRACTS_20260207.md`
- `out/ops/ORCH_BYPASS_PATHS_20260207.txt`
- `out/ops/ORCH_GAPS_ASSERTIONS_20260207.md`

**No-Bypass Enforcement Plan (pre-implementation)**
- `out/ops/ORCH_BYPASS_CLASSIFICATION_20260207.txt`
- `out/ops/ORCH_NO_BYPASS_PLAN_20260207.md`
- `out/ops/ORCH_BYPASS_PATCH_TEMPLATES_20260207.diff`
- `out/ops/ORCH_NO_BYPASS_CI_LINT_RULES_20260207.txt`
- `out/ops/ORCH_NO_BYPASS_HANDOFF_20260207.txt`

### 1.7 Risk/Strategy “Max Info lokal, minimal safe outbound”
- `out/ops/RISK_STRAT_KEYWORDS_20260207.txt`
- `out/ops/RISK_STRAT_LEARNING_SURFACE_CANDIDATES_20260207.txt`
- `out/ops/RISK_STRAT_LEARNING_SURFACE_TOP50_20260207.txt`
- `out/ops/RISK_STRAT_LEARNING_SURFACE_MAP_20260207.md`
- `out/ops/RISK_STRAT_REDACTION_POLICY_20260207.md`
- `out/ops/RISK_STRAT_EGRESS_GUARD_PATCH_TEMPLATES_20260207.diff`
- `out/ops/RISK_STRAT_NO_LEAK_CI_LINT_RULES_20260207.txt`

### 1.8 Implementation + Merge Evidence
**PR**
- PR: `#1205` — “security: enforce orchestrator no-bypass + outbound redaction guardrails”
- Branch (deleted): `security/orch-no-bypass-and-redaction-20260207`

**Merge Evidence (persisted)**
- `out/ops/ORCH_NO_BYPASS_MERGE_EVIDENCE_20260207.txt`
- `out/ops/ORCH_NO_BYPASS_MERGE_HEAD_20260207.txt`
- `out/ops/ORCH_NO_BYPASS_MERGE_LOG1_20260207.txt`

---

## 2) Incoming Data: Was “kommt rein” (Systematic View)

Die folgenden Kanäle sind die **relevanten Eintrittspunkte** für Daten in das AI-/Governance-System (Orchestrator + Layer):

### 2.1 CLI / Runner Entrypoints
- `--transcript` / Fixtures / replay-basierte Inputs
- Runner-Entrypoints für **L1/L2/L4** (und InfoStream-Module)
- Dry-run / gating flags (z. B. `DRY_RUN`, `ORCHESTRATOR_ENABLED`, `SKIP_AI`, confirm/armed/enabled)

**Evidence:** `out/ops/AI_LAYERS_INPUT_CHANNELS_20260207.txt`, `out/ops/ORCH_DATA_ARRIVAL_POINTS_20260207.txt`

### 2.2 Environment / Secrets (Control Plane)
- API Keys: `OPENAI_API_KEY` (und potenziell Anthropic-Configs/Paths)
- GitHub: `GITHUB_TOKEN` u. ä.
- Debug flags (ACTIONS/GIT_TRACE) als Leak-Risiko (durch Governance-Test abgedeckt)

**Evidence:** `out/ops/DATA_EGRESS_AUDIT_SECRETS_RISK_20260207.txt`, Governance tests

### 2.3 Config / Capability Scopes / Registry (Policy & Routing Inputs)
- `config/capability_scopes/*.toml` (Layer-Grenzen, erlaubte Fähigkeiten/Autonomie-Level)
- Model/Adapter Registry / select_model
- Routing-Logik: `scope_loader.load(layer_id)` etc.

**Evidence:** `out/ops/AI_LAYERS_DATA_FLOW_MAP_20260207.md`, `out/ops/ORCH_ROUTING_CALLGRAPH_20260207.txt`

### 2.4 File-based Inputs (Evidence, Reports, Learnings, Docs)
- `out/ops/` Evidence-Packs (lokal, auditierbar)
- potenziell `reports/**`, `docs/**`, `mindmap/**`, Learnings Logs
- Replay/Transcripts (können in LLM-Kontext wandern, wenn nicht gated/redacted)

**Evidence:** `out/ops/AI_EGRESS_PAYLOAD_HINTS_20260207.txt`, Sensitive/Risk-Strategy Maps

### 2.5 Runtime Data Objects (Risk/Strategy Surface)
Risk- und Strategie-relevante Daten, die als Kontext in L1–L4/InfoStream landen können:
- Metriken: Sharpe/MaxDD/PF/Vol, exposures, gate outcomes
- Trades/Orders/Positions (raw) — **hoch sensibel**
- Backtest / Walk-Forward / Monte-Carlo Ergebnisse (teils sensibel; roh nicht outbound)

**Evidence:** `out/ops/RISK_STRAT_LEARNING_SURFACE_MAP_20260207.md`, `out/ops/RISK_STRAT_REDACTION_POLICY_20260207.md`

---

## 3) Outgoing / Egress: Wo Daten “raus” können

### 3.1 LLM Egress (Processing vs. Training)
**Repo-sicher belegt:** LLM-Egress existiert (mind. OpenAI).  
**Nicht repo-belegbar:** ob Provider die Daten als “Training/Lernen” nutzt (Provider-/Account-Settings).

**Belegte Payload-Nähe:** `messages`, `transcript`, prompt/context, learnings/summaries.  
**Evidence:** `out/ops/AI_TRAINING_DATA_CURRENT_STATE_20260207.md`, `out/ops/AI_EGRESS_CALL_SITES_20260207.txt`, `out/ops/AI_EGRESS_PAYLOAD_HINTS_20260207.txt`

### 3.2 Webhooks / Escalation (PagerDuty / Slack)
- Domains: `events.pagerduty.com`, `hooks.slack.com` (viele Vorkommen, teils Docs/Config)
- Risiko: payload-leaks, wenn raw risk/strategy content versendet wird.
- Mitigation: reason codes + hashes, allowlist + opt-in gate.

**Evidence:** `out/ops/DATA_EGRESS_DOMAINS_TOP_20260207.txt`, `out/ops/DATA_EGRESS_DOMAINS_WHERE_20260207.txt`, Remediation docs

### 3.3 Telemetry (OpenTelemetry/OTLP etc.)
- Kandidaten: otlp/collector/remote_write
- Risiko: Attribute können PII/Secrets/Risk-Details tragen, wenn nicht gescrubbt.
- Mitigation: attribute scrubbing + local-only default + explicit opt-in for remote exporters.

**Evidence:** `out/ops/DATA_EGRESS_TELEMETRY_EGRESS_CANDIDATES_20260207.txt`, Sensitive runtime Top-30

### 3.4 GitHub Artifacts / Logs
- Risk: leakage in logs via echo/print/debug flags
- Mitigation: secret-print governance test + lint rules; evidence in out/ops only (controlled).

**Evidence:** `out/ops/DATA_EGRESS_SECRETS_TO_LOGS_CANDIDATES_20260207.txt`, governance tests

---

## 4) Sensitive Data (Health/Psych) — Approach & Result

### 4.1 Why this mattered
- Health/Psych ist “High-risk sensitive” und kann in free-text (transcripts, notes, summaries) auftreten.
- Ziel war: **finden → triagieren → de-noise → echte Risiken priorisieren**.

### 4.2 Result
- Große Kandidatenliste wegen generischer Begriffe; deshalb:
  - Runtime-only Filter (`src/` + `scripts/`)
  - Hi-Confidence Scoring
  - Top-30 “True Risk” Ranking

**Artifacts:** siehe Section 1.3 und 1.4 (Sensitive Lens + Remediation Pack)

---

## 5) Orchestrator: Architektur, Gaps, Fix

### 5.1 Erwartung (Target)
- Alle Daten sollen am Orchestrator ankommen.
- Orchestrator sortiert/normalisiert und routet zu L1/L2/L4/InfoStream.
- Egress (LLM/Webhook/Telemetry) passiert an einer Stelle mit Gates + Redaction.

### 5.2 Feststellung (Audit)
- Routing vorhanden (Scopes/Registry, Route Selection, Adapter Dispatch)
- **Bypass** existierte (OpenAI direct in InfoStream & Market Sentinel).

**Evidence:** `out/ops/ORCH_BYPASS_PATHS_20260207.txt`

### 5.3 Umsetzung (Merged)
- Direkte LLM-Aufrufe außerhalb `src/ai_orchestration/**` entfernt.
- InfoStream + Market Sentinel nutzen `create_model_client("live")` + `ModelRequest/complete()`.
- `model_client.py`: `redact_outbound_envelope()` ergänzt; Kommentar “Single egress boundary”.
- Governance Tests verhindern Regression:
  - `test_no_llm_bypass.py`
  - `test_no_secret_prints.py`
- PR #1205 gemerged; Merge Evidence gespeichert.

**Merge Evidence:** `out/ops/ORCH_NO_BYPASS_MERGE_*_20260207.*`

---

## 6) Risk/Strategy: “Max Info lokal, minimal safe outbound” (Operational Contract)

### 6.1 Was lokal bleiben soll (Max Info)
- Full-fidelity Evidence: raw trades/orders/positions, detailed backtests, traces, configs
- Speicherung ausschließlich kontrolliert (empfohlen `out/ops/`), mit SHA/Manifest/Integrity

### 6.2 Was outbound ok ist (Minimal Safe)
- Run metadata (`run_id`, hashes)
- Aggregierte Performance / Risk summary
- Gate status + reason codes
- Strategy label + parameter hashes (nicht raw)

**Policy:** `out/ops/RISK_STRAT_REDACTION_POLICY_20260207.md`

### 6.3 Hotspots (Top-50)
- LLM: `model_client.py`, `v0_daily_outlook.py`, `run_cycle.py`
- Webhook: PagerDuty/Slack (mehrheitlich Config/Docs/Tests)
- Telemetry: OTLP/Collector (auch evidence generator)
- Persistence: jsonl/csv Stellen

**Map:** `out/ops/RISK_STRAT_LEARNING_SURFACE_MAP_20260207.md`

---

## 7) InfoStream “No Commit” — Root Cause & Hardening

### 7.1 Root Cause
- Runs sind **SUCCESS_NOOP**: keine Änderungen → kein Commit.
- Gründe: kein neuer Report / missing inputs / `--skip-ai` / leere API keys → keine writes in Learnings/Reports.

### 7.2 Hardening (Template)
- Workflow “Commit changes” sichtbarer machen (git status/diff stat, commit errors nicht swallow)
- NOOP explicit log line

**Evidence:** `out/ops/EVIDENCE_INFOSTREAM_NO_COMMIT_20260207*.md` + patch notes

---

## 8) Current Status (as of merge)
- `main` ist sauber (`main...origin/main`).
- PR #1205 ist gemerged: Commit `3492f35e...`.
- Branch ist lokal & remote entfernt.
- Merge-Evidence liegt unter `out/ops/`.

---

## 9) Suggested Next Steps (Optional)
1) **Provider-Settings auditieren** (OpenAI/Anthropic Data usage / training opt-in/out) — außerhalb Repo.
2) `redact_outbound_envelope()` finalisieren: stabile allowlist + deterministic hashing + unit tests.
3) CI: zusätzliche “no-leak near sinks” Checks (risk/strategy denylist near LLM/webhook/telemetry calls).
4) Evidence retention policy (TTL/rotation) für `out/ops` definieren.

---

## 10) Download / Usage
Dieses Dokument ist als Markdown-Datei generiert und kann direkt in PRs/Runbooks/Evidence-Packs referenziert werden.
