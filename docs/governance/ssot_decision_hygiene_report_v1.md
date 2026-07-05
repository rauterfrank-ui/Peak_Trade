# SSOT Decision Hygiene Report v1

**Status:** READ-ONLY BIAS SCAN — keine SSOT-Auswahl, keine Konfliktauflösung, keine Architektur-Aktion  
**Erzeugt:** 2026-07-05  
**Branch:** `main` @ `2f1672bee8761f8d50def3f6ef31cc803824b2e9`  
**Scope:** Decision Hygiene + Bias Detection vor SSOT-Ratifikation

**Inputs (verwendet):**

| Artefakt | Pfad | Scan-Status |
|----------|------|-------------|
| Authority Resolution Synthesis v1 | [`authority_resolution_synthesis_v1.md`](authority_resolution_synthesis_v1.md) | ✅ gelesen |
| Authority Conflict Matrix v1 | [`authority_conflict_matrix_v1.md`](authority_conflict_matrix_v1.md) | ✅ gelesen |
| System Snapshot Before SSOT Decision v1 | [`system_snapshot_before_ssot_decision_v1.md`](system_snapshot_before_ssot_decision_v1.md) | ✅ gelesen |
| Feature State Map v1 | [`feature_state_map_v1.md`](feature_state_map_v1.md) | ✅ gelesen (Kontext) |
| Drift Cleanup Plan v1 | [`drift_cleanup_plan_v1.md`](drift_cleanup_plan_v1.md) | ✅ gelesen (Kontext) |

**Input (fehlend):**

| Artefakt | Pfad | Scan-Status |
|----------|------|-------------|
| SSOT Decision Surface v1 | `docs/governance/ssot_decision_surface_v1.md` | ❌ **nicht im Repository** — Bias-Scan gegen dieses Artefakt entfällt; Abschnitt 5 vermerkt die Lücke |

**Explizite Nicht-Ziele dieses Reports:**

- Keine SSOT-Ratifikation
- Keine Konfliktauflösung
- Keine Architektur- oder Code-Empfehlung mit Umsetzungscharakter
- Nur Identifikation von Annahmen, Bias und vorzeitiger Kanonisierung

---

## Section 1: Explicit vs Implicit Authorities

### 1.1 Explizit deklarierte Neutralität (korrekt formuliert)

Mehrere Artefakte wiederholen konsistent:

- „SSOT not selected yet“ (Snapshot §Explicit Statements)
- „Candidate“ / „NOT ENFORCED YET“ / „proposal only“ (Synthesis §2, Matrix Spalte „Expected Canonical Ownership“)
- „Keine Enforcement der Expected-Canonical-Ownership-Spalte“ (Matrix §9, Synthesis §5)
- Wiring Inventory: „non-authorizing“, „map not decision“

Diese Formulierungen sind **explizit** und reduzieren Enforcement-Risiko.

### 1.2 Implizite Default-Authorities (nicht ratifiziert, aber systemisch vorbelegt)

| Domäne | Explizite Behauptung | Implizite Default-Authority | Bias-Mechanismus |
|--------|----------------------|------------------------------|------------------|
| **Operational gate** | Validation Rule ist „frozen“ | `feature_state_map_v1` + Runtime Decision Core (`integrated_offline_trading_logic_replay_v1.py`, Slice-B-Bridge) | Regel erscheint in **allen** Governance-Artefakten identisch; wirkt wie bereits ratifizierte Meta-SSOT, obwohl sie selbst von der Feature State Map stammt |
| **Runtime vs Registry** | Registry-Tier ≠ operational | Runtime Core wiring = einziger Weg zu „operational“ | Downstream-Leser können Registry/Config/TOML als „irrelevant“ abwerten, obwohl AUTH-005/012/020 zeigen, dass Tier-Metadaten Routing-Risiko tragen |
| **ECM Identity** | AUTH-001 BLOCKED | `armstrong_cycle` als StrategySpec vs `ecm_cycle` als functional-only | Registry-Typ-Hierarchie (StrategySpec > functional-only) + Docs-Safe-Fixes (A-05, DOC-06 „Canonical“) |
| **Offline compute** | AUTH-017 proposal only | `integrated_offline_trading_logic_replay_v1.py` + `double_play_composition_matrix_v1` | Matrix „Current Ownership: kanonisch offline“; Class A in Feature State Map; Runbook `CANONICAL_OWNER` (extern zum Snapshot, aber repo-weit) |
| **Capital/Risk/Sizing** | AUTH-014 BLOCKED | `capital_risk_sizing_v1.py` merged chain | Matrix „Current Ownership“ = Code-Merge; Runbook = 3 Owner — Synthesis nennt Code „de facto merge truth“ |
| **Registry→Core wiring** | AUTH-019 BLOCKED | `suitability_binding_v1` + offline snapshot, **not** `registry.py` | Bereits in Matrix als „Expected“ verankert; Research-Wiring als einziger dokumentierter Adapter-Pfad |
| **Docs authority chain** | Snapshot: read-only index | Linear: drift report → feature state map → cleanup plan → matrix → synthesis | Frühere Stufen werden in Prosa als „kanonisch“ bezeichnet (Feature State Map = „kanonische Feature-State-Map“) |

