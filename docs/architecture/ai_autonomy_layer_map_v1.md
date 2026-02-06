# AI Autonomy Layer Map + Model Assignment Matrix (Day Trading, Safety-First)

**Status:** Detailed Specification v1.0  
**Authoritative Matrix:** `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md` ⚠️  
**Scope:** Peak_Trade Day Trading. **Execution bleibt verboten**, bis explizite Evidence Packs + Go/NoGo Freigabe vorliegen.  
**Date:** 2026-01-08

> **WICHTIG:** Dieses Dokument ist die **detaillierte Spezifikation**. Die **authoritative Matrix** für Layer→Model Assignments ist:  
> `docs/governance/matrix/AI_AUTONOMY_LAYER_MAP_MODEL_MATRIX.md`  
> Evidence Packs MÜSSEN auf die Matrix referenzieren, nicht auf dieses Dokument.

---

## 0) Design-Prinzipien (nicht verhandelbar)

1. **Safety-First:** Kein Modell darf Trades „ausführen" oder Execution-Pfad triggern.  
2. **Separation of Duties (SoD):** *Proposer ≠ Critic* (unterschiedliche Modelle/Instanzen, getrennte Logs).  
3. **Least Privilege / Tooling:** Tool-Zugriff pro Layer minimal (z.B. Web nur in Research/Outlook, niemals in Execution).  
4. **Deterministische Auditfähigkeit:** Jeder Output ist (a) layer-gebunden, (b) modell-gebunden, (c) scope-gebunden, (d) geloggt.  
5. **Hard Gates schlagen Soft Advice:** Risk/Policy/CodeGate-Entscheide sind deterministisch und überstimmen jedes LLM-Artefakt.

---

## 1) Layer Map (Purpose → Autonomy → Modelle)

### Legende Autonomy

- **RO** = Read-Only (zusammenfassen, prüfen, extrahieren)
- **REC** = Recommend (Empfehlung ohne Plan-Fixierung)
- **PROP** = Propose (konkreter Vorschlag/Artefakt, aber nicht ausführbar)
- **EXEC** = Execute (**verboten**)

### 1.1 Authoritative Matrix

| Layer | Zweck (Day Trading) | Default Autonomy | Primary Model (Proposer) | Fallback/Mirror | Independent Critic (Verifier) | Tool Access | Hard Constraints |
|---|---|---:|---|---|---|---|---|
| **L0 Ops/Docs** | Runbooks, Checklisten, Doc-Patches | REC | GPT-5.2 (Chat) | GPT-5 mini | DeepSeek-R1 | Repo-Text only | Keine Live-Parameter ändern; keine Secrets; nur Docs |
| **L1 DeepResearch** | Literatur/Methoden/Best Practices, Evidenzrecherche | PROP | **o3-deep-research** | o4-mini-deep-research / DeepSeek-R1 | o3-pro (oder GPT-5.2 pro) | Web + Files | Nur Research-Outputs; keine „Do X live" Anweisungen |
| **L2 Market Outlook** | Makro/Regime/Szenarien, Risiko-Kontext | PROP | GPT-5.2 pro | GPT-5.2 | DeepSeek-R1 | Web optional | Output = Szenarien + Unsicherheit + No-Trade-Triggers |
| **L3 Trade Plan Advisory** | Intraday Trade-Hypothesen, Setup-Templates | REC/PROP | GPT-5.2 pro | GPT-5.2 | o3 (Reasoning) | Files only | Keine Order-Parameter als „ready to send"; immer Risk-Checklist |
| **L4 Governance / Policy Critic** | Policy-Checks, Evidence Pack Review, Go/NoGo-Begründung | RO/REC | **o3-pro** (conservative) | DeepSeek-R1 | GPT-5.2 pro (2nd opinion) | Files only | Darf nichts „freischalten" ohne Evidence IDs; verweist auf CodeGate |
| **L5 Risk Gate (Hard)** | Limits, Exposure, Kill-Switch, Bounded-Auto Regeln | RO | (kein LLM) | — | — | — | Deterministischer Code; LLM darf nur erklären, nicht entscheiden |
| **L6 Execution** | Order Routing/Execution Pipeline | **EXEC (forbidden)** | — | — | — | — | Ausnahmslos verboten bis Freigabe + Evidence Packs + CodeGate |

