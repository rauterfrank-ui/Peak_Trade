# Worktree Policy (Ops Standard)

## Zielbild

Wir nutzen Git Worktrees, um parallel zu arbeiten — **ohne Branch-Kollisionen** und ohne "detached HEAD"-Fußangeln.

**Standard:**

* ✅ **Genau 1 Worktree auf `main`** (Primary, z.B. `elegant-austin`)
* ✅ Alle weiteren Worktrees nutzen **eigene Branches**:

  * `wt&#47;<name>-main` für *main-tracking* (spiegelt `origin&#47;main`)
  * `feat&#47;*`, `fix&#47;*`, `docs&#47;*`, `chore&#47;*` für echte Arbeit
* ❌ Kein dauerhaftes **detached HEAD** (nur temporär, dann sofort auf Branch wechseln)

## Warum das so sinnvoll ist

* Git erlaubt **nicht**, dass derselbe Branch (`main`) gleichzeitig in mehreren Worktrees ausgecheckt ist.
* Ein `wt&#47;*`-Branch ist die einfache Lösung: **gleiches Commit-Level wie `main`**, aber **anderer Branch-Name** → keine Kollision.
* Detached HEAD ist fehleranfällig (Commits "hängen lose", Branch-Delete blockiert, etc.).

---

## Naming Convention

* Primary main worktree: `main`
* Secondary main-tracking: `wt&#47;<worktree>-main`
  Beispiele:

  * `wt&#47;wonderful-main`
  * `wt&#47;keen-main`

---

## Rezepte

### A) "Main-tracking" Worktree aufsetzen (ohne Branch-Kollision)

Im gewünschten Worktree:

```bash
git fetch origin
git checkout -b wt/<name>-main origin/main
```

### B) "Main-tracking" Worktree aktualisieren (sicher & deterministisch)

Empfohlen (hart synchronisieren):

```bash
git fetch origin
git checkout wt/<name>-main
git reset --hard origin/main
```

Alternative (fast-forward, wenn Branch linear bleibt):

```bash
git checkout wt/<name>-main
git pull --ff-only
```

### C) Primary `main` Worktree aktualisieren

Im Primary-Worktree:

```bash
git checkout main
git pull --ff-only
```

---

## Troubleshooting

### 1) "Branch is already checked out" / "multiple worktrees"

**Symptom:** `git checkout main` schlägt in einem Worktree fehl.
**Fix:** Lass `main` exklusiv im Primary-Worktree und nutze `wt&#47;<name>-main` in allen anderen.

### 2) Worktree steckt in "detached HEAD"

**Symptom:** `git status` zeigt "HEAD detached at …".
**Fix (empfohlen):** Auf einen Branch wechseln:

```bash
# Wenn du main-Stand willst:
git fetch origin
git checkout -b wt/<name>-main origin/main
```

### 3) Lokalen Branch kann man nicht löschen ("checked out in worktree …")

**Symptom:** `git branch -d <branch>` scheitert, weil irgendwo ausgecheckt.
**Fix:** In *diesem* Worktree auf einen anderen Branch wechseln (z.B. `wt&#47;<name>-main` oder `main`) und dann löschen.

### 4) Worktree entfernen (wenn nicht mehr gebraucht)

```bash
git worktree remove --force <path>
git worktree prune
```

---

## Quick Verification (Operator)

```bash
git worktree list
git status -sb
git rev-parse --abbrev-ref --symbolic-full-name @{u}   # upstream 확인
```

**Erwartung:**

* Primary: `main`
* Secondary: `wt&#47;*...origin&#47;main`
* Beide können auf demselben Commit stehen, ohne Konflikte.