### 1.3 ECM / Execution / Capital — Schicht-Präzedenz (implizit)

| Schicht | Implizite Lesereihenfolge | Evidenz |
|---------|---------------------------|---------|
| **Execution / Decision (Domain B)** | Primär für MV2-Pfad, Double Play, Operational-Semantik | AUTH-017 als Tier-0-Root; Boundary-Konflikte AUTH-016/017 primär in B verankert |
| **Capital (Domain C)** | Sekundär, abhängig von B-Slice-Grenzen | AUTH-014 Tier-0, aber AUTH-015/016/018 hängen an AUTH-014 **und** AUTH-017 |
| **ECM / Strategy (Domain A)** | Parallel startbar, aber Cross-Edge zu B via suitability | AUTH-001 → AUTH-019 (strategy_id in snapshot) |
| **Registry** | Promotion-Metadaten, nicht operational — **aber** „Expected Canonical“ in Matrix oft registry-aligned | AUTH-002 Expected: Config aligned to `armstrong_cycle`; AUTH-013: El-Karoui-Alias als Muster |

**Bias-Signal:** Die Domain-Cluster A/B/C suggerieren **gleichwertige** parallele Ratifikation, aber Tier-0 enthält **drei** Domain-B-Roots (AUTH-006, AUTH-017, AUTH-019) vs **einen** Domain-A-Root (AUTH-001) und **einen** Domain-C-Root (AUTH-014). Entscheidungsdruck ist implizit auf Execution/Runtime verschoben.

### 1.4 Registry vs Runtime vs Strategy — implizite Rangfolge

```
Implizite Hierarchie (nicht ratifiziert, aber durch Artefakte verstärkt):

Runtime Decision Core  >  Strategy Registry (operational)
Strategy Registry (StrategySpec)  >  functional-only IDs
Docs „Expected Canonical“  >  competing layer (in Tabellen)
Dual-Source Contract  >  einzelne Registry-Felder (explizit, aber nur wo zitiert)
Config/TOML  >  oft unterrepräsentiert in „Expected“-Spalten
```

**Kritischer Punkt:** Die Validation Rule privilegiert Runtime eindeutig — beabsichtigt als Safety-Gate, aber sie **ersetzt** nicht Strategy-/Registry-SSOT für Identität, Tiering oder Config. Mehrere Tabellen mischen „operational“ und „canonical identity“ ohne Trennspalte.

---

## Section 2: Hidden SSOT Biases

### 2.1 Terminologie-Bias („kanonisch“ ohne Ratifikation)

