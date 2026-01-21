# AI Autonomy Layer Map & Model Assignment Matrix

**Status:** Authoritative v1.0  
**Effective Date:** 2026-01-08  
**Owner:** ops  
**Scope:** Peak_Trade Day Trading AI Autonomy Layers

---

## PURPOSE

Diese Matrix ist die **authoritative Quelle** für:
- Layer-Definitionen (L0-L6)
- Autonomiestufen (RO/REC/PROP/EXEC)
- Model-Zuordnungen (Primary/Fallback/Critic)
- Tool-Access pro Layer
- Hard Constraints

**Alle Evidence Packs MÜSSEN auf diese Matrix referenzieren.**

---

## DESIGN-PRINZIPIEN (nicht verhandelbar)

1. **Safety-First:** Kein Modell darf Trades „ausführen" oder Execution-Pfad triggern
2. **Separation of Duties (SoD):** Proposer ≠ Critic (unterschiedliche Modelle/Instanzen)
3. **Least Privilege / Tooling:** Tool-Zugriff pro Layer minimal
4. **Deterministische Auditfähigkeit:** Jeder Output ist layer-, modell-, scope-gebunden und geloggt
5. **Hard Gates schlagen Soft Advice:** Risk/Policy/CodeGate-Entscheide sind deterministisch

---

## AUTONOMY LEVELS (Legende)

| Level | Code | Beschreibung |
|---|---|---|
| **Read-Only** | RO | Zusammenfassen, prüfen, extrahieren (keine Empfehlungen) |
| **Recommend** | REC | Empfehlung ohne Plan-Fixierung |
| **Propose** | PROP | Konkreter Vorschlag/Artefakt, aber nicht ausführbar |
| **Execute** | EXEC | Ausführung (**verboten** ohne Freigabe) |

---

## AUTHORITATIVE MATRIX

| Layer ID | Layer Name | Purpose (Day Trading) | Autonomy | Primary Model | Fallback Model(s) | Independent Critic | Tool Access | Hard Constraints |
|---|---|---|---|---|---|---|---|---|
| **L0** | Ops/Docs | Runbooks, Checklisten, Doc-Patches | REC | gpt-5.2 | gpt-5-mini | deepseek-r1 | files | Keine Live-Parameter; keine Secrets; nur Docs |
| **L1** | DeepResearch | Literatur/Methoden/Best Practices, Evidenzrecherche | PROP | o3-deep-research | o4-mini-deep-research, deepseek-r1 | o3-pro | web, files | Nur Research-Outputs; keine „Do X live" Anweisungen |
| **L2** | Market Outlook | Makro/Regime/Szenarien, Risiko-Kontext | PROP | gpt-5.2-pro | gpt-5.2 | deepseek-r1 | web (optional), files | Output = Szenarien + Unsicherheit + No-Trade-Triggers |
| **L3** | Trade Plan Advisory | Intraday Trade-Hypothesen, Setup-Templates | REC/PROP | gpt-5.2-pro | gpt-5.2 | o3 | files | Keine Order-Parameter als „ready to send"; immer Risk-Checklist |
| **L4** | Governance / Policy Critic | Policy-Checks, Evidence Pack Review, Go/NoGo-Begründung | RO/REC | o3-pro | deepseek-r1 | gpt-5.2-pro | files | Darf nichts „freischalten" ohne Evidence IDs; verweist auf CodeGate |
| **L5** | Risk Gate (Hard) | Limits, Exposure, Kill-Switch, Bounded-Auto Regeln | RO | (kein LLM) | — | — | — | Deterministischer Code; LLM darf nur erklären, nicht entscheiden |
| **L6** | Execution | Order Routing/Execution Pipeline | EXEC (forbidden) | — | — | — | — | Ausnahmslos verboten bis Freigabe + Evidence Packs + CodeGate |

---

## MODEL SPECIFICATIONS

### OpenAI Models

