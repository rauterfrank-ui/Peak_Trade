# PR-Body (Copy-Paste für Pragmatic-Flow-PR)

## Motivation

Ein einziger Required Check (PR Gate) für Branch Protection; bei Docs/Grafana/Workflow-only PRs läuft nur Fast-Lane (keine volle Py-Matrix). Reduziert Wartezeit und vereinheitlicht Merge-Gate.

## Pragmatischer CI-Flow

- **Reine Grafana/Docs/Workflow-Änderungen** → nur Fast-Lane/Smoke (+ Lint/Docs-Gates in eigenen Workflows), **keine** volle Py-Matrix.
- **Code-Änderungen** → volle Py-Matrix (3.9/3.10/3.11) + strategy-smoke wie bisher.

## Beispiele (Dateipfade → welche Jobs)

| Geänderte Pfade | run_matrix | Jobs |
|-----------------|------------|------|
| `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;...&#47;foo.json` | false | nur Fast-Lane (+ PR Gate) |
| `docs&#47;foo.md`, `README.md` (nur Docs) | false | nur Fast-Lane |
| `.github&#47;workflows&#47;...` | false | Fast-Lane + workflow checks |
| `src&#47;...`, `tests&#47;...`, `scripts&#47;...`, `pyproject.toml`, `uv.lock`, `requirements.txt` | true | volle Matrix |

## Required Check (Branch Protection)

**Einziger required check:** **PR Gate**  
(Alle anderen Checks laufen weiter, sind aber nicht als required eingetragen.)

## Änderungen

- `.github/workflows/ci.yml`: changes (run_fast, run_matrix, docs_only, workflow_only, force_matrix), Fast-Lane, PR Gate (umbenannt von Meta-Gate), workflow_dispatch mit `force_matrix`.
- `config/ci/required_status_checks.json`: `required_contexts: ["PR Gate"]`.
- Docs: `docs/ops/ci_pragmatic_flow_meta_gate.md`, `ci_pragmatic_flow_inventory.md`, kurzer Hinweis in `docs/ops/README.md`.

## Rollout (Branch Protection)

Nach Merge: In GitHub → Settings → Branches → main → Required status checks nur **PR Gate** eintragen (bestehende andere required checks entfernen oder durch PR Gate ersetzen, je nach Policy).