| Begriff | Wo | Versteckte Wirkung |
|---------|-----|------------------|
| „kanonisch offline“ | Matrix AUTH-006, AUTH-008 Current Ownership | Leser interpretieren als SSOT, obwohl „Expected … NOT ENFORCED“ |
| „Canonical Truth“ | Feature State Map DOC-Tabelle (§3), Drift Cleanup Plan §2 | Spaltenname impliziert bereits entschiedene Wahrheit |
| „Candidate SSOT“ + konkrete ID | Synthesis §2 Domain A/B/C | „Candidate“-Label schwächt nicht die **Benennung** der favorisierten ID |
| „primary StrategySpec-ID“ | Synthesis Domain A, Strategy identity row | `armstrong_cycle` vor `ecm_cycle` — Option (c) dual-ID in Phase A.1 wirkt nachträglich |
| „offline compute authority“ | Synthesis Domain B Summary | Semantische Gleichsetzung von Modul-Pfad und Authority |
| „de facto merge truth“ | Synthesis Domain C Summary | Code-Implementierung als faktische SSOT vor Runbook-Ratifikation |
| „Root-Konflikt“ | Synthesis Domain-Cluster-Tabelle | Priorisierungssprache ohne formale Gewichtung |

### 2.2 Klassifikations-Bias (Konflikttyp → implizite Korrektheit)

| Muster | Beispiel | Bias |
|--------|----------|------|
| Typ **C** (Registry) → Expected = Registry-Alignment | AUTH-002 Expected: Config → `armstrong_cycle` | Registry-Seite als „Expected“ auch wenn AUTH-001 offen |
| Typ **B** (Strategy vs Runtime) → Expected = Runtime | AUTH-006, AUTH-012 | Runtime gewinnt in Expected-Spalte |
| Typ **D** (Architectural Ambiguity) → Expected = zuletzt implementierter Pfad | AUTH-017: Integrated Replay = compute owner | Implementierungs-Reife biasiert gegen Packet-Flow |
| Docs-only Residual Layer | AUTH-021–023 aus Authority-Kern ausgeschlossen | Risiko-Unterschätzung: Docs-Echo kann später Authority-Rückwirkung haben (AUTH-003) |
| „Pattern-Analog“ | AUTH-020 → AUTH-005 | El-Karoui-Lösung (Alias angewendet) als Vorlage für Armstrong-Triangle |

### 2.3 Wave-Order-Bias (Synthesis §3.5)

| Wave | Inhalt | Versteckte Wirkung |
|------|--------|-------------------|
| **W1** | AUTH-006, AUTH-017 supplement, AUTH-012 read model — **Docs markers** | Weiche Kanonisierung von Integrated Replay + Legacy-Ops-Markierung **vor** Governance Decision Records (W2) |
| **W2** | AUTH-001, AUTH-014, AUTH-019 — Decision Records | Identitäts-/Architektur-Entscheidungen **nach** Pfad-Docs-Markern |
| **W3** | Registry/config alignment **proposal** | Folgt implizit den W1/W2-Prämissen |

**Bias:** Docs-Marker in W1 können als „faktisch entschieden“ gelesen werden, bevor W2 formal entscheidet — insbesondere für `integrated_offline_trading_logic_replay_v1` und Ops `LEGACY_NON_AUTHORITATIVE`.

### 2.4 Safe-Fix-Präzedenz-Bias (bereits angewendet)

| Fix | Status | Bias für offene Konflikte |
|-----|--------|---------------------------|
| DOC-09: `el_karoui_vol_v1` → `el_karoui_vol_model` | Section A applied | Alias-Migration als **bewährtes** Muster für AUTH-013 (`ecm_cycle`), AUTH-011 (`rsi_strategy`) |
| Post-A Docs: Strategy-Layer kanonisch für ECM | drift_safe_docs_patch | Docs-Seite der Identität vor Registry-Ratifikation |
| A-05: `ecm_cycle` → Hinweis auf `armstrong_cycle` | Safe fix geplant/teilweise | Einseitige Namensführung in Docs ohne AUTH-001 |

**Bias-Schwere:** MEDIUM — historische Safe-Fixes sind legitim, aber sie **verengen** den wahrgenommenen Optionenraum für AUTH-001.

### 2.5 Boundary-Konflikt-Verankerung

AUTH-016 (Slice A/B) und AUTH-017 (Packet vs Integrated Replay) sind **Cross-Domain**, aber in Synthesis **primär Domain B** verankert („Boundary-Konflikte modelliert, primär in B verankert“).

