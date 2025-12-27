# MERGE LOG — PR #{{PR_NUMBER}} — {{TYPE}}({{SCOPE}}): {{TITLE}}

**PR:** {{PR_URL}}  
**Merged:** {{MERGE_DATE_YYYY_MM_DD}}  
**Merge Commit:** {{MERGE_COMMIT_SHA}}

---

## Zusammenfassung
- {{ONE_LINE_WHAT_CHANGED}}
- {{ONE_LINE_IMPACT_OR_USER_VALUE}}

## Warum
- {{ROOT_CAUSE_OR_CONTEXT}}
- {{WHY_NOW_OR_WHAT_BROKE}}

## Änderungen
**Geändert**
- `{{path/to/file.ext}}` — {{SHORT_CHANGE_DESC}}
- `{{path/to/file.ext}}` — {{SHORT_CHANGE_DESC}}

**Neu**
- `{{path/to/new_file.ext}}` — {{SHORT_DESC}}

## Verifikation
**CI**
- {{CHECK_NAME}} — {{PASS/FAIL}} ({{DURATION_IF_KNOWN}})
- {{CHECK_NAME}} — {{PASS/FAIL}} ({{DURATION_IF_KNOWN}})

**Lokal**
- {{COMMAND_1}}
- {{RESULT_1}}
- {{OPTIONAL_NOTE}}

## Risiko
**Risk:** 🟢 Minimal / 🟡 Medium / 🔴 High  
**Begründung**
- {{WHY_LOW_OR_MEDIUM_OR_HIGH}}
- {{WHAT_COULD_GO_WRONG}}

## Operator How-To
- {{STEP_1}}
- {{STEP_2}}
- {{STEP_3}}

## Referenzen
- PR: {{PR_URL}}
- Commit: {{MERGE_COMMIT_URL_OR_SHA}}
- Related: {{LINKS_IF_ANY}}

---

### Extended (optional)
> Nur bei komplexen/riskanten PRs: Deep-Dive, Rollback, Edge-Cases, Migrationshinweise.