| Model ID | Family | Context | Use Cases (Layers) | Cost (USD/1k) | Latency (p50) | Status |
|---|---|---|---|---|---|---|
| `gpt-5.2-pro` | gpt-5 | 200k | L2, L3 | 0.015 / 0.060 | 2000ms | production |
| `gpt-5.2` | gpt-5 | 200k | L0, L2 fallback, L3 fallback | 0.010 / 0.040 | 1500ms | production |
| `gpt-5-mini` | gpt-5 | 128k | L0 fallback | 0.002 / 0.008 | 800ms | production |
| `o3-deep-research` | o3 | 200k | L1 | 0.025 / 0.100 | 15000ms | production |
| `o3-pro` | o3 | 200k | L4, L1 critic | 0.020 / 0.080 | 3000ms | production |
| `o3` | o3 | 200k | L3 critic | 0.015 / 0.060 | 2500ms | production |
| `o4-mini-deep-research` | o4 | 128k | L1 fallback | 0.010 / 0.040 | 8000ms | production |

### DeepSeek Models (Heterogeneous Verification)

| Model ID | Family | Context | Use Cases (Layers) | Cost (USD/1k) | Latency (p50) | Status |
|---|---|---|---|---|---|---|
| `deepseek-r1` | deepseek | 128k | L0 critic, L2 critic, L4 fallback | 0.001 / 0.002 | 1000ms | production |

---

## CAPABILITY SCOPES (Referenz)

Jeder Layer hat einen formalen **Capability Scope**, definiert in:

``
config/capability_scopes/<layer_id>_<layer_name>.toml
``

**Capability Scope definiert:**
- `inputs_allowed` / `inputs_forbidden`
- `outputs_allowed` / `outputs_forbidden`
- `tooling_allowed` / `tooling_forbidden`
- `safety_checks` (runtime enforcement)
- `logging` (required fields: `run_id`, `model_id`, `prompt_hash`, `artifact_hash`, etc.)

**Existierende Capability Scopes:**
- L0: `config/capability_scopes/L0_ops_docs.toml`
- L1: `config/capability_scopes/L1_deep_research.toml`
- L2: `config/capability_scopes/L2_market_outlook.toml`
- L4: `config/capability_scopes/L4_governance_critic.toml`

---

## SEPARATION OF DUTIES (SoD) – MINIMALREGEL

**SoD PASS**, wenn alle Bedingungen erfüllt sind:

1. ✅ Proposer-Run und Critic-Run haben **unterschiedliche `model_id`**
2. ✅ Critic sieht **nur** Inputs + Proposer-Output (keine versteckten Side-Effects)
3. ✅ Critic schreibt **eine** von: `APPROVE`, `APPROVE_WITH_CHANGES`, `REJECT` + Begründung + Evidence-IDs
4. ✅ Bei `REJECT`: Ergebnis ist final (bis neuer Proposer-Run)

**Idealerweise:** Proposer und Critic sind aus unterschiedlichen Model-Familien (z.B. OpenAI GPT-5 vs DeepSeek-R1).

---

## DAY-TRADING SAFETY RULES (Operator-verbindlich)