**Versteckte Annahme:** Execution/Decision-Domäne definiert Slice-Grenzen; Capital folgt. Alternative Lesart (Capital definiert erforderliche Replay-Schritte) ist in der Cluster-Graphik unterrepräsentiert.

---

## Section 3: Premature Canonicalizations

### 3.1 `armstrong_cycle` — de-facto-SSOT-Signale

| # | Signal | Quelle | Vorzeitig? |
|---|--------|--------|------------|
| 1 | „Central `strategy_id` (catalog)“ | Wiring Inventory §4 | Ja — Inventory sagt „non-authorizing“, Tabellenzeile wirkt dennoch wie Katalog-SSOT |
| 2 | DOC-06 „Canonical Truth“ = `armstrong_cycle` in `registry.py` | Feature State Map §3, Drift Cleanup §2.1 | Ja — AUTH-001 explizit BLOCKED |
| 3 | Expected Canonical: Config aligned to `armstrong_cycle` | Matrix AUTH-002 | Ja — setzt Identität voraus |
| 4 | Candidate: `armstrong_cycle` als **primary** StrategySpec-ID | Synthesis §2 Domain A | Ja — „Candidate“ + „primary“ ist widersprüchlich |
| 5 | Action Required: `armstrong_cycle` → „Rename (vs `ecm_cycle`)“ | Feature State Map Class B | Ja — Rename-Richtung ohne Ratifikation |
| 6 | `ecm_cycle` in Class D „naming surface“ | Feature State Map §2.4 | Ja — stuft `ecm_cycle` ab ohne Identity-Record |
| 7 | Safe fix A-05: Docs zeigen auf `armstrong_cycle` | Drift Cleanup §3 | Ja — docs-only Vorab-Alignment |

**Severity:** **HIGH** für AUTH-001 — mehrere unabhängige Artefakte konvergieren auf `armstrong_cycle`, während der formale Status „BLOCKED“ bleibt.

### 3.2 `integrated_offline_trading_logic_replay_v1` — de-facto-SSOT-Signale

| # | Signal | Quelle | Vorzeitig? |
|---|--------|--------|------------|
| 1 | Runtime Decision Core Code-Owner (Slice A) | Matrix §Runtime Decision Core, Feature State Map §1 | Teilweise — als **Integrations**-Owner legitimiert, aber nicht als vollständiger MV2-SSOT |
| 2 | „kanonisch offline“ in Current Ownership | Matrix AUTH-006, AUTH-008 | Ja — AUTH-017 noch proposal |
| 3 | Class A „Master V2 Orchestration (Integrated Replay)“ | Feature State Map §2.1 | Ja — Class A = Core-bound Semantik |
| 4 | Candidate SSOT + Summary „offline compute authority“ | Synthesis §2 Domain B | Ja |
| 5 | Phase B.1: „compute owner = Integrated Replay“ | Synthesis Minimal Path | Ja — Pfadvorschlag als Default |
| 6 | `CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER` | Runbook Progress Registry (repo, nicht Snapshot) | Ja — parallele Authority außerhalb der SSOT-Neutralitäts-Serie |
| 7 | Wave W1: AUTH-017 docs supplement **before** W2 records | Synthesis §3.5 | Ja — Reihenfolge kanonisiert vor Entscheid |

**Severity:** **HIGH** für AUTH-017 — starke Konvergenz auf Integrated Replay; Decision Packet Flow (`local_evaluator_v1`, `decision_packet_v1`) bleibt Class B „parallel track“ ohne symmetrische Candidate-Behandlung.

### 3.3 Weitere vorzeitige Kanonisierungen

| Entity | Signal | Severity |
|--------|--------|----------|
| `double_play_composition_matrix_v1` | Class D „Double Play authority (canonical)“; ersetzt Ops evaluator | MEDIUM |
| `capital_risk_sizing_v1` | „de facto merge truth“ vs Runbook 3-owner | HIGH (AUTH-014) |
| `MASTER_V2_DECISION_AUTHORITY_MAP_V1` | Domain B SSOT-Kandidat in Synthesis Summary | MEDIUM — Spec selbst sagt „non-authorizing“, Referenzierung als Kandidat verstärkt |
| `STRATEGY_REGISTRY_TIERING_DUAL_SOURCE_CONTRACT_V1` | Domain A live-readiness „Leseregel-Oberbehörde“ | MEDIUM — Contract existiert, **pro strategy_id Quelle noch offen** |
| Validation Rule | Meta-SSOT für operational | LOW–MEDIUM — beabsichtigt, aber nicht identisch mit Feature-/Strategy-SSOT |

