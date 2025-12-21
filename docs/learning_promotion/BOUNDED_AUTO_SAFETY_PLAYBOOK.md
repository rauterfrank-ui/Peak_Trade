# bounded_auto – Safety, Governance & Dry-Run Playbook

## Übersicht

Dieses Dokument beschreibt die Safety-Features, Go/No-Go-Kriterien und das Dry-Run-Verfahren für den **bounded_auto-Modus** des Learning & Promotion Loop Systems.

**Zielgruppe:** System-Operator, DevOps, Governance-Verantwortliche

**Letzte Aktualisierung:** 2025-12-12

---

## 1. Status – Mission Accomplished

### Aktueller Stand des Learning & Promotion Loop Systems

* ✅ **10/10 Stabilisierungs-Cycles** erfolgreich durchlaufen
* ✅ Kritische Findings (Blacklist + Bounds) wurden **nicht nur beobachtet, sondern als Code-Sicherheitsfeatures implementiert**
* ✅ **P0-Sicherheitsfeatures aktiv:**

  * **Promotion-Blacklist:** Strategien/Tags, die niemals auto-promoted werden dürfen
    * Target-Blacklist: z.B. `live.api_keys`, `risk.stop_loss`, `live.max_order_size`
    * Tag-Blacklist: z.B. `r_and_d`, `experimental`, `untested`
  * **Harte metrische Bounds:** z.B. `min_sharpe`, `max_drawdown`, `min_trades`
    * Leverage-Bounds: min/max/max_step
    * Trigger-Delay-Bounds: min/max/max_step
    * Macro-Weight-Bounds: min/max/max_step
  * **bounded_auto Guardrails:**
    * Ignoriert alle Kandidaten mit P0-Sicherheitsflags (Blacklist/Bounds)
    * Ignoriert alle Strategien mit `tier = "r_and_d"` oder `is_live_ready = False`
    * Prüft Confidence-Threshold vor Auto-Apply
    * Respektiert Global Promotion Lock

* ✅ **P1-Sicherheitsfeatures aktiv:**

  * **Promotion-Audit-Log:** Jede Entscheidung wird protokolliert (JSONL-Format)
    * Pfad: `reports/promotion_audit/promotion_audit.jsonl`
    * Enthält: Timestamp, Mode, Patch-Details, Decision, Safety-Flags
  * **Globaler Promotion-Lock:** `global_promotion_lock` in Config
    * `true` → bounded_auto komplett deaktiviert
    * `false` → bounded_auto darf arbeiten (innerhalb Safety-Grenzen)

### Kurzfassung

> **Stabilisierungsphase ✅**  
> **Safety-Sprint P0+P1 ✅**  
> **System ist bounded_auto-ready, aber bewusst nur unter Operator-Governance.**

---

## 2. Operator Go/No-Go Checkliste

Diese Checkliste definiert, wann bounded_auto aus Governance-Sicht „GO" hat.

### 2.1 Technische Voraussetzungen (müssen erfüllt sein)

#### P0-Sicherheitsfeatures (kritisch)

- [ ] **Promotion-Blacklist wird im Code geprüft**
  - [ ] `blacklist_targets` konfiguriert in `promotion_loop_config.toml`
  - [ ] `blacklist_tags` konfiguriert in `promotion_loop_config.toml`
  - [ ] Blacklisted Kandidaten erhalten P0-Flag (`P0_BLACKLIST`)
  - [ ] bounded_auto ignoriert alle Kandidaten mit P0-Flags

- [ ] **Harte Bounds werden geprüft**
  - [ ] Leverage-Bounds konfiguriert (`leverage_min`, `leverage_max`, `leverage_max_step`)
  - [ ] Trigger-Delay-Bounds konfiguriert
  - [ ] Macro-Weight-Bounds konfiguriert
  - [ ] Out-of-bounds Kandidaten erhalten P0-Flag (`P0_BOUNDS`)
  - [ ] bounded_auto ignoriert alle Kandidaten mit Bounds-Verletzungen

- [ ] **bounded_auto Guardrails aktiv**
  - [ ] Tier-Check: `tier = "r_and_d"` → keine Auto-Promotion
  - [ ] Readiness-Check: `is_live_ready = False` → keine Auto-Promotion
  - [ ] Confidence-Check: `confidence_score < min_confidence_for_auto_apply` → keine Auto-Promotion
  - [ ] Global-Lock-Check: `global_promotion_lock = true` → keine Auto-Promotion

#### P1-Features (wichtig)

