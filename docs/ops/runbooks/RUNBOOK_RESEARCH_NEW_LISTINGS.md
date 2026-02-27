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
- reproduzierbarer Output unter `out/research/new_listings/`

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
