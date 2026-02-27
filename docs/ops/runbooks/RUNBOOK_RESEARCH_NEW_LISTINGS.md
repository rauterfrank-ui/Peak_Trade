# RUNBOOK – Research New Listings

## Ziel
`src/research/new_listings/` als kontrollierten Research-Baustein nutzbar machen.

## Status
Aktivierungswelle 1 – minimaler Entrypoint + Smoke-Test + Output-Kontrakt.

## Geplanter Einstieg
- Python-Modul-Entrypoint
- Make-Target
- Smoke-Test

## Guardrails
- offline / local-first
- kein Live-/Order-Hook
- reproduzierbarer Output unter `out&#47;research&#47;new_listings&#47;`

## Nächste Integrationsstufe
- Registry/Evidence-Anbindung
- optional Shadow-Pipeline-Export

## Aktueller CLI-Status
Vorhanden:
- `python -m src.research.new_listings --help`
- `python -m src.research.new_listings run --help`

Subcommands:
- `init`
- `collect`
- `normalize`
- `risk`
- `score`
- `export`
- `run`

## Smoke-Check
```bash
make research-new-listings-smoke
```

## Pass 2 – deterministischer Run-Smoketest
Fixture:
- `tests/fixtures/research/new_listings/config.json` (collectors: manual_seed)
- `tests/fixtures/research/new_listings/manual_seed.json` (Beispieldaten)

Ziel:
- `run` nicht nur per `--help`, sondern mit testbarem Input/Output-Pfad ausführbar machen
- Output deterministisch unter temporärem oder stabilem Verzeichnis prüfen

```bash
pytest tests/research/test_new_listings_run_smoke.py -v
make research-new-listings-run-smoke
```