- [ ] **Promotion-Audit-Log funktioniert**
  - [ ] `audit_log_path` in Config gesetzt
  - [ ] Log-Verzeichnis ist schreibbar
  - [ ] Test-Entry wurde erfolgreich geschrieben

- [ ] **Globaler Promotion-Lock funktioniert**
  - [ ] `global_promotion_lock` in Config vorhanden
  - [ ] Lock ON → bounded_auto deaktiviert (getestet)
  - [ ] Lock OFF → bounded_auto darf arbeiten (getestet)

### 2.2 Praktischer Funktionstest (muss mindestens einmal gemacht sein)

- [ ] **Testlauf mit konstruierten Kandidaten durchgeführt:**
  - [ ] **Kandidat A (blacklisted):**
    - Target oder Tag ist blacklisted
    - Erwartet: P0-Flag `P0_BLACKLIST`
    - Erwartet: Nicht auto-promoted
  - [ ] **Kandidat B (out-of-bounds):**
    - Wert verletzt min/max oder max_step
    - Erwartet: P0-Flag `P0_BOUNDS`
    - Erwartet: Nicht auto-promoted
  - [ ] **Kandidat C (gültig):**
    - Innerhalb aller Bounds
    - Nicht blacklisted
    - Confidence >= Threshold
    - Erwartet: Prinzipiell auto-promotable

- [ ] **Audit-Log geprüft:**
  - [ ] Einträge für alle Kandidaten vorhanden
  - [ ] Einträge enthalten:
    - Mode (`manual_only`, `bounded_auto`)
    - Strategie-ID, Target, alte/neue Werte
    - Relevante Metriken (Confidence, Tags)
    - Safety-Flags
    - Entscheidung (`ACCEPTED_FOR_PROPOSAL`, `REJECTED_BY_POLICY`, etc.)
    - Reasons

- [ ] **Globaler Lock geprüft:**
  - [ ] Lock ON getestet → bounded_auto führt keine Promotionen aus
  - [ ] Lock OFF getestet → bounded_auto verhält sich wie erwartet

### 2.3 Governance-Entscheidung

- [ ] **Modus für Start ist klar definiert:**
  - [ ] bounded_auto läuft **zunächst nur im Dry-Run-Modus**
    - Erzeugt Pläne/Reports
    - Schreibt **noch keine echten Promotions**

- [ ] **Verantwortlichkeiten geklärt:**
  - [ ] Wer bounded_auto aktivieren darf
    - Lock OFF / Config anpassen
    - Dokumentiert in: _______________________
  - [ ] Wer bounded_auto im Incident-Fall sofort deaktivieren darf
    - Lock ON / Config anpassen
    - Dokumentiert in: _______________________

- [ ] **Scope definiert:**
  - [ ] In welcher Umgebung bounded_auto starten darf:
    - [ ] Nur Shadow/Testnet-Konfigurationen
    - [ ] Nur bestimmte Strategie-Familien: _______________________
    - [ ] Produktions-Umgebung: Ja/Nein _______________________
  - [ ] Datum/Timestamp der ersten bounded_auto-Aktivierung dokumentiert:
    - Datum: _______________________
    - Operator: _______________________

### 2.4 Go/No-Go Regel

* ✅ **GO** → wenn **alle** Kästchen oben abgehakt sind
* ❌ **NO-GO** → sobald
  * ein P0/P1-Mechanismus unklar oder fehlerhaft ist, **oder**
  * der Governance-Prozess (Lock/Verantwortliche) nicht eindeutig ist

---

## 3. bounded_auto Dry-Run Playbook (nächste 7–14 Tage)

**Ziel:** bounded_auto unter Realbedingungen beobachten, aber zunächst **ohne echte Promotions**.

### 3.1 Schritt 1 – Dry-Run-Modus aktivieren

**Config-Anpassungen:**

1. Öffne `config/promotion_loop_config.toml`
2. Setze:

```toml
[promotion_loop]
mode = "bounded_auto"  # Aktiviert bounded_auto-Logik

[promotion_loop.governance]
global_promotion_lock = false  # Erlaubt Proposal-Generierung
```

3. **WICHTIG:** Im Code/Script sicherstellen, dass:
   * bounded_auto nur **Proposals** generiert
   * bounded_auto **KEINE** echten Config-Änderungen schreibt
   * Optionale Flag-/Umgebungsvariable für Dry-Run nutzen (falls implementiert)

**Beispiel-Aufruf (falls Script Dry-Run unterstützt):**

