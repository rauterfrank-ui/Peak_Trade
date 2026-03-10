# Phase 3 — Branch Deletion Runbook (Draft, Do Not Execute)

**Erstellt:** 2026-03-10  
**Status:** Dokumentation only. Keine Löschung in dieser Phase.

---

## Preflight Checks

1. **Branch:** Auf `main` sein.
2. **Status:** `git status --short` — sauber oder nur erwartete Änderungen.
3. **Backup:** `out/ops/branch_archive_phase2_review/` vollständig vorhanden.
4. **Merged-Liste:** `git branch --merged main` erneut ausführen, mit Phase-2-Classification abgleichen.

---

## Safety Gates

| Gate | Bedingung |
|------|-----------|
| G1 | Nur `git branch -d` verwenden (kein `-D`) |
| G2 | Nur Branches löschen, die in `git branch --merged main` erscheinen |
| G3 | Vor Löschung: `git log main..<branch> --oneline` — muss leer sein |
| G4 | Keine Remote-Branches mutieren |
| G5 | Keine Branches mit aktivem Upstream (origin/…) löschen, ohne vorher Upstream zu prüfen |

---

## Inventory Backup (vor Löschung)

```bash
mkdir -p out/ops/branch_archive_phase3_YYYYMMDD
git branch --merged main | grep -v '^\*' | grep -v ' main' | sort > out/ops/branch_archive_phase3_YYYYMMDD/branches_to_delete.txt
git for-each-ref refs/heads --format='%(refname:short)	%(committerdate:short)	%(objectname:short)' | sort >> out/ops/branch_archive_phase3_YYYYMMDD/pre_delete_snapshot.tsv
```

---

## Dry-Run

```bash
# Zeige, welche Branches gelöscht würden
git branch --merged main | grep -v '^\*' | grep -v ' main' | while read b; do
  echo "WOULD_DELETE: $b"
done
```

---

## Deletion Commands (nur nach manueller Freigabe)

```bash
# Einzeln (empfohlen für erste Batches)
git branch -d <branch-name>

# Batch (nur für verifizierte merged branches)
git branch --merged main | grep -v '^\*' | grep -v ' main' | xargs -I {} git branch -d {}
```

**Hinweis:** `git branch -d` schlägt fehl, wenn der Branch nicht vollständig gemerged ist.

---

## Post-Delete Verification

```bash
git branch | wc -l
# Vergleiche mit erwarteter Anzahl
```

---

## Rollback

Kein Rollback möglich nach Löschung. Branches sind nur über Reflog wiederherstellbar (`git reflog`), und nur solange die Objekte noch im Repo sind.

---

## Empfohlener Ablauf

1. Phase-2-Classification prüfen
2. Nur `SAFE_DELETE_LOCAL_MERGED` in Betracht ziehen
3. Pro Branch: `git log main..<branch> --oneline` — wenn nicht leer, nicht löschen
4. Backup erstellen
5. Dry-Run ausführen
6. Manuelle Freigabe
7. Einzeln oder in kleinen Batches löschen
