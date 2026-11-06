# PR #237 — MERGE LOG (kompakt)

**PR:** #237 — chore(ops): add shared bash run helpers (strict/robust)  
**Status:** MERGED (squash)  
**Datum:** 2025-12-21  
**Scope:** Ops / Scripts / Templates / Tests / Doku

## Summary
- Ops-Tooling für konsistente strict/robust Semantik in Bash-Skripten
- Shared helper library (`run_helpers.sh`) + Copy-paste Template für neue Skripte
- Integration in bestehende Skripte (`pr_inventory_full.sh`, `label_merge_log_prs.sh`)

## Why
- Einheitliches Error-Handling für Ops-Skripte (fail-fast vs. warn-only)
- Wiederverwendbare Helper-Funktionen reduzieren Code-Duplikation
- Template ermöglicht schnellen Start für neue Ops-Skripte mit Best Practices
- Klare Trennung: Gating (required) vs. Main Work (mode-controlled) vs. Optional (never gating)

## Changes
- Added: `scripts/ops/run_helpers.sh` — Shared bash helper library
  - `pt_run_required()` — always abort on failure (gating)
  - `pt_run_optional()` — never abort (warn only)
  - `pt_run()` — mode-controlled (strict/robust)
  - `pt_require_cmd()` — command availability checks
  - `pt_log()`, `pt_warn()`, `pt_die()`, `pt_section()` — logging helpers
  - Mode control: `PT_MODE=strict` (default) or `PT_MODE=robust`
- Added: `templates/bash/ops_script_template.sh` — Copy-paste template for new ops scripts
- Modified: `scripts/ops/pr_inventory_full.sh` — integrated helpers
- Modified: `scripts/ops/label_merge_log_prs.sh` — integrated helpers
- Modified: `tests/test_ops_pr_inventory_scripts_syntax.py` — updated for `pt_require_cmd`
- Modified: `docs/ops/README.md` — added Bash Helpers section

## Verification
- CI: audit ✅, lint ✅, tests (3.11) ✅, strategy-smoke ✅
- Bash syntax: ✅ all scripts pass `bash -n`
- Tests: ✅ 17/17 tests pass

## Risk
🟢 **Low** — Ops tooling only, no production code changes. Behavior unchanged (strict mode is default).

## Operator How-To
- **Für neue Skripte:**
  ```bash
  # Template kopieren
  cp templates/bash/ops_script_template.sh scripts/ops/mein_script.sh

  # Platzhalter anpassen + Logik implementieren

  # Ausführen
  bash scripts/ops/mein_script.sh              # strict mode
  PT_MODE=robust bash scripts/ops/mein_script.sh  # robust mode
  ```
- **Helper-Funktionen:**
  - `pt_run_required "Label" command` — gating (immer abort)
  - `pt_run "Label" command` — mode-controlled
  - `pt_run_optional "Label" command` — never abort

## References
- PR #237 (GitHub)
- Helper library: `scripts/ops/run_helpers.sh`
- Template: `templates/bash/ops_script_template.sh`
