# CI Pragmatic Flow — PR Gate (Single Required Check)

**Canonical reference:** [GATES_OVERVIEW.md](GATES_OVERVIEW.md) ist SSoT für Gates. Dieses Doc beschreibt PR-Gate-Details.

**Ziel:** Für Branch Protection nur **einen** Required Check: **PR Gate**.  
- Reine Docs/Workflow-Änderungen: nur Fast-Lane + Smoke (keine volle Py-Matrix).  
- Code-Änderungen: volle Python-Matrix (3.9/3.10/3.11) + strategy-smoke.

## Required Check = PR Gate

In **GitHub → Settings → Branches → Branch protection rules → main → Required status checks** nur eintragen:

| Check-Name | Quelle |
|------------|--------|
| **PR Gate** | `.github/workflows/ci.yml` Job `pr-gate` |

Matrix läuft nur bei Code-Änderungen (siehe Pfad-Logik). Lint Gate, Docs Gates, CI Health Gate laufen weiter in eigenen Workflows, sind aber nicht als required eingetragen (nur PR Gate).

## Pfad-Logik (paths-filter)

| Output | Bedeutung | Bedingung |
|--------|-----------|-----------|
| `run_fast` / `run_fast_lane` | immer `true` | — |
| `run_matrix` | volle Matrix | Code-Pfade geändert (oder `workflow_dispatch` mit `force_matrix=true`) |
| `docs_only` | nur Fast-Lane nötig | **Nur** `docs&#47;**`, `out&#47;**`, `**&#47;*.md` |
| `workflow_only` | nur Fast-Lane nötig | **Nur** `.github&#47;workflows&#47;**` |

**Code-Pfade** (run_matrix): `src&#47;**`, `tests&#47;**`, `scripts&#47;**`, `config&#47;**`, `requirements*.txt`, `pyproject.toml`, `uv.lock`, `pytest.ini`, `Makefile`.  
`.github&#47;workflows&#47;**` zählt **nicht** zu Code (workflow-only → kein Matrix).

## Beispiel-Pfade → welche Jobs laufen

| Geänderte Pfade (nur diese) | run_matrix | Laufende Jobs (relevant) |
|-----------------------------|------------|---------------------------|
| `docs&#47;foo.md` | false | changes, Fast-Lane, tests (skip), strategy-smoke (skip), **PR Gate** |
| `.github&#47;workflows&#47;lint.yml` | false | wie oben |
| `src&#47;foo.py` | true | changes, Fast-Lane, **tests (3.9/3.10/3.11)**, **strategy-smoke**, **PR Gate** |
| `tests&#47;test_baz.py`, `scripts&#47;obs&#47;build_foo.py`, `pyproject.toml`, `uv.lock`, `requirements.txt` | true | wie oben |

## workflow_dispatch: Matrix erzwingen

CI → "Run workflow" → Input **force_matrix** (boolean): bei `true` wird `run_matrix=true` gesetzt (volle Matrix unabhängig von Pfaden).

## Abhängigkeiten

- **PR Gate** benötigt: `changes`, `fast-lane`, `tests`, `strategy-smoke`.
- **tests** / **strategy-smoke**: werden immer erstellt; bei `code_changed != true` nur Skip-Step (kein job-level `if`).

## Lokal (vor Push)

**Fast-Lane:** `ruff format --check .` → `ruff check .` → `pytest -q -m smoke -x 2>&#47;dev&#47;null \|\| pytest -q -x tests&#47;obs&#47;`  
**Matrix (bei Code-Change):** `pytest -q`

## Konfiguration

- `config/ci/required_status_checks.json`: `required_contexts: ["PR Gate"]`.
- Hygiene-Validator: `scripts&#47;ci/validate_required_checks_hygiene.py`.
- Inventar: `docs/ops/ci_pragmatic_flow_inventory.md`.

Stand: 2026-02-07
