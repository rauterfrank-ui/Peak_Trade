# Policy Critic Roadmap (Post-G2)

**Status:** G1 (Core) ✅ + G2 (Wiring) ✅ → Ready for operational refinement

**Leitprinzip:** *Konfigurierbarkeit → reale Cycles → Feedback → erst dann LLM-Enhancements*

Damit bleibt es symbiotisch: Hard-Gates souverän, Critic bremst nur, Operator lernt schnell.

---

## Phase G3 (P0): Policy Packs & Threshold-Tuning

**Ziel:** Ein Critic, der je Umgebung/Run-Type konsistent, aber passend streng ist.

### 1. Policy Pack Struktur einführen

Dateien:
- `policy_packs/ci.yml`
- `policy_packs/research.yml`
- `policy_packs/live_adjacent.yml`

Inhalte pro Pack:
- `enabled_rules[]` - Welche Rules aktiv sind
- `severity_overrides` - z.B. `EXECUTION_ENDPOINT_TOUCH: WARN→BLOCK` in `live_adjacent`
- `path_scopes` - Welche Ordner zählen als "critical"
- `required_context_keys` - z.B. `test_plan` required bei execution/live changes

### 2. Critic lädt Policy Pack über context

```python
decision = evaluate_policy_critic_before_apply(
    diff_text=diff,
    changed_files=files,
    context={
        "environment": "live_adjacent",  # → lädt policy_packs/live_adjacent.yml
        "run_type": "promotion",
        ...
    }
)
```

Report speichert:
- `policy_pack_id` (z.B. "live_adjacent")
- `effective_ruleset_hash` (Audit-stabil)

### 3. Tests erweitern

- "Same diff, different pack → different action"
- Ensure: Secrets bleiben immer BLOCK (in allen Packs)

**Done wenn:** Packs existieren, loader + tests grün, Reports enthalten `policy_pack_id` + hash.

---

## Phase G3.5 (P0): Bounded_auto / Promotion Cycles "Real Data" Runs

**Ziel:** Critic-Noise vs Signal kalibrieren – nicht theoretisch, sondern mit echten Patches.

### Run-Plan (2–5 Cycles)

#### Cycle #1 (Baseline)
- Normaler bounded_auto/promotion run
- Sammle: Critic severity distribution, top rule hits, false positives

#### Cycle #2 (Critical Touch Scenario)
- Erzeuge/verwende ein Proposal, das execution/live/risk tangiert (harmlos, aber in critical path)
- Erwartung: `REVIEW_REQUIRED` oder `AUTO_APPLY_DENY` greift zuverlässig

#### Cycle #3 (Docs/Low Risk)
- Proposal nur in docs/non-critical
- Erwartung: `ALLOW` (oder max INFO), kein unnötiges Gate

#### Cycle #4 (Risk Limit Change with Justification)
- Risk limit change mit context.justification
- Erwartung: WARN (nicht BLOCK) + Testplan

#### Cycle #5 (Secrets Leak Attempt)
- Proposal mit versehentlichem Secret
- Erwartung: BLOCK (kein Durchkommen möglich)

### Output pro Cycle:
- Report JSON mit `governance.policy_critic`
- Kurznotiz: "Operator Decision + warum"
- Mini-Liste: "Regeln zu streng / zu lasch"

**Done wenn:** 5 Cycles dokumentiert, Pattern erkannt, Tuning-Liste erstellt.

---

## Phase G3.6 (P0): Governance Review & Tuning Session

**Ziel:** Packs feinjustieren, ohne Sicherheitsprinzipien zu brechen.

### Tuning-Regeln (nur diese Stellschrauben)

✅ **Erlaubt:**
- Severity overrides pro Pack (z.B. WARN→BLOCK für live_adjacent)
- Path_scopes verfeinern (welche Pfade zählen als critical)
- Required_context_keys hinzufügen (statt Rules zu entfernen)
- Evidence formatting kürzen/verbessern

❌ **Nicht erlaubt:**
- **Secrets:** niemals runterstufen (immer BLOCK)
- **Live-Unlock:** niemals runterstufen (immer BLOCK)
- **Order endpoints:** niemals auto-allow in live_adjacent

### Tuning-Prozess:

1. Review cycle results (G3.5)
2. Identify false positives (zu streng)
3. Identify false negatives (zu lasch)
4. Adjust packs within allowed boundaries
5. Document changes in pack changelog
6. Re-run subset of cycles to verify

**Done wenn:** False positives reduziert, kritische Treffer bleiben hart, dokumentiert.

---

## Phase G4 (P1): Operator Artifacts & UX

**Ziel:** Das Ganze "lebt" im Alltag: schnell erfassbar, auditierbar.

### 1. Report-Renderer verbessern (falls vorhanden)

HTML/Markdown Abschnitt: "Policy Critic Summary"
- Top violations + evidence + recommended_action
- "Minimum test plan" prominent
- Operator questions highlighted
- Policy pack + hash für Audit

### 2. CI Summary polish

GitHub Actions Job Summary:
- Severity badge (🟢 INFO / 🟡 WARN / 🔴 BLOCK)
- Top 3 violations with file:line links
- Test plan checklist
- Artifact-Link im Summary