### 3.4 Asymmetrie: Was **nicht** vor-kanonisiert wird (kontrollierte Gegenprobe)

| Entity | Behandlung | Bias-Richtung |
|--------|------------|---------------|
| `ecm_cycle` | Functional-only, Class D, Config aktiv | Anti-SSOT-Bias (korrekt offen, aber Docs driften zu `armstrong_cycle`) |
| Ops `evaluate_double_play` | LEGACY_NON_AUTHORITATIVE | Explizit de-kanonisiert |
| Decision Packet compute path | Class B, „Defer“ | Unter-kanonisiert vs Integrated Replay |
| Runbook 3-owner Capital chain | Expected offen bis AUTH-014 | Korrekt offen, aber Code-Merge in Current Ownership dominant |

---

## Section 4: Dependency-Induced Bias Chains

### 4.1 Lineare Governance-Artefakt-Kette

```text
feature_drift_reconciliation_report_v1
  → feature_state_map_v1          ← „kanonische Feature-State-Map“
    → drift_cleanup_plan_v1
      → authority_conflict_matrix_v1
        → authority_resolution_synthesis_v1
          → [SSOT Decision — NOT YET]
```

**Bias:** Jede Stufe **übernimmt** frozen rules und Ownership-Tabellen der Vorgängerin. Späte Leser sehen Synthesis-Kandidaten als **logische Fortsetzung**, nicht als Hypothesen. Fehlendes Glied `ssot_decision_surface_v1` bricht die explizite Entscheidungsfläche ab — Synthesis wirkt de facto wie Decision Surface.

### 4.2 Tier-0 → Downstream-Zwangsketten

| Upstream (Tier-0) | Downstream | Erzwungene SSOT-Richtung |
|-------------------|------------|--------------------------|
| AUTH-001 ECM Identity | AUTH-002 Config, AUTH-013 Alias, AUTH-019 suitability keys | Wahl von (a) alias vs (b) migration vs (c) dual-ID **prägt** gesamte Registry/Config-Grammatik |
| AUTH-017 MV2 Path | AUTH-008 replay hierarchy, AUTH-007 packet boundary, AUTH-016 Slice A completeness | Integrated Replay als Compute-Owner **zwingt** Packet zu handoff-only |
| AUTH-019 Registry→Core | AUTH-012 operational read model, AUTH-010/011 functional policy | Suitability-Snapshot-SSOT **entkoppelt** Registry von Core — Registry allein darf nicht SSOT werden |
| AUTH-014 Capital architecture | AUTH-015 Scope Capital replay, AUTH-018 attestation | Merge-vs-split **zwingt** Runbook- und Attestation-SSOT |
| AUTH-006 DP Ops vs Matrix | B-03 docs markers | Docs-only Marker **verstärkt** Matrix ohne Runtime-Change |

### 4.3 Cross-Domain-Zwang (A × B × C)

```text
Chain 1 (Identity → Execution):
  AUTH-001 premature alias (armstrong_cycle)
    → AUTH-019 suitability snapshot keys
      → Integrated Replay strategy module binding
        → Capital/Risk context (wrong strategy parameters)

Chain 2 (Path → Capital):
  AUTH-017 Integrated Replay = compute owner
    → AUTH-015 packet handoff treated as substitute
      → AUTH-018 attestation slot mismatch

Chain 3 (Operational rule → Strategy):
  Validation Rule (Runtime-only operational)
    → AUTH-012 Registry tier misread as non-authoritative for everything
      → AUTH-005 live-readiness triangle ignored in operator UI assumptions
```

### 4.4 Zirkuläre Authority-Annahmen (latent)