**Hinweis zur Modellwahl:**  
- **o3-deep-research** ist für mehrstufige Recherche und Synthese optimiert (inkl. Web/Connector-Quellen) und ist der Lead für L1.  
- **DeepSeek-R1** dient als heterogener Verifier/Mirror für SoD und als lokales Fallback bei Ausfällen.  
- **OpenAI Modellportfolio** (GPT-5.x, o3-pro, o4-mini-deep-research) sind hier verankert.

---

## 2) Capability Scopes (für Evidence Packs verpflichtend)

Jeder Layer-Run muss ein **Capability Scope** deklarieren:

- **Inputs Allowed:** exakt welche Artefakte/Quellen (z.B. "docs/*", "config snapshots", "market data summary vX").  
- **Outputs Allowed:** Artefakt-Typen (z.B. `ScenarioReport`, `ChecklistPatch`, `EvidenceSummary`).  
- **Tooling Allowed:** `none | files | web | code-interpreter` (Default: minimal).  
- **Forbidden:** Liste (z.B. „Order senden", „Risk Limits ändern", „Secrets anfassen", „Live toggle").  
- **Logging:** `run_id`, `model_id`, `prompt_hash`, `artifact_hash`, `inputs_manifest`, `outputs_manifest`.

### 2.1 Schema-Beispiel (TOML)

```toml
[capability_scope.L2_market_outlook_v1]
layer_id = "L2"
description = "Market Outlook: Makro/Regime/Szenarien"

inputs_allowed = [
  "docs/market_outlook/**/*.yaml",
  "config/macro_regimes/**/*.toml",
  "data/market_snapshots/latest.json"
]

outputs_allowed = [
  "ScenarioReport",
  "RegimeClassification",
  "NoTradeTriggers"
]

tooling_allowed = ["files", "web"]

forbidden = [
  "Order senden",
  "Risk Limits ändern",
  "Secrets anfassen",
  "Live toggle",
  "Execution trigger"
]

[capability_scope.L2_market_outlook_v1.logging]
required_fields = ["run_id", "model_id", "prompt_hash", "artifact_hash", "inputs_manifest", "outputs_manifest"]
```

---

## 3) Separation-of-Duties Check (SoD) – Minimalregel

**SoD PASS**, wenn alle Bedingungen erfüllt sind:

1. Proposer-Run und Critic-Run haben **unterschiedliche model_id** (und idealerweise unterschiedliche Provider/Familie).  
2. Critic sieht **nur** Inputs + Proposer-Output (keine versteckten Side-Effects).  
3. Critic schreibt **eine** von: `APPROVE`, `APPROVE_WITH_CHANGES`, `REJECT` + Begründung + Referenzen auf Evidence-IDs.  
4. Bei `REJECT`: Ergebnis ist final (bis neuer Proposer-Run).

### 3.1 SoD-Implementierung (Pseudocode)

```python
def check_sod(proposer_run: Run, critic_run: Run) -> bool:
    """
    Prüft, ob Separation of Duties eingehalten wurde.
    """
    # 1. Unterschiedliche Modelle
    if proposer_run.model_id == critic_run.model_id:
        return False

    # 2. Critic sieht nur Inputs + Proposer-Output
    if critic_run.inputs != (proposer_run.inputs, proposer_run.output):
        return False

    # 3. Critic hat validen Decision-Status
    if critic_run.decision not in ["APPROVE", "APPROVE_WITH_CHANGES", "REJECT"]:
        return False

    # 4. Begründung + Evidence-IDs vorhanden
    if not critic_run.rationale or not critic_run.evidence_ids:
        return False

    return True
```

---

## 4) Day-Trading Safety Rules (Operator-verbindlich)