1. **No-Trade Triggers** müssen in L2/L3 immer genannt werden (News-Risk, Spread/Vol Spike, Data Quality)
2. **Keine Execution-Kommandos** in L3 (keine „place order now"), nur „Hypothese/Plan/Checklist"
3. **Risk Gate bleibt hard:** LLM-Outputs sind nie „authoritative" gegenüber Limits/Kill-Switch
4. **Bounded Auto:** Selbst bei „Go" bleibt Execution auf deterministisch geprüfte Parameter beschränkt
5. **Kill-Switch Priority:** Hardware/Software Kill-Switch überstimmt jede LLM-Empfehlung

---

## EVIDENCE PACK INTEGRATION

Jedes Evidence Pack **MUSS** folgende Felder aus dieser Matrix referenzieren:

| Feld | Quelle (Matrix) | Beispiel |
|---|---|---|
| `layer_id` | Matrix: Layer ID | `L2` |
| `layer_name` | Matrix: Layer Name | `Market Outlook` |
| `autonomy_level` | Matrix: Autonomy | `PROP` |
| `primary_model_id` | Matrix: Primary Model | `gpt-5.2-pro` |
| `fallback_model_id` | Matrix: Fallback Model(s) | `gpt-5.2` |
| `critic_model_id` | Matrix: Independent Critic | `deepseek-r1` |
| `capability_scope_id` | Capability Scope Datei | `L2_market_outlook_v1` |
| `sod_check_status` | Runtime Check | `PASS` / `FAIL` |

**Evidence Pack Template:** `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`

---

## FALLBACK POLICY (Fail-Closed)

**Regel:** Wenn Primary Model unavailable → Fallback Model in order → Bei allen Failures: **Fail Closed**

| Layer | Fallback Order | Fail-Closed Action |
|---|---|---|
| L0 | gpt-5.2 → gpt-5-mini | Alert + Block (keine Docs ohne Review) |
| L1 | o3-deep-research → o4-mini-deep-research → deepseek-r1 | Alert + Block (keine Research ohne Source) |
| L2 | gpt-5.2-pro → gpt-5.2 | Alert + Block (keine Outlook ohne Uncertainty) |
| L3 | gpt-5.2-pro → gpt-5.2 | Alert + Block (keine Plan ohne Risk-Checklist) |
| L4 | o3-pro → deepseek-r1 | Alert + **REVIEW_REQUIRED** (Governance kann nicht skippen) |
| L5 | (kein LLM) | — |
| L6 | (verboten) | `GovernanceViolationError` |

---

## CODEGATE INTEGRATION

**CodeGate** prüft Evidence Packs gegen diese Matrix:

1. ✅ `layer_id` existiert in Matrix (L0-L6)
2. ✅ `primary_model_id` entspricht Matrix-Zuordnung
3. ✅ `critic_model_id` ≠ `primary_model_id` (SoD)
4. ✅ `autonomy_level` entspricht Matrix (RO/REC/PROP/EXEC)
5. ✅ `capability_scope_id` existiert und ist Layer-kompatibel
6. ✅ Hard Constraints eingehalten (z.B. L6 = EXEC → GO-Freigabe erforderlich)

**Bei Violations:** Evidence Pack wird **rejected**, keine Freigabe möglich.

---

## VERSION HISTORY

| Version | Date | Changes | Author |
|---|---|---|---|
| v1.0 | 2026-01-08 | Initial authoritative matrix: 7 Layer, 8 Modelle, SoD Rules, Capability Scope Integration | ops |

---

## REFERENZEN

### Verwandte Dokumente

- **Detailed Spec:** `docs/architecture/ai_autonomy_layer_map_v1.md`
- **Gap-Analyse:** `docs/architecture/ai_autonomy_layer_map_gap_analysis.md`
- **Integration Summary:** `docs/architecture/INTEGRATION_SUMMARY.md`
- **Evidence Pack Template v2:** `docs/governance/templates/AI_AUTONOMY_EVIDENCE_PACK_TEMPLATE_V2.md`

### Configuration Files

- **Model Registry:** `config/model_registry.toml` (detaillierte Model Specs, Budget, Audit)
- **Capability Scopes:** `config&#47;capability_scopes&#47;*.toml` (Layer-spezifische Enforcement Rules)

### Governance

- **GoNoGo Overview:** `docs/governance/AI_AUTONOMY_GO_NO_GO_OVERVIEW.md`
- **Policy Critic Charter:** `docs/governance/LLM_POLICY_CRITIC_CHARTER.md`
- **Governance Rules:** `.cursor/rules/peak-trade-governance.mdc`

---

## USAGE (für Evidence Packs)

**Evidence Pack Header (Minimal):**

``markdown
**Evidence Pack ID:** EVP_20260108_L2_OUTLOOK_001
**Layer ID:** L2
**Layer Name:** Market Outlook
**Autonomy Level:** PROP
**Primary Model:** gpt-5.2-pro
**Critic Model:** deepseek-r1
**SoD Check:** PASS
**Matrix Version:** v1.0 (2026-01-08)
**Capability Scope:** `config/capability_scopes/L2_market_outlook.toml`
``

**Evidence Pack validiert:**
1. Layer ID existiert in Matrix: ✅ L2
2. Primary Model korrekt: ✅ gpt-5.2-pro (Matrix: L2 → gpt-5.2-pro)
3. Critic Model korrekt: ✅ deepseek-r1 (Matrix: L2 Critic → deepseek-r1)
4. SoD: ✅ PASS (gpt-5.2-pro ≠ deepseek-r1)
5. Autonomy: ✅ PROP (Matrix: L2 → PROP)

---

**END OF AUTHORITATIVE MATRIX**

**CRITICAL:** Diese Matrix ist die **single source of truth** für Layer-Model Assignments.  
Alle Änderungen erfordern Owner-Approval + Evidence Pack Update.