| Zirkularität | Beschreibung |
|--------------|--------------|
| **Runtime ↔ Feature State Map** | Map definiert Core-Owner; Validation Rule in Map; Matrix zitiert Map als Kanon — Map ist gleichzeitig Analyseoutput und Norm |
| **Expected Canonical ↔ Current Ownership** | Matrix listet beide; „Expected“ folgt oft „Current“ für Runtime-Pfade — wenig echte Optionen-Darstellung |
| **Candidate SSOT ↔ Collapse Chains** | Synthesis Collapse Chains testen Abweichung von Kandidaten — Kandidaten werden zum impliziten Null-Hypothese-SSOT |
| **El-Karoui alias ↔ ECM alias** | Erfolgreicher Safe-Fix suggeriert gleiche Lösung für AUTH-001 — unterschiedliche Semantik (functional-only vs StrategySpec) |

### 4.5 Registry-vs-Runtime-Abhängigkeit (DEF-02 / AUTH-019 / AUTH-012)

Diese drei Konflikte bilden eine **verdeckte Super-Kette**:

```text
AUTH-019 (kein Default Registry→Core)
  → AUTH-012 (Tier ≠ operational)
    → Validation Rule (NON-OPERATIONAL default)
      → Feature State Map Class A/B Trennung
```

**Bias:** Wer AUTH-019 mit „Registry bleibt Promotion-Katalog“ löst, **verstärkt** Runtime als einzige operational truth — korrekt für Safety, aber **keine** Strategy-Identity-SSOT-Entscheidung.

---

## Section 5: Risk Assessment (Bias Severity)

### 5.1 Gesamtbewertung

| Kategorie | Severity | Begründung (Kurz) |
|-----------|----------|-------------------|
| **`armstrong_cycle` premature SSOT** | **HIGH** | Konvergenz über Docs, Expected-Spalten, Candidate-Primary, Safe-Fixes; widerspricht AUTH-001 BLOCKED |
| **`integrated_offline_trading_logic_replay_v1` premature SSOT** | **HIGH** | Class A + kanonisch offline + W1 vor W2 + Runbook CANONICAL_OWNER außerhalb Snapshot |
| **Validation Rule / Runtime Core meta-SSOT** | **MEDIUM** | Beabsichtigtes Safety-Gate; Risiko: vermischt operational mit identity/canonical |
| **Wave-order (W1 docs before W2 records)** | **MEDIUM** | Weiche Kanonisierung vor formaler Ratifikation |
| **Domain-B-Tier-0-Dichte** | **MEDIUM** | Execution-domäne implizit prioritär vs A/C |
| **`capital_risk_sizing_v1` de-facto truth** | **HIGH** | AUTH-014 offen; Code-Current dominiert Runbook-Expected |
| **El-Karoui alias Präzedenz** | **MEDIUM** | Verengt Optionenraum AUTH-001/011/013 |
| **Boundary-Konflikte in Domain B verankert** | **MEDIUM** | Capital-Slice-Definition folgt Execution-Graph |
| **Fehlendes `ssot_decision_surface_v1`** | **MEDIUM** | Synthesis füllt Lücke; keine explizite neutrale Entscheidungsfläche |
| **Snapshot neutral claim vs „kanonische“ Labels** | **LOW–MEDIUM** | Snapshot sagt neutral; indexiert dennoch „kanonische“ Vorgänger |
| **Docs-only Residual (AUTH-021–023) aus Kern** | **LOW** | Begrenzte unmittelbare SSOT-Wirkung |

### 5.2 Kritikalität nach AUTH-ID (Bias, nicht Konflikt-Risiko)

