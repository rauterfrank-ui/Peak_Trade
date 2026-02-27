# Wave 4 – Hook / Contract Integration Plan

## Ziel
Von isolierten Smoke-Oberflächen zu ersten bewusst verbundenen Verträgen und Hook-Punkten übergehen.

## Pass 1
- shared smoke contract definieren
- Hook-Map definieren
- kleinsten gemeinsamen Felderkatalog festlegen

## Pass 2
- Smoke-Skripte auf gemeinsamen Contract bringen
- Tests auf Contract-Felder erweitern

## Pass 3
- kleiner Aggregator / Summary-Bridge
- ein gemeinsames Summary-Artefakt unter `out&#47;ops&#47;...`

## Nicht-Ziele
- keine tiefe Runtime-Verkabelung
- keine Live-/Execution-Freigabe

## Erreichte Aktivierung (Pass 1)
- gemeinsamer Minimal-Contract in allen Smoke-Artefakten
- Pflichtfelder:
  - `contract_version`
  - `status`
  - `component`
  - `run_id`
  - `timestamp`
  - `summary`
- Contract-Test ergänzt