1. **No-Trade Triggers** müssen in L2/L3 immer genannt werden (z.B. News-Risk, Spread/Vol Spike, Data Quality).  
2. **Keine Execution-Kommandos** in L3 (keine „place order now"), nur „Hypothese/Plan/Checklist".  
3. **Risk Gate bleibt hard:** LLM-Outputs sind nie „authoritative" gegenüber Limits/Kill-Switch.  
4. **Bounded Auto:** Selbst bei „Go" bleibt Execution auf deterministisch geprüfte Parameter beschränkt.  
5. **Kill-Switch Priority:** Hardware/Software Kill-Switch überstimmt jede LLM-Empfehlung.

---

## 5) Mapping: Evidence Pack → Layer Matrix (Minimal)

Jedes Evidence Pack MUSS referenzieren:

- `layer_id` (z.B. `L2`)  
- `primary_model_id` + `fallback_model_id`  
- `critic_model_id`  
- `capability_scope_id` (oder eingebettet)  
- `run_ids` + Hashes (SHA256 für Artefakte)  
- `decision` (nur RO/REC; Freischaltung erfolgt im CodeGate/GoNoGo Prozess)

### 5.1 Evidence Pack Schema (TOML)

```toml
[evidence_pack.EP_2026_01_08_001]
layer_id = "L2"
primary_model_id = "gpt-5.2-pro"
fallback_model_id = "gpt-5.2"
critic_model_id = "deepseek-r1"
capability_scope_id = "L2_market_outlook_v1"

[evidence_pack.EP_2026_01_08_001.runs]
proposer_run_id = "run_abc123"
critic_run_id = "run_def456"

[evidence_pack.EP_2026_01_08_001.hashes]
proposer_artifact_sha256 = "a1b2c3d4..."
critic_artifact_sha256 = "e5f6g7h8..."

[evidence_pack.EP_2026_01_08_001.decision]
status = "RO"  # Read-Only / Recommendation only
rationale = "Scenario analysis passed SoD; keine Execution-Trigger; safe for archival."
go_nogo_required = true
codegate_ref = "CG_2026_01_08_005"
```

---

## 6) Integration mit bestehenden Governance-Systemen

### 6.1 CodeGate

- **Inputs:** Evidence Packs (mit Layer-Map Referenzen)  
- **Outputs:** Go/NoGo Decision + Freigabe-Token  
- **Regel:** Kein Layer darf ohne CodeGate-Token zu L6 (Execution) eskalieren.

### 6.2 Kill-Switch

- **Priorität:** Überstimmt alle Layer-Outputs (L0-L6).  
- **LLM-Rolle:** Nur explanatory (RO), niemals decisional.

### 6.3 Risk Gates

- **L5 Risk Gate:** Deterministisch, kein LLM-Einfluss auf Limits.  
- **L2/L3 Safety Checks:** LLM generiert No-Trade-Triggers, aber Gate prüft diese nicht (Gate ist unabhängig).

---

## 7) Next Steps (Implementation Roadmap)

1. **Phase 1 (Doc-only):** ✅ Diese Spec als authoritative v1.  
2. **Phase 2 (Schema):** Capability Scope + Evidence Pack Schemas als `.toml` Configs implementieren.  
3. **Phase 3 (SoD Framework):** Python-Modul für Proposer/Critic Orchestration + Logging.  
4. **Phase 4 (Model Integration):** API-Wrapper für o3-deep-research, GPT-5.2, DeepSeek-R1.  
5. **Phase 5 (CodeGate Integration):** Evidence Pack → CodeGate Pipeline.  
6. **Phase 6 (Tests):** Unit + Integration Tests für SoD, Capability Scopes, Evidence Packs.  
7. **Phase 7 (Pilot):** L1 (DeepResearch) + L2 (Market Outlook) Pilot (read-only).  
8. **Phase 8 (Evaluation):** 30-day pilot, dann Go/NoGo für L3 (Trade Plan Advisory).

**Execution bleibt bis dahin verboten.**

---

## 8) Änderungshistorie

| Version | Datum | Änderungen | Autor |
|---|---|---|---|
| v1.0 | 2026-01-08 | Initial authoritative spec | Operator |

---

## 9) Referenzen

- OpenAI Platform Docs: Model Capabilities (o3-deep-research, GPT-5.x)  
- DeepSeek-R1: arXiv:2501.12948  
- Peak_Trade Governance Rules: `.cursor/rules/peak-trade-governance.mdc`  
- Peak_Trade Delivery Contract: `.cursor/rules/peak-trade-delivery-contract.mdc`

---

**END OF DOCUMENT**