| AUTH-ID | Bias Severity | Hauptsignal |
|---------|---------------|-------------|
| AUTH-001 | **CRITICAL** | Multi-Artefakt-Konvergenz auf `armstrong_cycle` bei BLOCKED |
| AUTH-017 | **CRITICAL** | Integrated Replay als Default-Compute-Owner in Kandidaten, Waves, Class A |
| AUTH-002 | **HIGH** | Expected Canonical setzt `armstrong_cycle` voraus |
| AUTH-006 | **HIGH** | „kanonisch offline“ Current Ownership |
| AUTH-012 | **MEDIUM** | Operational-Read-Model folgt Runtime-Bias |
| AUTH-014 | **HIGH** | Code de-facto vs Runbook de-jure Spannung ungleich gewichtet |
| AUTH-019 | **MEDIUM** | Suitability-Snapshot als Expected — schließt Registry-SSOT vorweg |
| AUTH-013, AUTH-011 | **MEDIUM** | El-Karoui-Präzedenz |
| AUTH-005, AUTH-020 | **MEDIUM** | Dual-Source Contract als Oberbehörde ohne per-ID-Quelle |
| AUTH-016 | **MEDIUM** | Slice-Grenze durch B-Domäne vorbelegt |

### 5.3 Snapshot-Konsistenz-Check

| Prüffrage | Ergebnis |
|-----------|----------|
| Behauptet Snapshot Neutralität? | Ja — „SSOT not selected yet“, „0 live operational“ |
| Privilegiert Snapshot eine Domäne? | **Indirekt ja** — indexiert Feature State Map als „kanonisch“; listet Synthesis-Kandidaten ohne Bias-Warnung |
| Wird eine Schicht als „primary truth“ behandelt? | **Ja, latent** — Runtime Decision Core + Validation Rule in jedem verknüpften Artefakt |
| Fehlt ein neutraler Decision-Surface-Index? | **Ja** — `ssot_decision_surface_v1.md` nicht vorhanden |
| Externe Authority (Runbook Progress)? | **Ja** — `CANONICAL_OWNER` für Integrated Replay existiert repo-weit, nicht im Snapshot reflektiert |

**Snapshot-Bias-Urteil:** Snapshot ist **explizit neutral**, aber die **indexierte Artefakt-Kette** und fehlende Decision Surface **untergraben** die Neutralitätsbehauptung für unvorsichtige Leser.

---

## Section 6: Neutralization Recommendations (NO ACTION — nur Beschreibung)

> **Hinweis:** Diese Empfehlungen beschreiben **was** vor einer SSOT-Entscheidung klargestellt werden sollte. Sie sind **keine** Ausführungsanweisungen und **keine** SSOT-Wahl.

### 6.1 Terminologie-Entschärfung (Dokumenten-Disziplin, zukünftig)

| Empfehlung | Ziel |
|------------|------|
| „Canonical Truth“ in Tabellen durch „Observed primary surface (disputed)“ / „Governance options pending“ ersetzen | Verhindert DOC-06-ähnliche Vorab-Festlegung |
| „Candidate SSOT“ immer mit **mindestens zwei** benannten Alternativen in derselben Tabellenzeile | Symmetrie für Packet-Flow, `ecm_cycle`, Runbook-3-owner |
| „primary“ und „Candidate“ nicht kombinieren | Synthesis Domain A Strategy identity |
| „de facto“ / „kanonisch offline“ nur mit AUTH-ID + BLOCKED/OPEN Status koppeln | Matrix Current Ownership |

### 6.2 Entscheidungsfläche herstellen (fehlendes Artefakt)

| Empfehlung | Ziel |
|------------|------|
| `ssot_decision_surface_v1.md` **vor** Ratifikation anlegen — explizite Optionen-Matrix **ohne** Default-Spalte | Schließt Lücke zwischen Synthesis und Operator-Entscheid |
| Decision Surface sollte **symmetrisch** AUTH-017-Pfade (Integrated Replay **vs** Decision Packet **vs** Scenario Replay) darstellen | Gegen Integrated-Replay-Bias |
| Decision Surface sollte AUTH-001-Optionen (a/b/c) **gleichgewichtet** tabellieren — inkl. „Status quo dual surface“ | Gegen `armstrong_cycle`-Bias |

### 6.3 Reihenfolge-Entbiasung