```bash
python scripts/run_promotion_proposal_cycle.py --dry-run
# oder
export BOUNDED_AUTO_DRY_RUN=true
python scripts/run_promotion_proposal_cycle.py
```

### 3.2 Schritt 2 – 3–5 Cycles im Dry-Run durchlaufen lassen

**Für die nächsten 3–5 Promotion-Cycles:**

1. **Promotion-Cycle starten:**

```bash
python scripts/run_promotion_proposal_cycle.py --dry-run
```

2. **bounded_auto generiert im Dry-Run:**
   * Liste von Kandidaten, die promoten würde
   * Separaten "Plan-Output", z.B.:
     * `reports/live_promotion/<proposal_id>/proposal_meta.json`
     * `reports/live_promotion/<proposal_id>/config_patches.json`
     * `reports/live_promotion/<proposal_id>/OPERATOR_CHECKLIST.md`

**Operator-Aufgabe nach jedem Run:**

- [ ] **Plan/Report öffnen:**
  - Welche Strategien wären promoted worden?
  - Sind alle „verdächtigen" Kandidaten (Blacklist, schlechte Metriken) korrekt ausgeschlossen?

- [ ] **Kurz-Notizen machen:**
  - „bounded_auto verhält sich wie erwartet in Fall X/Y"
  - „Auffällig: Kandidat Z war knapp, aber noch innerhalb Bounds – okay/nicht okay?"
  - Notizen in: `docs/learning_promotion/OPERATOR_DECISION_LOG.md`

### 3.3 Schritt 3 – Blacklist- und Bounds-Verhalten explizit testen

**Mindestens einen Dry-Run so aufsetzen:**

1. **Input-Patches konstruieren mit:**
   - Mindestens einer **blacklisted** Strategie (oder blacklisted Tag)
   - Mindestens einer Strategie, die **Bounds** verletzt
   - Mindestens einer **sauberen** Strategie

2. **Erwartung:**
   - bounded_auto-Dry-Run schlägt **ausschließlich die saubere Strategie** vor
   - Audit-Log & Plan-Report dokumentieren klar:
     - Gründe, warum andere Kandidaten rausgefallen sind (P0-Flags)

3. **Prüfung:**

```bash
# Audit-Log prüfen
cat reports/promotion_audit/promotion_audit.jsonl | jq 'select(.decision_status == "REJECTED_BY_POLICY")'

# Plan-Report prüfen
cat reports/live_promotion/<proposal_id>/config_patches.json | jq .
```

### 3.4 Schritt 4 – bounded_auto „Live"-Freigabe vorbereiten

**Wenn nach 3–5 Dry-Run-Cycles klar ist:**

- [ ] bounded_auto respektiert:
  - [ ] Blacklist
  - [ ] Bounds
  - [ ] Tier/Readiness
  - [ ] Globalen Lock

- [ ] Die Vorschläge sind **intuitiv nachvollziehbar**

- [ ] Das Audit-Log ist **brauchbar lesbar**

**Dann kann die Governance-Entscheidung getroffen werden:**

#### Option A – konservativ (empfohlen für Start)

bounded_auto bleibt dauerhaft im **Dry-Run-Modus**:

* Liefert kontinuierlich Vorschläge
* Operator entscheidet weiterhin manuell, ob Patches angewendet werden
* Risiko: Minimal (nur Proposals, keine Auto-Applies)

#### Option B – scharf, aber gebounded (nur nach erfolgreicher Option A)

bounded_auto darf in einem **begrenzten Scope** echte Promotions durchführen:

* **Nur für bestimmte Strategie-Familien** (z.B. nur `leverage`, nicht `risk`)
* **Nur in Test-/Shadow-Umgebung** (nicht Produktion)
* **Nur wenn zusätzlich ein „Approval-Flag" gesetzt ist**

**In jedem Fall:**

- [ ] **Aktivierung dokumentieren:**
  - Datum & Scope in `docs/learning_promotion/OPERATOR_DECISION_LOG.md`
  - Commit-Message mit klarem Hinweis

- [ ] **Global Promotion Lock dient als Notbremse:**
  - Bei Incident: `global_promotion_lock = true` setzen
  - bounded_auto ist sofort deaktiviert

---

## 4. Optionale Modi & Sicherheitsstufen

### Modus-Übersicht

