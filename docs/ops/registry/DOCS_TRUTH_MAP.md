# DOCS_TRUTH_MAP — Zweck (Slice A)

**Status:** Slice A — maschinenlesbares Mapping + lokaler Drift-Check  
**Konfiguration:** `config/ops/docs_truth_map.yaml`  
**Skript:** `scripts/ops/check_docs_drift_guard.py`

## Zweck

Einige **sensible Code- und Dokumentationspfade** (Execution, Orders, Environment, zentrale Governance-/Limitations-Docs) sollen nicht **still** von den **kanonischen Beschreibungen** im Repo abdriften.

Dieses Mapping verknüpft **Bereiche** (Triggers) mit **Canonical-Docs** (mindestens eine Datei aus der Liste muss bei einer Änderung im Bereich mitgeändert werden — im selben Diff gegenüber dem gewählten Basis-Ref, z. B. `origin&#47;main`).

## Wie das Mapping funktioniert

1. Regeln stehen in `config/ops/docs_truth_map.yaml` (`rules[]`).
2. Jede Regel hat `sensitive` (Pfade) und `required_docs` (Pfadliste).
3. Das Skript ermittelt geänderte Dateien via `git diff <base>...HEAD` und prüft pro Regel:  
   **Wenn** mindestens ein `sensitive`-Pfad geändert wurde **und** **keine** der `required_docs` geändert wurde → **Fehler** (Exit 1).

Pfad-Matching:

- Endet ein Eintrag in `sensitive` mit `/`, gelten alle Repo-relativen Pfade **unter** diesem Präfix.
- Sonst exakter Pfad.

## Was das nicht leistet

- **Kein** Beweis, dass die Doku inhaltlich korrekt ist — nur dass **bewusst** mindestens eine referenzierte Canonical-Datei mitaktualisiert wurde.
- **Keine** semantische Prüfung, kein LLM.
- **Kein** Ersatz für Review, Governance oder Operator-Urteil.

## Betrieb

```bash
python3 scripts/ops/check_docs_drift_guard.py --base origin/main
```

Vor dem ersten Lauf: `git fetch origin` sinnvoll, damit `origin&#47;main` existiert.
