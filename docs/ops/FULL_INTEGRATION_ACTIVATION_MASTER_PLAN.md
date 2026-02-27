# Full Integration Activation Master Plan

## Ziel
Alle relevanten Layer so integrieren, dass Implementierung, Entrypoints, Tests, Workflows, Docker, Docs und Runbooks konsistent zusammenspielen.

## Statusüberblick
- **implementiert_getestet**: 164
- **isoliert**: 278
- **operationalisiert**: 225
- **referenziert_ohne_entrypoint**: 35
- **unklar**: 101

## Layer-Übersicht
### research (35)
- isoliert: 27
- unklar: 8

### ai (13)
- implementiert_getestet: 4
- isoliert: 6
- referenziert_ohne_entrypoint: 2
- unklar: 1

### ai_orchestration (31)
- implementiert_getestet: 6
- isoliert: 7
- operationalisiert: 13
- referenziert_ohne_entrypoint: 1
- unklar: 4

### observability (14)
- implementiert_getestet: 5
- isoliert: 4
- operationalisiert: 4
- unklar: 1

### execution (132)
- implementiert_getestet: 39
- isoliert: 39
- operationalisiert: 29
- referenziert_ohne_entrypoint: 6
- unklar: 19

### other (578)
- implementiert_getestet: 110
- isoliert: 195
- operationalisiert: 179
- referenziert_ohne_entrypoint: 26
- unklar: 68

## Aktivierungsprinzipien
- keine Blindverkabelung
- pro Bereich: Contract -> Entrypoint -> Test -> Doku -> Workflow
- Research-Module erst aktivieren, wenn klarer Nutzenpfad definiert ist
- Operationalisierung bevorzugt über Make/CLI/Script + Tests + Runbook

## Empfohlene Waves
1. Research-Orphans (insb. new_listings)
2. AI-Layer ohne Entrypoints
3. Observability-/Execution-Nebenpfade ohne Runtime-Hook
4. Workflow-/Runbook-Abgleich
