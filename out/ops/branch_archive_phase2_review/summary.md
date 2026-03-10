# Branch Archive Phase 2 — Review Summary

**Erstellt:** 2026-03-10  
**Modus:** Review-only (keine Löschung)

---

## Artifacts

| File | Beschreibung |
|------|--------------|
| `normalized_inventory.tsv` | Normalisierte Branch-Liste mit Kategorien |
| `classification.tsv` | Konservative Klassifikation pro Branch |
| `summary.md` | Diese Datei |
| `salvage_priority_list.md` | Salvage/Recover-Prioritäten |
| `historical_noise_list.md` | Vermutlich entbehrliche Branches |
| `phase3_delete_runbook_draft.md` | Phase-3-Lösch-Runbook (Draft) |

---

## Category Counts

| Kategorie | Anzahl |
|-----------|--------|
| main | 1 |
| feat | 300 |
| salvage | 48 |
| recover | 44 |
| cursor_name | 46 |
| fix | 26 |
| docs | 23 |
| ops | 14 |
| backup | 9 |
| other | 11 |
| ci | 6 |
| chore | 5 |
| wip | 5 |
| tmp | 2 |
| obs | 2 |
| analysis | 1 |
| config | 1 |
| governance | 1 |
| restore | 1 |
| **Total** | **501** |

---

## Classification Summary

| Bucket | Anzahl | Regel |
|--------|--------|------|
| SAFE_DELETE_LOCAL_MERGED | 55 | In main gemerged, `git branch -d` möglich |
| SAFE_ARCHIVE_KEEP_LOCAL_FOR_NOW | 12 | backup/tmp/wip — behalten, später prüfen |
| SALVAGE_REVIEW_REQUIRED | 43 | salvage/recover — manuelle Prüfung |
| MANUAL_REVIEW_REQUIRED | 230 | feat/fix/chore/docs/ci/ops etc. — Triage |
| ACTIVE_DO_NOT_TOUCH | 161 | main, aktueller Branch, oder mit Upstream |

---

## Classification Rules

1. **ACTIVE_DO_NOT_TOUCH:** main, feat/full-scan-wave3-branch-archive-review, Branches mit origin/…-Upstream
2. **SAFE_DELETE_LOCAL_MERGED:** `git branch --merged main` (ohne main)
3. **SAFE_ARCHIVE_KEEP_LOCAL_FOR_NOW:** backup/*, tmp/*, wip/*
4. **SALVAGE_REVIEW_REQUIRED:** recover/*, feat/salvage-*
5. **MANUAL_REVIEW_REQUIRED:** Alle übrigen (feat, fix, chore, docs, ci, ops, cursor_name, other)

---

## Normalization Notes

- Kategorien: main, feat, fix, chore, recover, salvage, backup, tmp, wip, docs, ci, ops, config, analysis, obs, governance, restore, cursor_name, other
- Merged: aus `branch_list_merged_into_main.txt` (Phase 1)
- Upstream: aus `git for-each-ref`

---

## Validation

- Alle Phase-1-Inputs vorhanden
- 6 Output-Dateien erstellt
- Keine Branch-Löschung durchgeführt
- docs/GOVERNANCE_DATAFLOW_REPORT.md, docs/REPO_AUDIT_REPORT.md unverändert
