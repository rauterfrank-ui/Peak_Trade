# Queue am effizientesten durchziehen

**Zweck:** Regeln für PR-Größe, Merge-Reihenfolge und Definition of Done, damit die Queue zügig und konsistent abgearbeitet werden kann.

---

## Regeln

### PR-Größe

- **200–500 LOC netto** pro PR
- **Maximal 1–2 Themen** pro PR

### Merge-Reihenfolge

1. **Docs/Contracts zuerst** → PR-01  
2. **Enforcement** → PR-02, PR-10  
3. **Providers/Telemetry** → PR-03, PR-04, PR-05  
4. **Data correctness** → PR-06, PR-07, PR-08, PR-09  

### Definition of Done pro PR

- **Grüne Tests** (CI grün)
- **Ein „Expected Artifacts“-Beispiel** in `docs/` oder `reports&#47;fixtures&#47;`

---

## PR-Queue (Platzhalter für konkrete PRs)

| PR   | Thema / Schwerpunkt      | Reihenfolge | Erwartete Pfade / Themen |
|------|--------------------------|-------------|---------------------------|
| PR-01 | Docs/Contracts           | 1           | Verträge, SSoT-Docs, erwartete Artefakte |
| PR-02 | Enforcement              | 2           | Validierung, Guards       |
| PR-10 | Enforcement (weitere)    | 2           | wie PR-02                 |
| PR-03 | Providers                | 3           | Adapter, Datenquellen     |
| PR-04 | Telemetry (Teil 1)      | 3           | Metriken, Logging         |
| PR-05 | Telemetry (Teil 2)      | 3           | Evals, Exporter           |
| PR-06 | Data correctness (1)   | 4           | Schema, Validierung       |
| PR-07 | Data correctness (2)   | 4           | Fixtures, Contracts       |
| PR-08 | Data correctness (3)   | 4           | Report-Compare, Index     |
| PR-09 | Data correctness (4)   | 4           | Regression, Golden       |

*(Inhalt von PR-01…PR-10 kann je nach Backlog angepasst werden.)*

### PR-Queue (DoD & Evidence)

| PR | Thema | Scope | DoD | Evidence |
|---|---|---|---|---|
| PR-01 | Status-Matrix + Evidence-Schema v1 + GATES-Overview konsolidieren | docs/ops + docs/ops/evidence | ✅ markdown konsistent, ✅ Claims nutzen status enums, ✅ Evidence pack example vorhanden | docs/ops/evidence/packs/PR-01/EV-2026-02-PR01-000.json |
| PR-02 | Kill Switch Enforcement + Audit JSONL + Unit-Tests | src/live + config/risk + tests/risk + docs/ops/evidence | ✅ pytest grün, ✅ hard block nachweisbar (E1), ✅ audit JSONL append-only | docs/ops/evidence/packs/PR-02/EV-2026-02-PR02-001.json <!-- pt:ref-target-ignore --> |
| PR-03 | Escalation Providers: Stub default + PagerDuty optional (envelopes) + Tests | src/infra/escalation + config + tests/infra + docs/ops/evidence | ✅ offline-safe default, ✅ provider selection tested, ✅ no secrets in artifacts | docs/ops/evidence/packs/PR-03/EV-2026-02-PR03-001.json <!-- pt:ref-target-ignore --> |
| PR-03b | PagerDuty HTTP Sender (guarded) + Tests | src/infra/escalation + config + tests/infra + docs/ops/evidence | ✅ allow_network gating, ✅ urlopen monkeypatched test, ✅ secrets never persisted | docs/ops/evidence/packs/PR-03b/EV-2026-02-PR03b-001.json |
| PR-04 | Event Schemas + Validator + Smoke Tests (+ optional CI) | schemas/events + scripts + tests/fixtures + tests/validation + docs/ops/evidence | ✅ fixtures valid, ✅ invalid fails, ✅ CLI validator works offline | docs/ops/evidence/packs/PR-04/EV-2026-02-PR04-001.json |
| PR-05 | Observability ports: metricsd vs session, fail-fast + PEAK_TRADE_METRICSD_PORT (+ canonical/legacy env, OBS_PORTS.md) | src/ops/net + src/obs + tests/ops + tests/obs + docs/ops + docs/ops/evidence + docs/webui/observability | ✅ metricsd/session cannot share port, ✅ startup fails with clear error, ✅ canonical/legacy env tested, ✅ OBS_PORTS contract doc | docs/ops/evidence/packs/PR-05/EV-2026-02-PR05-001.json |
| PR-06 | Stage1 deterministic artifacts: index.json contract + generator + tests + docs | src/obs/stage1 + scripts/obs + tests/obs + docs/ops | ✅ index.json sorted + sha256, ✅ no now() in content, ✅ optional generated_at, ✅ STAGE1_INDEX_CONTRACT.md | (Evidence pack PR-06 optional) |
| PR-06b | WebUI consumes Stage1 index.json | src/webui + templates + tests/webui + docs/ops/evidence | ✅ loader robust, ✅ UI table, ✅ fixture-based tests | docs/ops/evidence/packs/PR-06b/EV-2026-02-PR06b-001.json <!-- pt:ref-target-ignore --> |
| PR-07 | Stage1 index validator (sha256/bytes + required artifacts) | scripts/obs + tests/obs + tests/fixtures + docs/ops/evidence | ✅ good fixture passes, ✅ tampered fails, ✅ required artifacts enforced | docs/ops/evidence/packs/PR-07/EV-2026-02-PR07-001.json <!-- pt:ref-target-ignore --> |
| PR-08 | Stage1 runners produce validation.json (fail-fast) | scripts/obs + docs/ops/evidence (+ optional scripts/obs/README.md) | ✅ index+validation generated after runs, ✅ required artifacts enforced | docs/ops/evidence/packs/PR-08/EV-2026-02-PR08-001.json |
| PR-09 | Stage1 required artifacts + index&#47;validation scripts; require real outputs | scripts/obs + docs/ops/evidence | ✅ index+validation scripts tracked, ✅ required artifacts (snapshot&#47;summary&#47;trend) enforced, exit 2 on failure | docs/ops/evidence/packs/PR-09/EV-2026-02-PR09-001.json <!-- pt:ref-target-ignore --> |
| PR-10 | Gate outbound telemetry&#47;escalation behind live safety gates | src/infra/escalation + config + tests/infra + docs/ops | ✅ default config denies network escalation, ✅ gate stub + tests, ✅ plan doc | EV-2026-02-PR10-001 |

