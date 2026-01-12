# Workflow Dispatch Guard (Phase 5C)

## Zweck

Statischer Guard zur Verhinderung von `workflow_dispatch` Regressions in GitHub Actions Workflows.

**Prüft:**
- Verwendung von `github.event.inputs.<name>` ohne Definition unter `on.workflow_dispatch.inputs`
- Referenzen auf `github.event.inputs` in Workflows ohne `workflow_dispatch` Trigger
- Versehentliche Verwendung von `inputs.<name>` (workflow_call Kontext) in workflow_dispatch Workflows

## Lokale Verwendung

```bash
# Scan aller Workflows
python3 scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows

# Mit Fail-on-Warn (strikterer Modus)
python3 scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --fail-on-warn

# Einzelne Workflow-Datei prüfen
python3 scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows/my-workflow.yml

# Mit OK-Output für Files ohne Findings
python3 scripts/ops/validate_workflow_dispatch_guards.py --paths .github/workflows --print-ok
```

## Typische Findings & Fixes

### Finding: "Referenziert github.event.inputs.X, aber Input ist nicht definiert"

**Problem:**
```yaml
on:
  workflow_dispatch:
    inputs:
      mode:
        description: "Mode"
        required: true

jobs:
  example:
    steps:
      - run: echo "${{ github.event.inputs.target }}"  # ❌ 'target' nicht definiert
```

**Fix:**
```yaml
on:
  workflow_dispatch:
    inputs:
      mode:
        description: "Mode"
        required: true
      target:  # ✅ Input hinzugefügt
        description: "Target"
        required: false
        default: "all"
```

### Finding: "Verdächtig: inputs.X gefunden"

**Problem:**
```yaml
on:
  workflow_dispatch:
    inputs:
      mode:
        description: "Mode"
        required: true

jobs:
  example:
    if: ${{ inputs.mode == 'dry-run' }}  # ❌ 'inputs.X' ist für workflow_call, nicht workflow_dispatch
```

**Fix:**
```yaml
jobs:
  example:
    if: ${{ github.event.inputs.mode == 'dry-run' }}  # ✅ Korrekte Syntax für workflow_dispatch
```

### Finding: "Workflow hat kein 'on: workflow_dispatch'"

**Problem:**
```yaml
on:
  push:
    branches: ["main"]

jobs:
  example:
    steps:
      - run: echo "${{ github.event.inputs.mode }}"  # ❌ Workflow hat keinen workflow_dispatch Trigger
```

**Fix Option 1 (Dispatch hinzufügen):**
```yaml
on:
  push:
    branches: ["main"]
  workflow_dispatch:  # ✅ Trigger hinzugefügt
    inputs:
      mode:
        description: "Mode"
        required: false
```

**Fix Option 2 (Input-Referenz entfernen/absichern):**
```yaml
on:
  push:
    branches: ["main"]

jobs:
  example:
    steps:
      - run: echo "${{ github.event.inputs.mode || 'default' }}"  # ✅ Mit Fallback abgesichert
```

## CI Integration

Der Guard läuft automatisch via `.github/workflows/ci-workflow-dispatch-guard.yml` wenn:
- Workflow-Dateien unter `.github/workflows/` geändert werden
- Der Guard-Script selbst geändert wird
- Tests/Fixtures für den Guard geändert werden

**Exit-Codes:**
- `0` = OK (keine Findings)
- `1` = WARN (nur wenn `--fail-on-warn` gesetzt)
- `2` = ERROR (Findings gefunden)

## Tests

**Lokale Ausführung:**
```bash
uv run pytest -q tests/ops/test_validate_workflow_dispatch_guards.py -v
```

**Fixtures:**
- `tests/fixtures/workflows_dispatch_guard/good_workflow.yml` — Valider Workflow (keine Findings)
- `tests/fixtures/workflows_dispatch_guard/bad_workflow.yml` — Invalider Workflow (2 Findings erwartet)

## Limitationen

- **Inline YAML Forms:** `on: {workflow_dispatch: ...}` wird erkannt, aber Inputs sind schwer zuverlässig zu parsen → WARN statt ERROR
- **Komplexe Expressions:** Guard scannt nur nach `github.event.inputs.<name>` und `inputs.<name>` Patterns, keine vollständige Expression-Evaluierung
- **False Positives:** Bei Reusable Workflows (`workflow_call`) die auch `workflow_dispatch` unterstützen kann es zu False Positives kommen → In solchen Fällen Guard-Empfehlung ignorieren oder Workflow umstrukturieren

## Empfehlung: Required Status Check

**Nach 1-2 PRs ohne False Positives sollte dieser Check als Required Status Check markiert werden:**

1. GitHub → Settings → Branches → Branch Protection Rules (oder Rulesets)
2. Check hinzufügen: `CI / Workflow Dispatch Guard / dispatch-guard`
3. Blockiert PRs bei Findings

## Referenzen

- **Guard Script:** `scripts/ops/validate_workflow_dispatch_guards.py`
- **CI Workflow:** `.github/workflows/ci-workflow-dispatch-guard.yml`
- **Tests:** `tests/ops/test_validate_workflow_dispatch_guards.py`
- **Root Cause (Phase 5B Bug):** PR #663 — workflow_dispatch condition regression
- **Prevention:** Phase 5C — dieser Guard

## Version

- **v1.0.0** (2026-01-12) — Initial implementation (stdlib-only, path-filtered CI)