### 3. CLI Enhancements

```bash
# Quick check mode
policy-critic check --quick

# Interactive mode (shows violations, asks to continue)
policy-critic check --interactive

# Export report
policy-critic check --export html
```

**Done wenn:** Reports gut lesbar, CI Summary polished, CLI interactive mode exists.

---

## Phase G5 (P2, optional): LLM-Augmented Critic

**Ziel:** Mehr Qualität in Reviews, weniger Operator-Last — ohne Autonomie-Risiko.

### LLM nur für:
- ✅ Bessere Begründungen (warum ist das riskant?)
- ✅ Bessere Operator-Fragen (was fehlt in der Begründung?)
- ✅ Bessere Testpläne (welche Edge-Cases?)
- ✅ Bessere Doc-Hinweise (welche Runbook-Schritte fehlen?)

### Harte Invarianten:

1. **LLM darf nur "strenger" sein, nie "lockerer"**
   - Wenn deterministisch ALLOW, LLM darf → REVIEW_REQUIRED
   - Wenn deterministisch BLOCK, LLM darf → BLOCK (nicht runterstufen)

2. **Fail-closed**
   - Wenn LLM unavailable → deterministic Ergebnis bleibt gültig
   - Optional: LLM-Fehler → eskaliere zu REVIEW_REQUIRED (niemals AUTO)

3. **No execution, no network (from LLM)**
   - LLM sieht nur: diff, changed_files, context, deterministic violations
   - LLM darf nicht: Code ausführen, Netzwerk-Calls machen, Dateien ändern

### Architecture:

```python
# Deterministisches Ergebnis ZUERST
deterministic_result = PolicyCritic().review(input_data)

# Optional: LLM Enhancement
if llm_available and should_enhance(deterministic_result):
    enhanced_result = LLMPolicyCritic().enhance(
        deterministic_result=deterministic_result,
        diff=input_data.diff,
        changed_files=input_data.changed_files,
    )
    # Merge: keep worst severity, add LLM insights
    final_result = merge_conservative(deterministic_result, enhanced_result)
```

**Done wenn:** LLM-Enhancement optional aktivierbar, Tests zeigen "niemals permissiver", Docs updated.

---

## Phase G6 (P2): Policy Intelligence Loop (Symbiose mit InfoStream)

**Ziel:** Governance wird lernfähig, ohne zu automatisieren.

### InfoStream Events (GOVERNANCE)

Emitted nach jedem Critic-Run:
- Category: GOVERNANCE
- Tags: severity, rule_ids, policy_pack, auto_apply_result
- Payload: violations summary, pack_id, decision

### Aggregation & Learning:

1. **Häufigste violations**
   - Welche Rules triggern am meisten?
   - Sind das echte Risiken oder false positives?

2. **Häufigste false positives**
   - Pattern-Erkennung: Welche Diffs werden geblockt, sollten aber durch?
   - Operator feedback loop

3. **Pack effectiveness**
   - Welche Packs sind zu streng/lasch?
   - Welche Rules in welchem Pack deaktiviert/aktiviert?

### Human-in-Loop:

InfoStream liefert **Insights**, aber:
- **Mensch entscheidet** über Pack-Changes
- **Mensch dokumentiert** Änderungen
- **Mensch reviewed** Vorschläge

**Done wenn:** InfoStream Events emittiert, Aggregation-Dashboard zeigt Patterns, Operator-Feedback-Loop dokumentiert.

---

## Empfohlene Reihenfolge (Kurzform)

1. ✅ **G1:** Policy Critic Core (done)
2. ✅ **G2:** Wiring & Auto-Apply Gate (done)
3. 🔄 **G3:** Policy Packs (konfigurierbar)
4. 🔄 **G3.5:** 2–5 reale Cycles (Kalibrierung)
5. 🔄 **G3.6:** Tuning Session
6. 🔄 **G4:** Reporting/UX
7. ⏳ **G5:** LLM-Enhancement (optional)
8. ⏳ **G6:** Policy Intelligence Loop (optional)

---

## Operator Definition of Success

✅ **Kritische Änderungen werden zuverlässig gebremst**
   - Auto-apply deny / review required greift bei Secrets, Live-Unlock, Order-Code

✅ **Unkritische Änderungen laufen ohne unnötigen Lärm durch**
   - Docs-only, non-critical paths: ALLOW oder max INFO

✅ **Jeder Run hat einen auditierbaren Governance-Footprint**
   - Report JSON enthält: policy_critic result, pack_id, hash, decision

✅ **Hard-Gates bleiben immer souverän**
   - Policy Critic kann bremsen, aber nie Hard-Gates überschreiben
   - Live-Locks, Risk-Limits, Confirm-Token: unabhängig aktiv

---

## Next Immediate Actions

1. **Commit G1 + G2** (done, ready to commit)
2. **Plan G3 Sprint** (Policy Packs design + implementation)
3. **Schedule real cycles** (bounded_auto integration + 5 test runs)
4. **Document learnings** (after each cycle)

---

**Maintainer:** Peak_Trade Governance Team
**Last Updated:** 2025-12-12
**Status:** G1+G2 Complete, G3+ Planned
