# RUNBOOK – Wave 4 Hook / Contract Integration

## Ziel
Die aktivierten Layer über gemeinsame Artefaktverträge und leichte Hook-Punkte verbinden.

## Fokus
- gemeinsamer JSON-Contract
- strukturierte Smoke-Artefakte
- später Aggregator / Summary

## Reihenfolge
1. Contract
2. Tests
3. Aggregator
4. optionale Hook-Dokumentation

## Pass 1 – Gemeinsamer Minimal-Contract
Alle Smoke-Artefakte tragen jetzt gemeinsame Pflichtfelder:
- `contract_version`
- `status`
- `component`
- `run_id`
- `timestamp`
- `summary`

Ziel:
- gleiche Prüfoberfläche für spätere Aggregation
- kein Verlust der fachspezifischen Felder
