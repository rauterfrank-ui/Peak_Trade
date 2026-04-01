# Truth Core — gemeinsame Schicht (Slice B)

**Status:** Slice B — gemeinsames Python-Modul für deterministische Checks  
**Modul:** `src/ops/truth/`  
**Konfigurationen:**

- `config/ops/docs_truth_map.yaml` — sensible Pfade → erforderliche Canonical-Docs (Diff gegen Basis-Ref)
- `config/ops/repo_truth_claims.yaml` — deklarative Repo-Claims (z. B. Pfad-Existenz)

**Skripte:**

- `scripts/ops/check_docs_drift_guard.py`
- `scripts/ops/check_repo_truth_claims.py`

## Zweck

Docs Drift Guard und Repo Truth Claims nutzen dieselbe **Truth-Schicht**: Loader, Ergebnisobjekte (`PASS` / `FAIL` / `UNKNOWN`) und Evaluatoren ohne GitHub-API und ohne Officer-Logik. Workflow Officer und Update Officer können später dieselben APIs importieren (`from ops.truth import …`).

## Komponenten

| Datei | Rolle |
| --- | --- |
| `models.py` | `TruthStatus`, strukturierte Ergebnisse (`DocsDriftEvaluationResult`, `RepoTruthEvaluationResult`, …) |
| `loaders.py` | YAML laden (`load_docs_truth_map`, `load_repo_truth_claims`) |
| `evaluator.py` | `evaluate_docs_drift`, `evaluate_repo_truth_claims` |
| `git_refs.py` | `git_changed_files_three_dot` für den Drei-Punkt-Diff vs. Basis-Ref |

## Exit-Codes (Skripte)

**Docs Drift Guard:** `0` OK · `1` Drift · `2` Konfiguration/Git-Fehler  

**Repo Truth Claims:** `0` alle PASS · `1` mindestens ein FAIL · `2` Ladefehler oder aggregiertes UNKNOWN (z. B. unbekannte `check`-Art)

## Betrieb (Beispiele)

```bash
python3 scripts/ops/check_docs_drift_guard.py --base origin/main
python3 scripts/ops/check_repo_truth_claims.py
```

Vor Drift-Checks: `git fetch origin`, damit die Basis-Ref (z. B. `origin&#47;main`) existiert.

## CI (GitHub — Pull Requests)

Workflow: `.github/workflows/truth_gates_pr.yml`.  
Stabile Check-Namen für Branch-Protection / Required Contexts: **`docs-drift-guard`**, **`repo-truth-claims`**.

## Nicht in Scope (Slice B)

- CI-Workflow-Umbau
- Semantische oder LLM-basierte Wahrheitsprüfung
- Vollständige Einbindung in Workflow/Update Officer (nur API-Vorbereitung)
