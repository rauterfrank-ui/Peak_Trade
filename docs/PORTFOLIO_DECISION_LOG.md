# Peak_Trade – Portfolio Decision Log

Dieses Dokument ist das zentrale Log für **Go/No-Go-Entscheidungen** rund um Portfolio-Presets (Research → Shadow → Testnet → Live).

## Verwendung

- Pro Portfolio-Preset **ein Eintrag pro Entscheidung** (z.B. „PROMOTE_TO_SHADOW“, „REVISE“, „REJECT“).
- Verweise auf die **konkreten Report-Pfade** (Research/Robustness/Status), damit Entscheidungen später reproduzierbar sind.
- Wenn du Anpassungen vornimmst, dokumentiere kurz **was** und **warum** (Parameter-/Konfig-Änderungen) und verlinke auf die neue Report-Generation.

## Report-Erzeugung (Copy/Paste)

> **Hinweis:** Die `--format`-Enums sind je Script unterschiedlich:
> - `scripts/research_cli.py` (Portfolio): `md|html|both`
> - `scripts/generate_live_status_report.py`: `markdown|html|both`

### Research (Portfolio-Report)

```bash
python3 scripts/research_cli.py portfolio \
  --config config/config.toml \
  --portfolio-preset <preset_id> \
  --format both
```

### Portfolio-Robustness (MC + Stress)

```bash
python3 scripts/run_portfolio_robustness.py \
  --config config/config.toml \
  --portfolio-preset <preset_id> \
  --format both
```

> Wenn das Preset/Recipe im Phase-53-Format `strategies=[...]` arbeitet, nutze zusätzlich `--use-dummy-data`.

### Live-/Testnet-Status (Phase 57)

```bash
python3 scripts/generate_live_status_report.py \
  --config config/config.toml \
  --output-dir reports/live_status \
  --format both \
  --tag <tag>
```

## Template (kopieren)

```markdown
## Portfolio: <preset_id>
**Datum:** YYYY-MM-DD
**Preset:** <preset_id>
**Risk-Profil:** <conservative|moderate|aggressive|...>

### Kern-Metriken
- Sharpe (OOS): <value>
- Max Drawdown: <value>
- Stress-Test (Crash): <value>
- Monte-Carlo (95% CI): Sharpe <low> - <high>

### Entscheidung
**Status:** <REJECT|REVISE|PROMOTE_TO_SHADOW|PROMOTE_TO_TESTNET|PROMOTE_TO_LIVE>

**Begründung:**
- <bullet>

### Nächste Schritte
1. <step>

### Reports
- Portfolio-Robustness-Report: `<path>`
- Research-Pipeline-Report: `<path>`
- (optional) Live-/Testnet-Status-Report: `<path>`

### Notes / Änderungen (falls relevant)
- <what changed, why>
```

---

## Einträge

<!-- Neue Einträge oben einfügen. -->