| Modus | Beschreibung | Risiko | Empfohlen für |
|-------|-------------|--------|--------------|
| `disabled` | Killswitch – keine Proposals, kein Auto-Apply | Minimal | Incident-Response |
| `manual_only` | Nur Proposals generieren, kein Auto-Apply | Minimal | Standard, Produktion |
| `bounded_auto` (Dry-Run) | Proposals + Plan-Reports, kein Auto-Apply | Gering | Testing, Validation |
| `bounded_auto` (Live) | Proposals + Auto-Apply innerhalb Bounds | Mittel | Nach erfolgreicher Dry-Run-Phase |

### Sicherheitsebenen

#### P0 – Kritische Safety-Features (MUSS)

* Promotion-Blacklist (Targets + Tags)
* Harte Bounds (min/max/max_step)
* bounded_auto Guardrails (Tier, Readiness, Confidence, Lock)

**Verletzung → Auto-Promotion unmöglich**

#### P1 – Wichtige Safety-Features (SOLLTE)

* Audit-Log (vollständige Nachvollziehbarkeit)
* Global Promotion Lock (Notbremse)

**Verletzung → Governance-Problem, aber technisch nicht blockierend**

---

## 5. Technisches Tooling

### 5.1 Readiness-Check

**Tool:** `scripts/check_bounded_auto_readiness.py`

**Zweck:** Automatische Prüfung der Go/No-Go-Kriterien

**Verwendung:**

```bash
python scripts/check_bounded_auto_readiness.py
```

**Ausgabe:**

* Text-Zusammenfassung mit `[OK]`, `[WARN]`, `[ERR]` für jeden Check
* Exit-Code:
  * `0` → READY (GO)
  * `1` → NOT READY (NO-GO)

**Checks:**

1. P0-Sicherheitskonfiguration (Blacklist + Bounds)
2. bounded_auto Guardrails im Code konfiguriert
3. Globaler Promotion-Lock konfiguriert
4. Audit-Log-Settings vorhanden

**Beispiel-Ausgabe (Erfolg):**

```
[bounded_auto readiness]

Status: READY (GO)

Checks:
  [OK] P0-Sicherheitskonfiguration gefunden (Blacklist + Bounds)
  [OK] bounded_auto Guardrails im Code konfiguriert
  [OK] Globaler Promotion-Lock konfiguriert
  [OK] Audit-Log-Settings vorhanden

Hinweis:
  bounded_auto kann im Dry-Run-Modus gestartet werden.
  Siehe docs/learning_promotion/BOUNDED_AUTO_SAFETY_PLAYBOOK.md für Operator-Details.
```

### 5.2 Audit-Log-Analyse

**Alle Entscheidungen anzeigen:**

```bash
cat reports/promotion_audit/promotion_audit.jsonl | jq .
```

**Nur Rejections anzeigen:**

```bash
cat reports/promotion_audit/promotion_audit.jsonl | jq 'select(.decision_status == "REJECTED_BY_POLICY")'
```

**P0-Violations anzeigen:**

```bash
cat reports/promotion_audit/promotion_audit.jsonl | jq 'select(.safety_flags | any(startswith("P0_")))'
```

### 5.3 Config-Anpassungen

**Globalen Lock aktivieren (Notbremse):**

```toml
# config/promotion_loop_config.toml
[promotion_loop.governance]
global_promotion_lock = true  # bounded_auto DISABLED
```

**Modus ändern:**

```toml
# config/promotion_loop_config.toml
[promotion_loop]
mode = "manual_only"      # Sicher, nur Proposals
# mode = "bounded_auto"   # Autopilot (mit Dry-Run oder Live)
# mode = "disabled"       # Killswitch
```

---

## 6. Zusammenfassung in einem Satz

> bounded_auto ist jetzt **sicherheitsgehärtet** (P0/P1), über eine klare Go/No-Go-Checkliste governable und kann kontrolliert im Dry-Run-Modus gefahren werden, bevor es in einem definierten Scope echte Promotionen übernimmt.

---

## 7. Weiterführende Dokumentation

* **Stabilisierungsphase:** `docs/learning_promotion/STABILIZATION_PHASE_COMPLETE.md`
* **Learning Loop Architektur:** `docs/LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md`
* **Operator Decision Log:** `docs/learning_promotion/OPERATOR_DECISION_LOG.md`
* **Config-Referenz:** `config/promotion_loop_config.toml`
* **Safety-Implementierung:** `src/governance/promotion_loop/safety.py`
* **Policy-Definitionen:** `src/governance/promotion_loop/policy.py`

---

**Letzte Aktualisierung:** 2025-12-12  
**Version:** 1.0  
**Autor:** Peak_Trade Governance Team
