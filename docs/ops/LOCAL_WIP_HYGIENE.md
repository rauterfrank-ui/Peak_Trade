# Local WIP / Untracked Hygiene (Ops)

Ziel: Der `main`-Worktree bleibt sauber, PRs bleiben minimal, und lokale Prototypen (untracked) erzeugen keine "Noise".

## Grundsatz
- **Kein globales `.gitignore`** für Pfade, die später echte Features werden könnten (z.B. `src&#47;eval&#47;`).
- **Lokale Ignorierung** stattdessen über:
  - `.git/info/exclude` (nur dieser Worktree)
  - oder globales Git-Ignore (`~/.config/git/ignore`)

## Empfohlener Workflow

### 1) Prototyp wird "echt" → eigene Branch + commit
Wenn aus lokalen Files ein Feature werden soll:
1. `git switch -c feat&#47;<topic>`
2. `git add ...`
3. `git commit ...`
4. PR erstellen

### 2) Prototyp bleibt lokal → Worktree-exklusiv ignorieren
**Nur lokal** (im Repo, nicht committet):
```bash
printf "\n# Local WIP (not committed)\nsrc/eval/\nscripts/evaluate_live_session.py\ndocs/ops/LIVE_DATA_EVALUATION.md\ntests/test_live_eval_*.py\n" >> .git/info/exclude
```

**Global** (gilt für alle Repos):
```bash
# In ~/.config/git/ignore oder ~/.gitignore_global
echo "scratch/" >> ~/.config/git/ignore
```

## Warum `.git/info/exclude`?
- Gilt nur für diesen Worktree
- Wird nicht committet → kein "Rauschen" in PRs
- Andere Entwickler können dieselben Pfade nutzen

## Beispiel: Live-Eval-Prototyp
```bash
# Im Hauptworktree lokal ignorieren
printf "\n# Eval prototype (local only)\nsrc/eval/\nscripts/evaluate_live_session.py\n" >> .git/info/exclude

# Arbeiten ohne Commit-Zwang
vim src/eval/metrics.py
python3 scripts/evaluate_live_session.py

# Später: Feature-Branch erstellen, wenn es ernst wird
git switch -c feat/eval-framework
git add src/eval/ scripts/evaluate_live_session.py
git commit -m "feat(eval): initial evaluation framework"
```

## Best Practices
1. **Docs-only PRs**: Nur Dokumentation committen, keine echten Code-Änderungen
2. **Feature-Branches**: Sobald Code "echt" wird, eigene Branch + PR
3. **Lokale Experimente**: In `.git/info/exclude` eintragen
4. **Worktree-Hygiene**: Regelmäßig `git status` checken

## Siehe auch
- [CI.md](CI.md) - Fast-lane vs. full test matrix
- [README.md](README.md) - Ops-Dokumentations-Index
