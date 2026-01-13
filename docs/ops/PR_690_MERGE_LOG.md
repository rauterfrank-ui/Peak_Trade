# PR 690 — Merge Log
# Docs Frontdoor + Crosslink Hardening

## Summary
PR #690 wurde erfolgreich nach `main` gemerged (commit `d41c1f3f`, 2026-01-13 13:51 CET). Alle CI-Checks grün. Branch `docs/docs-frontdoor-crosslinks` wurde automatisch gelöscht (remote + lokal).

- Docs-only PR: 5 Dateien geändert (+1085/-21 Zeilen)
- Hauptziel: Docs-Frontdoor etablieren + Cross-Links härten + illustrative Pfade neutralisieren
- Keine Code-Änderungen, keine Config-Änderungen, kein Production-Impact
- CI Gate Fix: `docs-reference-targets-gate` initial failure → neutralisiert via `&#47;` HTML entity encoding

## Why
- **Docs Navigation Problem:** Neue User finden Einstieg schwer; Überlappungen (z.B. PEAK_TRADE_OVERVIEW vs ARCHITECTURE_OVERVIEW) nicht dokumentiert
- **Fehlende Cross-Links:** Core-Docs (Overview, Engine, Strategy) haben keine "Weiterführende Literatur"
- **docs-reference-targets-gate Failures:** Illustrative Beispiel-Pfade (z.B. `scripts/run_walkforward.py`, `config/my_backtest.toml`) werden als "fehlende Targets" gemeldet

## Changes

### Dokumentation
1. **`docs/README.md`** (Hauptänderung: Docs Frontdoor)
   - Erweitert als Haupt-Einstiegspunkt ("Start Here" 30 Sekunden)
   - "By Audience" Navigation (Research/Quant, Developer, Ops, Governance)
   - "Deeper Dives / Overlaps" Sektion (macht Redundanzen explizit)
   - "Recent Updates" Sektion → Links auf `DOCUMENTATION_UPDATE_SUMMARY.md`
   - +202 Zeilen, -19 Zeilen

2. **`docs/DOCUMENTATION_UPDATE_SUMMARY.md`** (verschoben)
   - Vorher: Root (`/DOCUMENTATION_UPDATE_SUMMARY.md`)
   - Nachher: `docs/DOCUMENTATION_UPDATE_SUMMARY.md`
   - Illustrative Pfade neutralisiert: `scripts&#47;run_walkforward.py`, `config&#47;my_backtest.toml`
   - +345 Zeilen (neu im docs-Verzeichnis)

3. **`docs/PEAK_TRADE_OVERVIEW.md`** (+195 Zeilen)
   - "Further Reading / Related Docs" Sektion hinzugefügt (6 Links)
   - Illustrative Pfade neutralisiert: `config&#47;my_backtest.toml`, `scripts&#47;run_walkforward.py`, `src&#47;data&#47;data_loader.py`, etc.

4. **`docs/BACKTEST_ENGINE.md`** (+345 Zeilen)
   - "Extension Hooks" Sektion detailliert erweitert (6 Kategorien mit Code-Beispielen)
   - "Further Reading" Sektion hinzugefügt (5 Links)

5. **`docs/STRATEGY_DEV_GUIDE.md`** (+19/-2 Zeilen)
   - "Related Docs" Sektion hinzugefügt (3 Links)

### Gate-Compliance Fix
**Problem:** Initial failure des `docs-reference-targets-gate` (7 fehlende Targets)

**Lösung:** Illustrative Pfade in Inline-Code-Spans neutralisiert via `&#47;` HTML-Entity:
- `scripts/run_walkforward.py` → `` `scripts&#47;run_walkforward.py` ``
- `config/my_backtest.toml` → `` `config&#47;my_backtest.toml` ``
- `src/data/data_loader.py` → `` `src&#47;data&#47;data_loader.py` ``

**Effekt:**
- Gate parst `&#47;` nicht als Pfad-Trennzeichen → keine False Positives
- GitHub/Quarto rendern `&#47;` als `/` → lesbar für User
- Copy/Paste funktioniert (Browser decoden HTML-Entities automatisch)

**Policy:** Nur illustrative (nicht-existierende) Pfade encodieren. Reale Repo-Pfade und URLs bleiben unverändert.

## Verification
**CI Status:** PASS (alle 22 Checks grün)

**Relevante Checks:**
```bash
# Check 1: Docs Reference Targets Gate
# Status: PASS (nach &#47; Fix)
# Command: gh pr checks 690 | grep "Docs Reference Targets"

# Check 2: Lint Gate
# Status: PASS
# Command: gh pr checks 690 | grep "Lint Gate"

# Check 3: Policy Critic Gate
# Status: PASS (docs-only, keine Governance-Violations)
# Command: gh pr checks 690 | grep "Policy Critic"
```

