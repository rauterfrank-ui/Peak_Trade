# PR-Body (Copy-Paste für Pragmatic-Flow-PR)


<!-- ci pragmatic pr body staleness scope note -->
> Scope note: This document describes pragmatic PR-body flow context and should not be read as the sole canonical source for the current required PR checks.
> For the current gate catalog and branch-protection view, use `docs&#47;ops&#47;GATES_OVERVIEW.md`, `docs&#47;ops&#47;CI.md`, and `config&#47;ci&#47;required_status_checks.json`.

**Canonical reference:** [GATES_OVERVIEW.md](GATES_OVERVIEW.md) ist SSoT für Gates. Siehe auch [ci_pragmatic_flow_inventory.md](ci_pragmatic_flow_inventory.md), [ci_pragmatic_flow_meta_gate.md](ci_pragmatic_flow_meta_gate.md).

## Motivation

Historischer Pragmatic-Flow-Kontext: bei Docs/Grafana/Workflow-only PRs lief nur Fast-Lane (keine volle Py-Matrix), bei Code-Änderungen die volle Matrix.
Für aktuelle Required-Checks-Verträge ist JSON-SSOT maßgeblich (`config/ci/required_status_checks.json`, effective required contexts).

## Pragmatischer CI-Flow

- **Reine Grafana/Docs/Workflow-Änderungen** → nur Fast-Lane/Smoke (+ Lint/Docs-Gates in eigenen Workflows), **keine** volle Py-Matrix.
- **Code-Änderungen** → volle Py-Matrix (3.9/3.10/3.11) + strategy-smoke wie bisher.

## Beispiele (Dateipfade → welche Jobs)

| Geänderte Pfade | run_matrix | Jobs |
|-----------------|------------|------|
| `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;...&#47;foo.json` | false | nur Fast-Lane (+ PR Gate) | <!-- pt:ref-target-ignore -->
| `docs&#47;foo.md`, `README.md` (nur Docs) | false | nur Fast-Lane | <!-- pt:ref-target-ignore -->
| `.github&#47;workflows&#47;...` | false | Fast-Lane + workflow checks |
| `src&#47;...`, `tests&#47;...`, `scripts&#47;...`, `pyproject.toml`, `uv.lock`, `requirements.txt` | true | volle Matrix |

## Required Checks (SSOT)

Kanonisch ist `config/ci/required_status_checks.json` mit
`effective_required_contexts = required_contexts - ignored_contexts`.

## Änderungen

- `.github/workflows/ci.yml`: changes (run_fast, run_matrix, docs_only, workflow_only, force_matrix), Fast-Lane, PR Gate (umbenannt von Meta-Gate), workflow_dispatch mit `force_matrix`.
- `config/ci/required_status_checks.json`: SSOT für required/ignored contexts.
- Docs: `docs/ops/ci_pragmatic_flow_meta_gate.md`, `ci_pragmatic_flow_inventory.md`, kurzer Hinweis in `docs/ops/README.md`.

## Rollout (Branch Protection)

Branch-Protection-Rollout folgt der JSON-SSOT-Konfiguration und der aktuellen Ruleset-Policy;
keine separate PR-Gate-only-Anweisung.