| Empfehlung | Ziel |
|------------|------|
| W2 (Governance Decision Records) **vor** W1 (Docs markers) in Operator-Planung — oder W1 explizit als „non-decision annotations only“ labeln | Gegen Wave-order-Bias |
| Tier-0-Roots **pro Domain gleich sichtbar** halten — nicht nur AUTH-Count, sondern **Optionen-Offenheit** pro Root | Gegen Domain-B-Dichte-Bias |
| Boundary-Konflikte AUTH-016/017 in Decision Surface **dual-parent** (B + C) modellieren | Gegen B-Verankerung |

### 6.4 Schicht-Trennung explizit machen

| Dimension | Empfehlung |
|-----------|------------|
| **Operational SSOT** | Validation Rule / Runtime Core — getrennt dokumentieren |
| **Identity SSOT** | AUTH-001 — nicht aus Operational-Rule ableiten |
| **Compute SSOT** | AUTH-017 — nicht aus Class A allein ableiten |
| **Promotion/Tier SSOT** | AUTH-005/012/020 — Dual-Source Contract, nicht Registry allein |
| **Architecture SSOT** | AUTH-014 — Code-Current und Runbook-Expected **symmetrisch** |

### 6.5 Präzedenz-Isolation

| Empfehlung | Ziel |
|------------|------|
| El-Karoui Safe-Fix (DOC-09) explizit als **nicht übertragbar** auf AUTH-001 markieren — unterschiedliche Registry-Typen | Gegen Alias-Präzedenz-Bias |
| Safe Docs Fixes (A-05, DOC-06 redirects) als „directional hint only — BLOCKED“ bannern | Gegen Docs-Vorab-Alignment |

### 6.6 Snapshot-Ergänzung (beschreibend, nicht in diesem Scan ausgeführt)

| Empfehlung | Ziel |
|------------|------|
| Snapshot sollte **Bias-Warnung** tragen: „Downstream artefacts contain Candidate SSOT language — not ratified“ | Leser-Schutz |
| Runbook `CANONICAL_OWNER`-Einträge in Neutralitäts-Index aufnehmen oder explizit als „parallel non-governance authority“ markieren | Gegen versteckte Runbook-SSOT |
| Fehlendes Decision Surface im Snapshot als **blockierend für Ratifikation** vermerken | Fail-closed Governance |

### 6.7 Was **nicht** neutralisiert werden muss

| Element | Grund |
|---------|-------|
| Validation Rule NON-OPERATIONAL | Legitimes Safety-Gate — Bias nur bei **Verwechslung** mit Identity-SSOT |
| „NOT ENFORCED YET“-Spalten | Korrekte explizite Guardrails |
| Wiring Inventory non-authority boundary | Gut formuliert |
| Collapse Chains als Fail-closed-Review | Wertvoll — solange Kandidaten nicht als sole truth gelesen werden |

---

## Appendix A: Scan-Methodik

1. Vollständiges Lesen der vier referenzierten Governance-Inputs (+ Kontext Feature State Map, Drift Cleanup Plan)
2. Quersuche nach `armstrong_cycle`, `integrated_offline_trading_logic_replay_v1`, „kanonisch“, „Candidate SSOT“, „Expected Canonical“
3. Abgleich Snapshot-Neutralitätsclaims vs indexierte Artefakt-Rollen
4. Prüfung auf fehlendes `ssot_decision_surface_v1.md` (Repository-Grep: 0 Treffer)

**Kein Code gelesen** außer indirekt über Evidence-Zitate in Matrix/Synthesis. **Keine** Runtime-Inspection in diesem Scan.

---

## Appendix B: Explizite Nicht-Aktionen (dieser Report)

- Keine SSOT-Auswahl für ECM, MV2, Capital/Risk, Registry
- Keine Änderung an Matrix, Synthesis, Snapshot, Feature State Map
- Keine Wave-/Tier-Reihenfolge-Umsetzung
- Keine Registry-, Config- oder Runtime-Mutation

**Nächster Schritt (Operator, außerhalb dieses Reports):** Decision Surface v1 erstellen **mit** Bias-Neutralisierungs-Checkliste (§6) — **bevor** Wave-2 Governance Decision Records scoped werden.

---

**Report-Owner:** SSOT Decision Hygiene Report v1  
**Evidence frozen at:** `2f1672bee8761f8d50def3f6ef31cc803824b2e9`
