# Quick Reference: Cycles #1-5

**Schnellübersicht für Operator**

---

## 🚀 Quick Start für Cycle #6

```bash
# 1. Neue Demo-Patches generieren (empfohlen)
python scripts/generate_demo_patches_for_promotion.py

# 2. Cycle starten
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only

# 3. Reports prüfen
ls -lh reports/live_promotion/
```

---

## 📊 Status nach 5 Cycles

**Meilenstein:** 🎯 **50% der Stabilisierungsphase**

| Metrik | Wert |
|--------|------|
| Cycles abgeschlossen | 5 / 10 |
| Erfolgsrate | 100% |
| Crashes | 0 |
| False-Positives | 0 |
| Technische Stabilität | ✅ 100% |
| Datenvielfalt | ⚠️ 0% (Gap) |

---

## 🎯 Operator-Entscheidung: Leverage-Patch

**Nach 5 Cycles konsistenter Empfehlung:**

```
Patch: portfolio.leverage 1.0 → 1.25
Confidence: 0.85 (hoch)
Status: 5x empfohlen

Empfohlene Aktion: CONDITIONAL GO
→ Option A: In Test-Environment übernehmen
→ Option B: Weitere 5 Cycles abwarten
→ Option C: Direkt in Live übernehmen

EMPFEHLUNG: Option A (Test-Environment)
```

---

## 📁 Wichtige Dokumente

### Für tägliche Arbeit

- **[OPERATOR_DECISION_LOG.md](./OPERATOR_DECISION_LOG.md)**
  → Vollständige Cycle-Historie mit Entscheidungen

- **[promotion_loop_review_log.md](../promotion_loop_review_log.md)**
  → Kurz-Übersicht aller Cycles

### Für tiefere Analyse

- **[STABILIZATION_PHASE_CYCLES_1_5_SUMMARY.md](./STABILIZATION_PHASE_CYCLES_1_5_SUMMARY.md)**
  → Umfassende Analyse (13 Seiten)

- **[LEARNING_PROMOTION_LOOP_INDEX.md](../LEARNING_PROMOTION_LOOP_INDEX.md)**
  → Zentrale Doku mit bounded_auto Checklist

### Für Entwickler

- **[LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md](../LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md)**
  → System-Architektur

- **[PROMOTION_LOOP_V0.md](../PROMOTION_LOOP_V0.md)**
  → Technische Details

---

## 🚀 Nächste Schritte

### Diese Woche (Cycles #6-10)

1. **Datenvielfalt erhöhen**
   - Neue Demo-Patches mit Varianz generieren
   - Grenzfälle testen (Threshold ±0.01, große Steps)

2. **Governance härter testen**
   - Bounds-Tests
   - Blacklist-Tests
   - Whitelist-Tests

3. **Dokumentation fortführen**
   - Jeden Cycle dokumentieren
   - Patterns erkennen

### Nächste Woche

4. **Learning-Loop integrieren**
   - TestHealth → ConfigPatches
   - Trigger-Training → ConfigPatches

5. **Monitoring aktivieren**
   - Slack-Integration
   - Dashboard

---

## 📋 Checklisten

### Vor jedem Cycle

- [ ] Demo-Patches aktuell? (falls Varianz gewünscht)
- [ ] Letzter Cycle dokumentiert?
- [ ] Operator-Entscheidung getroffen?

### Nach jedem Cycle

- [ ] Reports in `reports&#47;live_promotion&#47;` prüfen
- [ ] OPERATOR_CHECKLIST.md durcharbeiten
- [ ] Entscheidung in OPERATOR_DECISION_LOG.md dokumentieren
- [ ] Bei Problemen: System auf `disabled` setzen

### Nach Cycle #10

- [ ] Mini-Review durchführen
- [ ] bounded_auto Readiness evaluieren
- [ ] Nächste 5-10 Cycles planen

---

## ⚠️ Troubleshooting

**Problem:** Cycle schlägt fehl

```bash
# 1. Modus prüfen
grep "mode =" config/promotion_loop_config.toml

# 2. Demo-Patches vorhanden?
ls -lh reports/learning_snippets/demo_patches_for_promotion.json

# 3. Logs prüfen
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only 2>&1 | tee cycle_log.txt
```

**Problem:** Keine neuen Empfehlungen

→ **Erwartet:** Bei identischen Demo-Patches gibt es identische Empfehlungen
→ **Lösung:** Neue Demo-Patches generieren

**Problem:** System lehnt alles ab

→ **Prüfen:** Confidence-Scores in Demo-Patches (müssen >= 0.75 sein für Acceptance)

---

## 🎯 Key Takeaways

1. ✅ **System ist stabil** (5 Cycles ohne Fehler)
2. ✅ **Confidence-Threshold 0.75 funktioniert**
3. ⚠️ **Brauchen Datenvielfalt** (aktuell 0% Varianz)
4. 📝 **Leverage-Patch nach 5 Cycles bereit für Test-Environment**
5. 🚀 **bounded_auto frühestens nach Cycle #15-20**

---

## 📞 Quick Commands

```bash
# Neuen Cycle starten
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only

# Reports auflisten
ls -lth reports/live_promotion/ | head -5

# Letzten Report öffnen
cd reports/live_promotion/$(ls -t reports/live_promotion/ | head -1)

# Config prüfen
cat config/promotion_loop_config.toml | grep -A5 "mode ="

# Dokumentation aktualisieren
vim docs/learning_promotion/OPERATOR_DECISION_LOG.md
```

---

**Letzte Aktualisierung:** 2025-12-11  
**Version:** 1.0  
**Status:** ✅ Cycles #1-5 abgeschlossen | 🎯 50% Meilenstein erreicht