---

## Relevante Repo-Pfade (für konkrete Patches)

Damit pro PR konkrete Commit-Patches (Diff-Style: neue Files, Signaturen, Testnamen) formuliert werden können, hier die relevanten Verzeichnisse und Dateitypen.

### Docs / Contracts (PR-01)

- `docs/ops/` – Ops-Docs, Runbooks, Merge-Logs, Gates
- `docs/ai/`, `docs/execution/`, `docs/risk/`, `docs/governance/` – fachliche Verträge
- `docs/webui/observability/` – Observability-Contracts
- `.cursor/rules/`, `.github/` – Projekt- und CI-Contracts
- Typische Artefakte: `docs&#47;ops&#47;evidence&#47;`, `docs&#47;ops&#47;EVIDENCE_SCHEMA.md`, `docs&#47;ops&#47;GATES_*.md`

### Enforcement (PR-02, PR-10)

- `scripts/ops/` – Validatoren, Guards (z. B. `validate_workflow_dispatch_guards.py`, `check_merge_log_hygiene.py`, `validate_docs_token_policy.py`)
- `scripts/ci/` – CI-Validierung (`validate_required_checks_hygiene.py`, `guard_no_tracked_reports.sh`)
- `.github/workflows/` – Workflows als Enforcement (Gates)
- `src/governance/`, `src/live/safety.py`, `src/data/safety/` – Runtime-Enforcement

### Providers / Telemetry (PR-03, PR-04, PR-05)

- `src/data/providers/`, `src/data/feeds/` – Datenprovider
- `src/obs/` – Observability, OTel, metricsd (`src/obs/otel.py`, `src/obs/metricsd.py`)
- `scripts/obs/` – Exporter, Stage1, Grafana/Prometheus
- `src/notifications/`, `src/infra/escalation/` – Alerts, Eskalation
- `config/telemetry_alerting.toml`, `config/model_registry.toml` – Telemetrie-Config

### Data correctness (PR-06, PR-07, PR-08, PR-09)

- `src/risk/validation/` – VaR report_compare, report_index
- `tests/risk/validation/`, `tests/fixtures/var_suite_reports/` – VaR-Fixtures
- `src/execution/replay_pack/`, `src/ai_orchestration/` – Replay, Evidence Pack, Critic-Schema
- `tests/fixtures/evidence_packs/`, `tests/fixtures/transcripts/` – erwartete Artefakte
- `scripts&#47;risk&#47;var_suite_*.py`, `scripts&#47;aiops&#47;` – Report-Tools
- `reports&#47;` – nur über Artifacts/fixtures; typisch `reports&#47;fixtures&#47;` oder Beispiele unter `docs&#47;`/`tests&#47;fixtures&#47;`

### Expected Artifacts / Fixtures (DoD)

- `docs/ops/evidence/` – Evidence-Beispiele
- `tests/fixtures/` – JSON/Parquet/JSONL für Tests
- `reports&#47;fixtures&#47;` – falls genutzt; sonst Beispiele in `docs&#47;` (z. B. `docs&#47;ops&#47;...&#47;example_*.json`)

---

## Nächster Schritt: konkrete Patches

- **Repo ist lokal verfügbar:** `/Users/frnkhrz/Peak_Trade` (bzw. Projektroot).
- Wenn du pro PR konkrete **Commit-Patches (Diff-Style)** willst: entweder
  - **PR-Thema konkretisieren** (z. B. „PR-01 = nur docs/ops/GATES_OVERVIEW.md + EVIDENCE_SCHEMA Anpassung“), dann können neue Files, geänderte Signaturen und Testnamen 1:1 vorgeschlagen werden, oder
  - **Dateiliste pro PR** angeben (z. B. „PR-03: scripts/obs/ai_live_exporter.py, config/...“), dann können Diffs dazu formuliert werden.

Dieses Doc kannst du als Referenz nutzen, wenn du (oder jemand anderes) die Patches formuliert.
