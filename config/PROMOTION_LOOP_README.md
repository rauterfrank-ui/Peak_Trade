# Promotion Loop Konfiguration

**Version:** v1  
**Status:** Production-Ready (manual_only Modus aktiv)  
**Datum:** 2025-12-11

---

## Aktueller Status

✅ **Modus:** `manual_only` (konservativ, sicher)  
✅ **Erster Production-Cycle:** Erfolgreich durchgeführt (2025-12-11)  
✅ **Proposals generiert:** 2 Patches akzeptiert, 2 Patches abgelehnt  
⏸️ **bounded_auto:** Vorbereitet, aber NICHT aktiv

---

## Konfigurationsdateien

### `config/promotion_loop_config.toml` ⭐

Zentrale Konfigurationsdatei für das Promotion Loop System.

**Wichtigste Einstellungen:**

```toml
[promotion_loop]
mode = "manual_only"  # AKTUELL AKTIV
output_dir = "reports/live_promotion"
live_overrides_path = "config/live_overrides/auto.toml"
```

**bounded_auto Bounds (vorbereitet, nicht aktiv):**

```toml
[promotion_loop.bounds]
leverage_min = 1.0
leverage_max = 2.0
leverage_max_step = 0.25
# ... weitere Bounds siehe Datei
```

### `config/live_overrides/auto.toml`

Wird vom Promotion Loop im `bounded_auto` Modus beschrieben.

**Aktuell:** Leer (da manual_only Modus aktiv)

---

## Erster Production-Cycle (2025-12-11)

### Input

- **4 Demo-Patches** geladen aus `reports/learning_snippets/demo_patches_for_promotion.json`
- Generiert mit: `python scripts/generate_demo_patches_for_promotion.py`

### Governance-Filter

- **2 Patches akzeptiert** (confidence >= 0.75):
  - `patch_demo_001`: portfolio.leverage (1.0 → 1.25)
  - `patch_demo_002`: strategy.trigger_delay (10.0 → 8.0)
- **2 Patches abgelehnt** (zu niedrige Confidence):
  - `patch_demo_003`: macro.regime_weight (confidence: 0.72)
  - `patch_demo_004`: risk.max_position (confidence: 0.45)

### Output

```
reports/live_promotion/live_promotion_20251211T230825Z/
├── proposal_meta.json          # Metadaten
├── config_patches.json         # Detaillierte Patch-Infos
└── OPERATOR_CHECKLIST.md       # Review-Checkliste
```

### Ergebnis

✅ **Proposals generiert:** Ja  
❌ **Auto-Apply durchgeführt:** Nein (manual_only Modus)  
✅ **Safety:** Keine automatischen Änderungen

---

## Nächste Schritte

### 1. Regular manual_only Cycles (empfohlen)

```bash
# Täglich oder wöchentlich
python scripts/run_promotion_proposal_cycle.py --auto-apply-mode manual_only

# Proposals reviewen
cat reports/live_promotion/*/OPERATOR_CHECKLIST.md
```

### 2. Operator-Review der Proposals

- [ ] Prüfe `OPERATOR_CHECKLIST.md` für jede Proposal
- [ ] Verifiziere Confidence-Scores und Evidenz
- [ ] Entscheide: Go/No-Go für manuelle Anwendung
- [ ] Dokumentiere Entscheidungen

### 3. bounded_auto aktivieren (wenn bereit)

**Voraussetzungen:**

- ✅ Mehrere erfolgreiche manual_only Cycles
- ✅ Proposals wurden reviewed und als sicher eingestuft
- ✅ Monitoring ist aktiv
- ✅ Rollback-Prozedur ist getestet

**Aktivierung:**

1. Editiere `config/promotion_loop_config.toml`:
   ```toml
   mode = "bounded_auto"  # VORSICHT!
   ```

2. Test-Cycle durchführen:
   ```bash
   python scripts/run_promotion_proposal_cycle.py --auto-apply-mode bounded_auto
   ```

3. Prüfe `config/live_overrides/auto.toml` auf korrekte Werte

4. Bei Problemen sofort zurückschalten:
   ```toml
   mode = "manual_only"  # oder "disabled" für Killswitch
   ```

---

## Safety-Features

### Environment-Gating

- ✅ Auto-Overrides nur in live/testnet, NICHT in paper
- ✅ Paper-Backtests bleiben isoliert

### Bounded Auto-Apply

- ✅ Leverage: 1.0-2.0 (max_step: 0.25)
- ✅ Trigger Delay: 3.0-15.0 (max_step: 2.0)
- ✅ Macro Weight: 0.0-0.8 (max_step: 0.1)

### Governance-Firewall

- ✅ `eligible_for_live` Default: False
- ✅ Leverage Hard Limit: 3.0 (nicht überschreitbar)
- ✅ Operator-Checkliste für manuelle Review

### Graceful Degradation

- ✅ Missing patches: Keine Proposals, kein Crash
- ✅ Invalid TOML: Warning + Fallback
- ✅ Non-existent paths: Override ignoriert

---

## Monitoring

### Check Proposals

```bash
# Neueste Proposal
ls -lt reports/live_promotion/ | head -5

# Operator-Checkliste
cat reports/live_promotion/*/OPERATOR_CHECKLIST.md
```

### Check Live-Overrides

```bash
# Aktuelle Auto-Overrides (sollte leer sein im manual_only)
cat config/live_overrides/auto.toml

# Config-Diff Demo
python scripts/demo_live_overrides.py
```

### Logs

- **Promotion Cycle Output:** Console-Logs
- **Proposals:** `reports/live_promotion/<timestamp>/`
- **Learning Signals:** `reports/learning_snippets/`

---

## Troubleshooting

### Keine Patches gefunden

```bash
# Generiere Demo-Patches für Testing
python scripts/generate_demo_patches_for_promotion.py
```

### Alle Patches abgelehnt

- Prüfe Confidence-Scores (müssen >= 0.75 sein für Auto-Eligibility)
- Prüfe `eligible_for_live` Flag in Script

### bounded_auto funktioniert nicht

- Prüfe `mode` in `config/promotion_loop_config.toml`
- Prüfe dass Patches innerhalb der Bounds liegen
- Prüfe Environment (nur live/testnet)

---

## Kontakt & Support

**Dokumentation:**

- Master-Doku: `docs/LEARNING_PROMOTION_LOOP_V1_ARCHITECTURE.md`
- Index: `docs/LEARNING_PROMOTION_LOOP_INDEX.md`
- Quickstart: `docs/QUICKSTART_LIVE_OVERRIDES.md`

**Bei Fragen:**

1. Prüfe Troubleshooting-Sektion oben
2. Lese Master-Dokumentation
3. Führe Demo-Script aus: `python scripts/demo_live_overrides.py`

---

**Letzte Aktualisierung:** 2025-12-11  
**Nächster Review:** Nach 5-10 weiteren manual_only Cycles
