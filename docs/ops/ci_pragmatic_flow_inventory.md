# CI Pragmatic Flow — Inventar (Workflows & Jobs)

**Stand:** 2026-02-07. Branch Protection: nur **PR Gate** als required check (TODO: in GitHub einstellen).

## Relevante Workflows und Jobs

| Workflow | Job(s) | Kontext-Name (für Branch Protection) | Derzeit required? |
|----------|--------|--------------------------------------|-------------------|
| `.github/workflows/ci.yml` | changes | (kein eigener Check) | — |
| | fast-lane | **Fast-Lane** | nein |
| | tests | **tests (3.9)**, **tests (3.10)**, **tests (3.11)** | nein (nur PR Gate) |
| | strategy-smoke | **strategy-smoke** | nein |
| | pr-gate | **PR Gate** | **ja (einziger)** |
| `.github/workflows/lint_gate.yml` | lint-gate | **Lint Gate** | nein |
| `.github/workflows/docs-token-policy-gate.yml` | (job) | **docs-token-policy-gate** | nein |
| `.github/workflows/docs_reference_targets_gate.yml` | (job) | **docs-reference-targets-gate** | nein |
| `.github/workflows/test_health.yml` | ci-health-gate | **CI Health Gate (weekly_core)** | nein |

**Branch Protection (main):** Nur **PR Gate** als required eintragen. Lint/Docs/CI Health laufen weiter, blockieren Merge aber nur indirekt, wenn sie in anderen Rulesets gefordert sind.

## Change-Classification (Outputs vom `changes`-Job)

| Output | Bedeutung |
|--------|-----------|
| `run_matrix` | true → volle Py-Matrix (tests 3.9/3.10/3.11, strategy-smoke) laufen |
| `run_fast` / `run_fast_lane` | immer true → Fast-Lane läuft immer |
| `docs_only` | true → nur docs/grafana/out/md geändert |
| `workflow_only` | true → nur .github/workflows geändert |

- **Code-Änderungen** (run_matrix): `src/**`, `tests/**`, `scripts/**`, `config/**`, `pyproject.toml`, `uv.lock`, `requirements*.txt`, `pytest.ini`, `Makefile`.
- **Docs/Grafana-only:** `docs/**`, `**/grafana/dashboards/**`, `out/**`, `**/*.md`.
- **Workflow-only:** `.github/workflows/**`.

## Beispiel-Pfade → welche Jobs

| Geänderte Pfade | run_matrix | Laufende CI-Jobs (relevant) |
|-----------------|------------|-----------------------------|
| `docs/webui/observability/grafana/dashboards/overview/foo.json` | false | changes, Fast-Lane, tests (skip), strategy-smoke (skip), **PR Gate** |
| `docs/foo.md` | false | wie oben |
| `.github/workflows/lint.yml` | false | wie oben (+ Lint Gate, Docs Gates in eigenen Workflows) |
| `src/foo.py` | true | changes, Fast-Lane, **tests (3.9/3.10/3.11)**, **strategy-smoke**, **PR Gate** |
| `tests/test_x.py`, `scripts/bar.py`, `pyproject.toml`, `uv.lock`, `requirements.txt` | true | wie oben |

## workflow_dispatch: Matrix erzwingen

- **CI** → "Run workflow" → Input **force_matrix** (boolean): bei `true` wird `run_matrix=true` gesetzt (volle Matrix läuft unabhängig von Pfaden).

## Simulation (expected job outcomes)

**Case A (docs-only):** e.g. only `docs/foo.md` or `docs/webui/observability/grafana/dashboards/overview/bar.json` changed.  
- Expected jobs: changes + Fast-Lane + PR Gate; tests + strategy-smoke run but **SKIP** (step-level) and still **pass**.  
- PR Gate: SUCCESS after Fast-Lane passes and tests/strategy-smoke report success (skip step).

**Case B (code change):** e.g. `src/foo.py` or `tests/test_x.py` or `pyproject.toml` changed.  
- Expected jobs: changes + Fast-Lane + **tests (3.9)** + **tests (3.10)** + **tests (3.11)** + strategy-smoke + PR Gate.  
- All run (no skip). PR Gate: SUCCESS only if Fast-Lane + all tests + strategy-smoke pass.

**Case C (workflow-only):** e.g. only `.github/workflows/lint.yml` changed.  
- Expected jobs: changes + Fast-Lane + PR Gate; tests/strategy-smoke **SKIP** (same as Case A).  
- Lint Gate / workflow-related checks run in their own workflows. PR Gate: SUCCESS after Fast-Lane + skip pass.