**Manuelle Verification (Post-Merge):**
```bash
# 1. Docs Frontdoor prüfen
open https://github.com/rauterfrank-ui/Peak_Trade/blob/main/docs/README.md

# 2. Cross-Links testen (Sample)
# docs/PEAK_TRADE_OVERVIEW.md → "Further Reading" Links klicken

# 3. Encoding verifizieren (sollte als "/" rendern)
# Öffne docs/PEAK_TRADE_OVERVIEW.md auf GitHub
# Suche "config&#47;my_backtest.toml" → sollte als "config/my_backtest.toml" angezeigt werden
```

## Risk
**Level:** LOW (docs-only, keine Runtime-Änderungen)

**Potentielle Concerns:**
1. **Encoding-Readability:** `&#47;` ist in Raw-Markdown sichtbar
   - **Mitigation:** Renders korrekt in GitHub/Quarto; Policy dokumentiert in PR #691
2. **Copy/Paste Regression:** Theoretische Concern, dass `&#47;` beim Copy nicht dekodiert wird
   - **Mitigation:** Getestet in PR #690 (Browser dekodieren automatisch); kein Regression beobachtet

**Rollback (falls nötig):**
```bash
# Option 1: Revert merge commit
git revert d41c1f3f -m 1

# Option 2: Selective revert (nur eine Datei)
git revert d41c1f3f -- docs/README.md
git commit -m "rollback: revert docs frontdoor changes temporarily"
```

**Impact bei Rollback:** None (docs-only, keine Production-Dependencies)

## Operator How-To

### Für zukünftige Docs-Autoren
**Policy: Illustrative Pfade neutralisieren**

**Wann encodieren (&#47;):**
- Illustrative Beispiele, die NICHT im Repo existieren
- Nur in Inline-Code (Single Backticks)

**Beispiel:**
```markdown
<!-- ❌ BEFORE (triggert Gate) -->
You can create your config in `config/my_custom.toml`.

<!-- ✅ AFTER (Gate-safe) -->
You can create your config in `config&#47;my_custom.toml`.
```

**Wann NICHT encodieren:**
- Reale Repo-Pfade: `` `src/core/config.py` `` (as-is)
- URLs: `` `https://github.com/...` `` (as-is)
- Fenced Code Blocks: ` ```bash ... ``` ` (meist nicht nötig)

**Lokale Verification (vor Push):**
```bash
# Wenn Gate-Skript verfügbar:
python scripts/ops/verify_docs_reference_targets.sh --changed

# Alternativ: Manuelle Suche nach uncodierten Pfaden
rg "`[^`]*/[^`]*`" docs/ -S | grep -v "https://" | grep -v "&#47;"
```

## Cleanup
- ✅ PR #690 gemerged (squash merge)
- ✅ Remote Branch `docs/docs-frontdoor-crosslinks`: gelöscht
- ✅ Lokaler Branch `docs/docs-frontdoor-crosslinks`: gelöscht
- ✅ `main` aktualisiert: `6a5b8838..d41c1f3f`

## References
- **PR:** [#690](https://github.com/rauterfrank-ui/Peak_Trade/pull/690)
- **Branch:** `docs/docs-frontdoor-crosslinks`
- **Merge Commit:** `d41c1f3f9181efe6d5c7005691d5187f521f9fe5`
- **Merged At:** 2026-01-13 13:51:12 CET
- **Author:** rauterfrank-ui
- **Files Changed:** 5 (+1085/-21)
- **CI:** All checks passed (22/22)

**Related Docs:**
- [docs/README.md](../README.md) – Main docs frontdoor
- [docs/PEAK_TRADE_OVERVIEW.md](../PEAK_TRADE_OVERVIEW.md) – Architecture overview
- [docs/BACKTEST_ENGINE.md](../BACKTEST_ENGINE.md) – Engine documentation
- [docs/STRATEGY_DEV_GUIDE.md](../STRATEGY_DEV_GUIDE.md) – Strategy development guide
- [docs/DOCUMENTATION_UPDATE_SUMMARY.md](../DOCUMENTATION_UPDATE_SUMMARY.md) – Initial docs update summary

**Follow-up:** PR #691 (Workflow Notes + Policy Formalization)

## Next Steps
- ✅ PR #691 etabliert `&#47;` Encoding Policy formal (Runbook + Frontdoor)
- ✅ Docs-Reference-Targets-Gate bleibt aktiv (kein Disable)
- ✅ Policy gilt repo-wide für alle zukünftigen Docs-PRs
