# Peak_Trade – Game‑Changer Setup & Runbook (Cursor Multi‑Agent Orchestration)
Stand: 2026‑02‑02 (Europe/Berlin)  
Scope: **Cursor‑gestützte Multi‑Agent‑Orchestrierung** für Peak_Trade mit **Multi‑Provider‑LLMs (alles außer Anthropic/Claude)**, reproduzierbar, auditierbar, safety‑first.  
Ziel: *Eine operational belastbare Agenten‑Pipeline* (Research → Shadow → Testnet → Live‑gated) mit klaren **Einstiegspunkten/Endpunkten** je Phase, **hard fails** bei Policy‑Verstößen und **eindeutiger Model‑Matrix** je Layer (L0–L6).

---

## Inhaltsverzeichnis
1. [Design‑Prinzipien](#design-prinzipien)  
2. [Zielarchitektur](#zielarchitektur)  
3. [Agenten‑Rollen in Cursor](#agenten-rollen-in-cursor)  
4. [Model‑Policy: “No Anthropic/Claude”](#model-policy-no-anthropicclaude)  
5. [Phasen‑Runbook](#phasen-runbook)  
   - [Phase 0 – Bootstrap](#phase-0--bootstrap)  
   - [Phase 1 – Multi‑Agent Foundation](#phase-1--multi-agent-foundation)  
   - [Phase 2 – Model‑Matrix & Routing](#phase-2--model-matrix--routing)  
   - [Phase 3 – Evaluations & “Verified”](#phase-3--evaluations--verified)  
   - [Phase 4 – Shadow](#phase-4--shadow)  
   - [Phase 5 – Testnet](#phase-5--testnet)  
   - [Phase 6 – Live (Gated)](#phase-6--live-gated)  
6. [Incidents, Rollback, Forensics](#incidents-rollback-forensics)  
7. [Checklisten](#checklisten)  
8. [Appendix: Konfig‑Snippets](#appendix-konfig-snippets)

---

## Design‑Prinzipien
**Safety‑First / Governance‑First**
- **L5 (Risk Gate) deterministisch**, L6 Execution standardmäßig **verboten** / stark gegated.
- Jeder LLM‑Call ist **auditierbar**: Request‑Hash, model_id/provider, prompt‑version, tool‑events, outcome.

**Reproduzierbarkeit**
- Versionierte Configs (TOML/YAML), Experiment‑Registry, Evidence‑Packs.
- Keine “hidden” Model‑Switches: Model‑IDs und Provider kommen ausschließlich aus der **Layer‑Matrix**.

**Separation of Duties (SoD)**
- Primary erzeugt Plan/Output.
- Critic prüft (Policy, Halluzinationen, Risiko).
- Orchestrator entscheidet (Escalate / Retry / Abort) – deterministisch nachvollziehbar.

**Budget & Latency Control**
- “Cheap by default”: L0/L2 mit kleinen Modellen, L4 Critic nur bei Escalations.
- Explizite Token‑/Kosten‑Budgets je Phase.

---

## Zielarchitektur

### Layer‑Konzept (gegeben)
| Layer | Rolle | LLM erlaubt | Bemerkung |
|---|---|---:|---|
| L0 Ops/Docs | primary + critic | ✅ | Orchestrator + Capability Scopes |
| L1 Runner DeepResearch | primary + fallback + critic | ✅ | Evidence‑Packs, Quellen |
| L2 Runner Market Outlook | primary + fallback + critic | ✅ | strukturierte Analyse |
| L3 Trade Plan Advisory | primary + fallback + critic | ✅ | kein eigener Runner, via Orchestrator |
| L4 Policy Critic Service | primary + critic | ✅ | Governance‑Critic |
| L5 Risk Gate | — | ❌ | deterministisch |
| L6 Execution | — | ❌ | verboten / gated |

### Game‑Changer: “Routing + Policy Gate” als **zentrale Control Plane**
Du behandelst LLM‑Provider wie Infrastruktur: **einheitliche API**, Policies zentral, Observability zentral.

**Bausteine**
1. **Model Matrix** (Layer → role → provider/model_id) = *Source of Truth*
2. **Policy Gate** (hard deny anthropic/claude, allowlists, budgets)
3. **Router/Client** (OpenAI‑compat oder per Adapter) mit Fallback‑Strategien
4. **Ledger/Audit Trail** (immutable events, Evidence Pack)
5. **Cursor Multi‑Agents** als “Control Plane UI” für Dev/Research (nicht als Prod‑Runtime)

**Empfehlung:**  
- Prod‑Runtime: euer eigener `model_client` + policy checks.  
- Cursor: nutzt eure Agenten‑Rollen, aber **immer** über dieselbe policy‑validierte Config.

---

## Agenten‑Rollen in Cursor
Ziel: Cursor nutzt mehrere spezialisierte Agenten parallel, aber **keiner** darf die Policy umgehen.

### Rollen (empfohlen)
1. **Orchestrator Agent**  
   - nimmt Tasks an, splittet in Sub‑Tasks, sammelt Results
   - darf keine direkten Code‑Commits ohne Critic‑Freigabe

2. **Research Agent (L1)**  
   - sammelt Quellen, schreibt Evidence‑Packs, dokumentiert Annahmen
   - Output: `docs/ai/evidence_packs/<topic>/<run_id>/`

3. **Market Analyst Agent (L2)**  
   - erzeugt Market‑Outlook Artefakte (keine Trades, keine “signals” ohne Gate)
   - Output: `research/market_outlook/<date>/<run_id>/`

4. **Policy Critic Agent (L4)**  
   - prüft auf Policy/Operational Safety, SoD, Scope‑Violations
   - Output: `audits/<run_id>/critic_report.md`

5. **Engineer Agent**  
   - implementiert Änderungen (Code/Configs), immer mit Tests & Logging
   - Output: PR‑ready Diff + changelog notes

6. **Release Manager Agent**  
   - checkt Versionierung, migration notes, Rollback plan, tags
   - Output: `docs/ops/release/<version>.md`

### Cursor‑Setup (konkret)
- Lege in Cursor pro Rolle ein **Agent Profile** an:
  - **System Prompt** (Rollenbeschreibung)
  - **Tool Policy** (was darf er anfassen)
  - **Output Contract** (Dateipfade + Format)
- Wichtiger Trick: **gemeinsame “Repo Rules”**: jeder Agent muss
  - einen `run_id` erzeugen
  - alle Artefakte unter `./runs/<run_id>/...` ablegen
  - am Ende eine “Result Summary” + “Risk Notes” schreiben

---

## Model‑Policy: “No Anthropic/Claude”
Du willst *alle Anbieter außer Anthropic*. Das heißt: **Multi‑Provider erlaubt**, aber mit harten Deny‑Regeln.

### Hard Deny Rules (MUSS)
- `provider == "anthropic"` → abort
- `model_id` matcht `^claude-` oder enthält `claude` → abort
- `base_url` enthält `anthropic` → abort

### Soft Guard Rules (SOLL)
- Provider muss in `ALLOWED_PROVIDERS` sein (e.g. openai, google, mistral, bedrock, together, azure)
- Model‑IDs müssen allowlisted sein oder aus “registry snapshot” stammen
- Budget‑Limits pro Layer/Run

### Wo enforced?
- **(1) beim Laden der Layer‑Matrix** (fail‑fast beim Start)
- **(2) im `model_client`** (defense in depth)
- **(3) in CI** (config‑lint)

---

# Phasen‑Runbook

## Phase 0 – Bootstrap
**Ziel:** Repo‑Struktur, Policies, minimaler Tooling‑Backbone, damit Agenten sauber arbeiten können.

### Einstiegspunkt
- Du hast die Layer/Runner/Configs im Repo, Cursor kann das Repo öffnen.
- Grundlegende Tests laufen lokal.

### Schritte
1. **Run‑ID Standard einführen**
   - Format: `YYYYMMDD_HHMMSS_<short>` (oder UUID)
   - Convention: jeder Agent schreibt nach `runs/<run_id>/...`
2. **Verzeichnisstruktur**
   - `runs/` (ephemeral)
   - `audits/` (persistent, versioniert)
   - `docs/ai/evidence_packs/`
   - `configs/ai/` (Layer‑Matrix, allowlists, budgets)
3. **Config‑Lint Job**
   - `scripts/ops/config_lint.sh`: parse TOML/YAML, validate schema
4. **Hard Deny implementieren**
   - `src/ai_orchestration/model_policy.py`: deny anthropic/claude
   - `src/ai_orchestration/model_client.py`: deny anthropic/claude
5. **Observability Basics**
   - Jede LLM‑Call: log line mit `run_id`, `layer`, `role`, `provider`, `model_id`, `request_hash`
   - Exporter Metric: `llm_calls_total{layer,role,provider,model_id}`

### Endpunkt (Definition of Done)
- `config_lint` läuft in CI grün.
- Policy‑Deny greift: Test zeigt, dass `provider=anthropic` oder `model_id=claude-*` *hart* failt.
- Ein Minimal‑Run erzeugt ein Audit‑Artefakt mit run_id.

---

## Phase 1 – Multi‑Agent Foundation
**Ziel:** Cursor Multi‑Agent Workflow operationalisieren: Rollen, Output Contracts, Review‑Flow.

### Einstiegspunkt
- Phase 0 abgeschlossen, Repo enthält Run‑ID Standard + Policy Gate.

### Schritte
1. **Agent Profiles in Cursor anlegen**
   - Orchestrator, Research, Analyst, Critic, Engineer, Release Manager
2. **Output Contracts**
   - Jeder Agent schreibt:
     - `runs/<run_id>/<agent>/result.md`
     - `runs/<run_id>/<agent>/risks.md`
3. **SoD Workflow**
   - Engineer darf nur “draft changes”
   - Critic prüft `runs/<run_id>/diff.patch` + `policy_report.md`
4. **“Merge Gate”**
   - Nur wenn `critic_passed == true` und `tests_passed == true`

### Endpunkt
- Ein kompletter Multi‑Agent Durchlauf (kleiner Task) erzeugt:
  - Evidence Pack (falls Research beteiligt)
  - Critic Report
  - PR‑Diff + Changelog

---

## Phase 2 – Model‑Matrix & Routing
**Ziel:** Für L0–L4 eine klare, provider‑agnostische Matrix: primary/fallback/critic je Layer.

### Einstiegspunkt
- Multi‑Agent Workflow stabil.

### Schritte
1. **Matrix als Source of Truth**
   - Datei: `configs/ai/layer_model_matrix.toml` (oder vorhandene Matrix‑MD + loader)
2. **Provider Adapter**
   - OpenAI‑API direkt (bereits da)
   - Adapter‑Stubs für: google, mistral, bedrock, together, azure
   - Wichtig: *einheitliche Interface‑Signatur* (messages, tools, budgets)
3. **Fallback‑Strategie pro Layer**
   - Trigger: timeout, rate limit, provider outage
   - Reihenfolge: primary → fallback1 → fallback2 → abort
4. **Budget‑Policy**
   - `max_tokens`, `max_cost_eur`, `max_calls` pro Layer/Run

### Empfohlene Start‑Matrix (ohne Anthropic)
> Du passt die konkreten IDs an eure Provider‑Verträge an; wichtig ist die Struktur.

- **L0**: primary `openai:gpt-5-nano`, critic `openai:gpt-5-mini`, fallback `google:gemini-2.5-flash-lite`
- **L1**: primary `openai:o3-deep-research`, fallback `openai:o4-mini-deep-research`, critic `openai:gpt-5.2`
- **L2**: primary `openai:gpt-5-mini`, fallback `google:gemini-2.5-flash`, critic `openai:gpt-5.2`
- **L3**: primary `openai:gpt-5.2`, fallback `mistral:mistral-medium-latest`, critic “call L4 service”
- **L4**: primary `openai:gpt-5.2-pro`, critic `openai:gpt-5.2`, fallback `google:gemini-2.5-flash (degraded)`

### Endpunkt
- Matrix lädt deterministisch, `config_lint` validiert.
- Ein “dry run” kann provider‑fail simulieren und korrekt auf fallback wechseln.
- Audit‑Logs zeigen `(layer, role, provider, model_id)`.

---

## Phase 3 – Evaluations & “Verified”
**Ziel:** Du willst nicht “best overall”, sondern **best per Layer/Role** unter euren Constraints.

### Einstiegspunkt
- Phase 2 Matrix + Fallback läuft.

### Schritte
1. **Eval Harness**
   - `tests/eval/` mit 30–100 Cases pro Layer
   - Metriken: pass@1, policy violations, format compliance, latency p95, cost estimate
2. **Golden Outputs**
   - Für deterministische Teile: Snapshot‑Tests
   - Für LLM: tolerance windows + structural validation
3. **“Verified” Definition**
   - Verified = (a) allowlisted, (b) eval score über threshold, (c) budget ok
4. **Registry Snapshot**
   - `configs/ai/verified_models.lock` (frozen list + timestamp)
   - Matrix darf nur auf verified lock referenzieren (Prod)

### Endpunkt
- Verified lock existiert, CI erzwingt, dass Prod‑Matrix nur verified models nutzt.
- Regression‑suite läuft auf PRs.

---

## Phase 4 – Shadow
**Ziel:** Realistische Inputs, aber keine Orders. Alles wird gemessen, geloggt, kritisiert.

### Einstiegspunkt
- Verified lock + Matrix existieren.

### Schritte
1. **Shadow Runner**
   - L2/L3 erzeugen Outputs, L4 critic prüft
   - L5 gate rechnet deterministisch “would block/would allow”
2. **Observability**
   - Dashboards: LLM call volume, cost, p95 latency, critic fail rate
3. **Drift Detection**
   - Wenn provider/model version drift: alert + auto‑disable
4. **Kill Switch**
   - Env `AI_ENABLED=false` global
   - `AI_ARMED=false` for any escalation path

### Endpunkt
- 1–2 Wochen Shadow Daten (oder definierte Anzahl Runs) ohne Policy incidents.
- Budget/latency in bounds.

---

## Phase 5 – Testnet
**Ziel:** End‑to‑end (inkl. Exchange/Testnet), aber weiterhin risk‑controlled.

### Einstiegspunkt
- Shadow stabil, Gate‑Logs sauber, keine Policy Leaks.

### Schritte
1. **Enablement**
   - `AI_ENABLED=true`, `AI_ARMED=false` (nur sim actions)
2. **Trade Simulation**
   - Orders nur Testnet
   - L5 Gate entscheidet, L4 critic muss “pass” geben
3. **Post‑Trade Review**
   - Evidence pack + ledger events + critic report pro run_id

### Endpunkt
- Definierte Testnet‑KPIs erreicht (Fill rate, expected slippage bounds, zero policy violations).
- Rollback procedure getestet.

---

## Phase 6 – Live (Gated)
**Ziel:** Live nur nach zwei Stufen + Confirm Token.

### Einstiegspunkt
- Testnet stabil, On‑call runbook ready, dashboards green.

### Schritte
1. **Arming**
   - `AI_ENABLED=true`
   - `AI_ARMED=true` nur kurzfristig, zeitlich begrenzt (TTL)
2. **Confirm Token**
   - pro Session/Run: token required
3. **Circuit Breakers**
   - Max daily loss, max drawdown, max order rate
4. **Forensics**
   - Jede Order referenziert `run_id` + ledger chain

### Endpunkt
- Live nur mit aktiver Human‑Freigabe, alle Events auditierbar.

---

## Incidents, Rollback, Forensics

### Incident Triggers
- Policy violation (z. B. forbidden provider/model)
- Budget runaway
- Unexpected model drift
- Critical service latency spikes

### Sofortmaßnahmen (1‑Minute actions)
1. `AI_ARMED=false`
2. `AI_ENABLED=false` (wenn nötig global)
3. Capture: `runs/<run_id>/` + logs + metrics snapshot

### Rollback
- Deploy rollback to previous verified lock
- Revert matrix to last known good

### Forensics
- Ledger chain prüfen: input → decisions → critic → gate → (testnet/live)
- Identify: “who selected which model and why” (policy logs)

---

## Checklisten

### Pre‑Merge (AI‑relevant)
- [ ] Policy deny anthropic/claude tested
- [ ] config_lint green
- [ ] eval suite unchanged or improved
- [ ] logs include provider/model_id/run_id

### Pre‑Shadow
- [ ] verified_models.lock exists
- [ ] dashboards working
- [ ] kill switches tested

### Pre‑Live
- [ ] arming TTL + confirm token tested
- [ ] rollback rehearsed
- [ ] on‑call escalation path documented

---

## Appendix: Konfig‑Snippets

### 1) Layer Model Matrix (TOML – Beispiel)
```toml
# configs/ai/layer_model_matrix.toml

[global]
forbidden_providers = ["anthropic"]
forbidden_model_prefixes = ["claude-"]
allowed_providers = ["openai", "google", "mistral", "bedrock", "together", "azure"]

[L0.primary]
provider = "openai"
model_id = "gpt-5-nano"

[L0.critic]
provider = "openai"
model_id = "gpt-5-mini"

[L0.fallback]
provider = "google"
model_id = "gemini-2.5-flash-lite"

[L1.primary]
provider = "openai"
model_id = "o3-deep-research"

[L1.fallback]
provider = "openai"
model_id = "o4-mini-deep-research"

[L1.critic]
provider = "openai"
model_id = "gpt-5.2"

# ...
```

### 2) Policy Validation – Pseudocode
```python
def validate_cfg(provider: str, model_id: str, base_url: str | None = None):
    if provider.lower() == "anthropic":
        raise ValueError("Forbidden provider: anthropic")
    if model_id.lower().startswith("claude-") or "claude" in model_id.lower():
        raise ValueError("Forbidden model_id (claude)")
    if base_url and "anthropic" in base_url.lower():
        raise ValueError("Forbidden base_url (anthropic)")
```

### 3) Cursor Agent Output Contract (Template)
```md
# runs/<run_id>/<agent>/result.md
## Summary
## Inputs
## Actions
## Outputs/Artifacts
## Risks & Open Questions
## Next Step (handoff)
```

---

## Download
Speichere diese Datei als `peak_trade_cursor_multi_agent_runbook.md` in deinem Repo oder nutze den Download‑Link unten.
