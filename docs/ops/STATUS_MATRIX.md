# Status Matrix Contract

## Motivation

Dieses Projekt unterscheidet strikt zwischen:
- **Vorhanden** (Config/Stub/Code vorhanden)
- **Wirksam** (Enforcement in Runtime + Tests/Checks belegen das)

Dokumentation darf **keine** impliziten Aussagen machen ("ist implementiert"), wenn nur Config/Stub existiert.

## Status-Werte (normativ)

- `planned`   – geplant, noch nicht im Repo oder nur als TODO/Issue referenziert
- `stub`      – Interface/Config existiert, Verhalten ist Platzhalter oder NO-OP
- `configured`– Config/Parametrisierung existiert, aber Enforcement/Runtime-Pfad nicht belegt
- `implemented` – Codepfad existiert und ist grundsätzlich lauffähig (ohne harten Nachweis)
- `enforced`  – wirksam: durch Tests/Checks/Evidence nachgewiesen (Block/Allow/Fail-Fast)
- `legacy`    – historisch vorhanden, wird nicht weiterentwickelt, nur kompat gehalten
- `optional`  – absichtlich nicht default-aktiv; muss explizit aktiviert werden

## Evidence-Level (normativ)

Evidence-Level beschreibt die Stärke des Nachweises:
- `E0` – Repo-Artefakt existiert (Config/Stub/Code), keine Ausführung
- `E1` – Unit-Test beweist Claim
- `E2` – Integration/Smoke beweist Claim (lokal oder CI)
- `E3` – CI Gate/Workflow erzwingt Claim
- `E4` – Runtime/Prod Monitoring/Alerting belegt Claim (nur wenn relevant)

## Tabellen-Contract (für Übersichten)

Jede Gate-/Datenfluss-Tabelle nutzt mindestens diese Spalten:
- `component` (Name)
- `scope` (z. B. L0–L6 / subsystem)
- `claim` (konkrete Aussage)
- `status` (aus obiger Liste)
- `evidence` (Link/Path auf Evidence Pack oder Tests)
- `notes` (Risiko, TODO, Owner, Deps)

## Sprache/Claims

Verbotene Formulierungen ohne `enforced` + Evidence:
- "ist sicher", "verhindert zuverlässig", "hart geblockt" (ohne E1+)

Erlaubte Formulierungen:
- "`stub`: Interface vorhanden, Verhalten NO-OP"
- "`configured`: Config vorhanden, Enforcement noch offen"
- "`enforced`: durch Test XYZ + Evidence ABC nachgewiesen"
