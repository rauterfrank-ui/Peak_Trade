# 📋 Peak Trade TO-MAKE Board - Setup Anleitung

> Eine umfassende Schritt-für-Schritt-Anleitung zur Einrichtung des GitHub Project Boards für Peak Trade

## 📑 Inhaltsverzeichnis

1. [Übersicht](#-übersicht)
2. [Projekt erstellen](#-projekt-erstellen-via-github-ui)
3. [Spalten/Status-Felder konfigurieren](#-spaltenstatus-felder-konfigurieren)
4. [Issues zum Board hinzufügen](#-issues-zum-board-hinzufügen)
5. [Automatisierungsregeln einrichten](#-automatisierungsregeln-einrichten)
6. [Custom Fields einrichten](#-custom-fields-einrichten)
7. [Quick Links](#-quick-links)
8. [GitHub CLI Alternative](#-github-cli-alternative)
9. [Best Practices](#-best-practices)

---

## 🎯 Übersicht

Das **Peak Trade TO-MAKE Board** ist ein GitHub Project, das die Verwaltung und Priorisierung von Aufgaben für das Peak Trade Projekt ermöglicht. Es verwendet ein flexibles Kanban-System mit mehreren Prioritätsstufen.

### Ziele
- ✅ Übersichtliche Darstellung aller anstehenden Aufgaben
- ✅ Priorisierung nach Wichtigkeit (Priorität 1-3)
- ✅ Transparenter Workflow von Backlog bis Done
- ✅ Automatische Statusaktualisierung
- ✅ Team-Koordination und Aufgabenverteilung

---

## 🆕 Projekt erstellen (via GitHub UI)

### Schritt 1: Zum Projects-Bereich navigieren

1. Öffne das Repository: `https://github.com/rauterfrank-ui/Peak_Trade`
2. Klicke auf den Tab **"Projects"** in der oberen Navigation
3. Klicke auf den grünen Button **"New project"**

> 💡 **Hinweis:** Du benötigst Admin- oder Write-Rechte für das Repository.

### Schritt 2: Projekt-Template auswählen

Es öffnet sich ein Modal mit verschiedenen Templates:

- **Team backlog** - Empfohlen! ⭐
- **Feature roadmap**
- **Bug tracker**
- **Start from scratch**

**Unsere Empfehlung:** Wähle **"Team backlog"** als Basis und passe es dann an.

### Schritt 3: Projekt benennen

- **Name:** `Peak Trade TO-MAKE Board`
- **Description:** `Aufgabenverwaltung und Priorisierung für Peak Trade - Issues #95-103 und weitere`
- **Visibility:**
  - ✅ **Private** (nur für Team-Mitglieder sichtbar)
  - ⬜ Public (öffentlich sichtbar)

### Schritt 4: Projekt erstellen

Klicke auf **"Create project"** - fertig! 🎉

---

## 🎨 Spalten/Status-Felder konfigurieren

### Empfohlene Spalten-Struktur

Das Board sollte folgende Spalten haben:

| Spalte | Symbol | Beschreibung | Farbcode |
|--------|--------|--------------|----------|
| **📥 Backlog** | 📥 | Gesammelte, noch nicht priorisierte Issues | Grau `#808080` |
| **🔥 Priorität 1** | 🔥 | Kritisch - sofort bearbeiten (High) | Rot `#d73a4a` |
| **⚡ Priorität 2** | ⚡ | Wichtig - zeitnah bearbeiten (Medium) | Orange `#fb8500` |
| **⭐ Priorität 3** | ⭐ | Normal - bei Gelegenheit (Low) | Gelb `#ffc107` |
| **🚧 In Progress** | 🚧 | Wird aktuell bearbeitet | Blau `#0969da` |
| **✅ Done** | ✅ | Abgeschlossen | Grün `#2da44e` |

### Workflow-Flow

```
📥 Backlog → 🔥 Priorität 1 → ⚡ Priorität 2 → ⭐ Priorität 3 → 🚧 In Progress → ✅ Done
```

**Aktueller Status der Issues:**
- 🔥 Priority 1 (High): #97, #101
- ⚡ Priority 2 (Medium): #98, #99, #100
- ⭐ Priority 3 (Low): #103
- 🎯 Epic: #96

### Spalten einrichten

#### Option A: Status-Feld bearbeiten (empfohlen)

1. Klicke auf **⚙️ Settings** (oben rechts im Project Board)
2. Wähle **"Status"** im linken Menü
3. Bearbeite die vorhandenen Status oder füge neue hinzu:

```
Status Field Name: Status
Type: Single select

Options:
- Backlog (Grau)
- Priorität 1 (Rot)
- Priorität 2 (Orange)
- Priorität 3 (Gelb)
- In Progress (Blau)
- Done (Grün)
```

4. **Standard-Status:** `Backlog`
5. Speichern mit **"Save changes"**

#### Option B: Board-Ansicht anpassen

1. Im Board-View (Table oder Board Layout)
2. Klicke auf **"+ New column"** rechts
3. Gib den Namen ein (z.B. "Priorität 1")
4. Weise dem Status eine Farbe zu
5. Wiederhole für alle gewünschten Spalten

> 📸 **Screenshot-Hinweis:** Die Status-Spalten erscheinen als vertikale Columns im Board-Layout und als Dropdown-Feld im Table-Layout.

---

## 📌 Issues zum Board hinzufügen

### Methode 1: Issues einzeln hinzufügen (UI)

1. Öffne das Project Board
2. Klicke auf **"+ Add item"** am unteren Rand einer Spalte
3. Suche nach der Issue-Nummer (z.B. `#95`)
4. Wähle die Issue aus und sie wird hinzugefügt
5. Wiederhole für Issues **#95 bis #103**

### Methode 2: Bulk-Import (schneller!)

1. Im Project Board: Klicke auf **"⋮"** (drei Punkte, oben rechts)
2. Wähle **"Settings"**
3. Scrolle zu **"Manage access"** oder **"Workflows"**
4. Gehe zurück zum Board
5. Nutze die Suchfunktion: `repo:rauterfrank-ui&#47;Peak_Trade is:issue 95..103`
6. Markiere alle Issues (Shift + Click)
7. Rechtsklick → **"Add to project"** → Wähle dein Board

### Methode 3: Via Issue-Seite

1. Öffne jede Issue (z.B. `https://github.com/rauterfrank-ui/Peak_Trade/issues/95`)
2. Rechte Sidebar → Klicke auf **"Projects"**
3. Wähle **"Peak Trade TO-MAKE Board"**
4. Die Issue wird automatisch im Backlog hinzugefügt

### Issues-Liste für schnellen Zugriff

Hier die Issues, die hinzugefügt werden sollen:

- [Issue #95](https://github.com/rauterfrank-ui/Peak_Trade/issues/95)
- [Issue #96](https://github.com/rauterfrank-ui/Peak_Trade/issues/96)
- [Issue #97](https://github.com/rauterfrank-ui/Peak_Trade/issues/97)
- [Issue #98](https://github.com/rauterfrank-ui/Peak_Trade/issues/98)
- [Issue #99](https://github.com/rauterfrank-ui/Peak_Trade/issues/99)
- [Issue #100](https://github.com/rauterfrank-ui/Peak_Trade/issues/100)
- [Issue #101](https://github.com/rauterfrank-ui/Peak_Trade/issues/101)
- [Issue #102](https://github.com/rauterfrank-ui/Peak_Trade/issues/102)
- [Issue #103](https://github.com/rauterfrank-ui/Peak_Trade/issues/103)

> ✅ **Tipp:** Nach dem Hinzufügen alle Issues auf Status "Backlog" setzen und dann einzeln priorisieren.

---

## 🤖 Automatisierungsregeln einrichten

GitHub Projects bietet eingebaute Automationen, die den Workflow vereinfachen.

### Zugriff auf Workflows

1. Im Project Board: **⚙️ Settings**
2. Linkes Menü: **"Workflows"**
3. Hier können Built-in Workflows aktiviert werden

### Empfohlene Automatisierungen

#### 1. Auto-add to project

**Regel:** Neue Issues automatisch zum Board hinzufügen

```
Workflow: Item added to project
Trigger: When an issue is opened in Peak_Trade
Action: Add to project → Set status to "Backlog"
```

**Einrichten:**
- Toggle **"Auto-add to project"** aktivieren
- Repository: `rauterfrank-ui&#47;Peak_Trade`
- Default status: `Backlog`

---

#### 2. Auto-move to In Progress

**Regel:** Issue nach "In Progress" verschieben, wenn zugewiesen

```
Workflow: Item closed
Trigger: Issue is assigned to someone
Action: Set status to "In Progress"
```

**Einrichten:**
```yaml
# In Workflows:
- Name: "Move to In Progress when assigned"
- When: Issue assigned
- Then: Status = "In Progress"
```

---

#### 3. Auto-move to Done

**Regel:** Abgeschlossene Issues automatisch nach "Done"

```
Workflow: Item closed
Trigger: Issue is closed
Action: Set status to "Done"
```

**Einrichten:**
- Toggle **"Auto-close"** aktivieren
- When: Issue closed
- Set status: `Done`

---

#### 4. Auto-archive Done items

**Regel:** Issues in "Done" nach 30 Tagen archivieren

```
Workflow: Auto-archive
Trigger: Status = "Done" for 30+ days
Action: Archive item
```

> 💡 **Hinweis:** Diese Regel hält das Board übersichtlich!

---

### Weitere nützliche Automationen

| Automation | Trigger | Aktion |
|------------|---------|--------|
| PR verknüpfen | PR opened und mit Issue verlinkt | Status → "In Progress" |
| Review angefordert | PR review requested | Assignee benachrichtigen |
| Stale Issues | Keine Aktivität seit 60 Tagen | Label "stale" hinzufügen |

---

## 🎛️ Custom Fields einrichten

Custom Fields ermöglichen zusätzliche Metadaten für bessere Organisation.

### Field 1: Priority (Priorität)

**Zweck:** Numerische Priorität unabhängig von der Spalte

1. Settings → **"+ New field"**
2. **Field name:** `Priority`
3. **Field type:** `Single select`
4. **Options:**
   ```
   P0 - Critical 🔴
   P1 - High 🟠
   P2 - Medium 🟡
   P3 - Low 🟢
   ```
5. **Default:** `P2 - Medium`

---

### Field 2: Effort (Aufwand)

**Zweck:** Geschätzter Zeitaufwand

1. **Field name:** `Effort`
2. **Field type:** `Single select`
3. **Options:**
   ```
   XS - < 1 Stunde
   S - 1-4 Stunden
   M - 1-2 Tage
   L - 3-5 Tage
   XL - 1+ Woche
   ```
4. **Default:** `M`

---

### Field 3: Category (Kategorie)

**Zweck:** Thematische Gruppierung

1. **Field name:** `Category`
2. **Field type:** `Single select`
3. **Options:**
   ```
   🐛 Bug Fix
   ✨ Feature
   📚 Documentation
   🔧 Refactoring
   🎨 UI/UX
   ⚡ Performance
   🔒 Security
   🧪 Testing
   ```

---

### Field 4: Sprint (optional)

**Zweck:** Sprint-Planung

1. **Field name:** `Sprint`
2. **Field type:** `Iteration`
3. **Duration:** 2 weeks
4. **Start date:** Montag des aktuellen Sprints

---

### Field 5: Assignee Group (optional)

**Zweck:** Team-Zuordnung

1. **Field name:** `Team`
2. **Field type:** `Single select`
3. **Options:**
   ```
   Frontend
   Backend
   DevOps
   Design
   QA
   ```

---

## 🔗 Quick Links

### Direkter Zugriff

Nach dem Erstellen des Projects, nutze diese Links:

```
📊 Project Board:
https://github.com/users/rauterfrank-ui/projects/[PROJECT_NUMBER]

📋 Board View:
https://github.com/users/rauterfrank-ui/projects/[PROJECT_NUMBER]/views/1

📊 Table View:
https://github.com/users/rauterfrank-ui/projects/[PROJECT_NUMBER]/views/2

⚙️ Settings:
https://github.com/users/rauterfrank-ui/projects/[PROJECT_NUMBER]/settings
```

> 💡 **Tipp:** Ersetze `[PROJECT_NUMBER]` mit der tatsächlichen Projektnummer (z.B. `1`, `2`, etc.)

### Bookmarklets

Speichere diese als Browser-Lesezeichen für schnellen Zugriff:

- **Zum Board:** `Peak Trade Board`
- **Issues filtern:** `Peak Trade Issues #95-103`
- **Priorität 1:** `Peak Trade P1`

---

## 💻 GitHub CLI Alternative

Für Power-User: Projekt-Setup via GitHub CLI (`gh`)

### Voraussetzungen

```bash
# GitHub CLI installieren
# macOS:
brew install gh

# Linux:
sudo apt install gh

# Windows:
winget install GitHub.cli

# Authentifizieren
gh auth login
```

---

### Projekt erstellen

```bash
# Projekt erstellen (User-Project)
gh project create \
  --owner rauterfrank-ui \
  --title "Peak Trade TO-MAKE Board" \
  --description "Aufgabenverwaltung für Peak Trade Issues #95-103"

# Output: Projekt-URL und -Nummer
```

---

### Status-Felder hinzufügen

```bash
# Projekt-Nummer aus vorherigem Befehl verwenden
PROJECT_NUMBER=1  # Anpassen!

# Status-Field mit Options erstellen
gh project field-create $PROJECT_NUMBER \
  --owner rauterfrank-ui \
  --name "Status" \
  --data-type "SINGLE_SELECT" \
  --single-select-options "Backlog,Priorität 1,Priorität 2,Priorität 3,In Progress,Done"
```

---

### Issues zum Projekt hinzufügen

```bash
# Einzelne Issue hinzufügen
gh project item-add $PROJECT_NUMBER \
  --owner rauterfrank-ui \
  --url https://github.com/rauterfrank-ui/Peak_Trade/issues/95

# Mehrere Issues in einer Loop
for i in {95..103}; do
  gh project item-add $PROJECT_NUMBER \
    --owner rauterfrank-ui \
    --url "https://github.com/rauterfrank-ui/Peak_Trade/issues/$i"
  echo "✅ Issue #$i hinzugefügt"
done
```

---

### Custom Fields erstellen

```bash
# Priority Field
gh project field-create $PROJECT_NUMBER \
  --owner rauterfrank-ui \
  --name "Priority" \
  --data-type "SINGLE_SELECT" \
  --single-select-options "P0 - Critical,P1 - High,P2 - Medium,P3 - Low"

# Effort Field
gh project field-create $PROJECT_NUMBER \
  --owner rauterfrank-ui \
  --name "Effort" \
  --data-type "SINGLE_SELECT" \
  --single-select-options "XS,S,M,L,XL"

# Category Field
gh project field-create $PROJECT_NUMBER \
  --owner rauterfrank-ui \
  --name "Category" \
  --data-type "SINGLE_SELECT" \
  --single-select-options "Bug Fix,Feature,Documentation,Refactoring,UI/UX,Performance,Security,Testing"
```

---

### Projekt-Informationen anzeigen

```bash
# Projekt-Details
gh project view $PROJECT_NUMBER --owner rauterfrank-ui

# Items im Projekt auflisten
gh project item-list $PROJECT_NUMBER --owner rauterfrank-ui --format json

# Fields anzeigen
gh project field-list $PROJECT_NUMBER --owner rauterfrank-ui
```

---

### Nützliche CLI-Aliase

Füge zu `~/.bashrc` oder `~/.zshrc` hinzu:

```bash
# Aliases für Peak Trade Project
alias pt-board="gh project view 1 --owner rauterfrank-ui --web"
alias pt-add="gh project item-add 1 --owner rauterfrank-ui"
alias pt-list="gh project item-list 1 --owner rauterfrank-ui"

# Issues schnell zum Board hinzufügen
pt-add-issue() {
  gh project item-add 1 --owner rauterfrank-ui \
    --url "https://github.com/rauterfrank-ui/Peak_Trade/issues/$1"
}

# Verwendung: pt-add-issue 95
```

---

## 📚 Best Practices

### 1. Regelmäßige Board-Reviews

- **Daily:** Kurzer Blick auf "In Progress" (max. 3-5 Items)
- **Weekly:** Priorisierung im Backlog aktualisieren
- **Bi-weekly:** Sprint Planning - Items in Prioritätsspalten verschieben

---

### 2. Status-Übergänge

Empfohlener Workflow:

```
📥 Backlog
  ↓ (Priorisierung)
🔥 Priorität 1/2/3
  ↓ (Zuweisung + Start)
🚧 In Progress
  ↓ (PR merged + Issue closed)
✅ Done
  ↓ (nach 30 Tagen)
📦 Archived
```

---

### 3. Prioritäts-Richtlinien

| Priorität | Kriterien | Beispiele |
|-----------|-----------|-----------|
| **P1** 🔥 | Blocker, kritische Bugs, Deadline < 48h | Produktion down, Security-Fix |
| **P2** ⚡ | Wichtige Features, größere Bugs | Neue API-Endpoint, UI-Bug |
| **P3** ⭐ | Nice-to-have, kleinere Verbesserungen | Code-Cleanup, Doku-Update |

---

### 4. Effort-Schätzung

```
XS (< 1h):     Typo-Fix, Doku-Änderung
S (1-4h):      Kleiner Bug-Fix, Config-Änderung
M (1-2 Tage):  Feature-Komponente, größerer Bug
L (3-5 Tage):  Komplexes Feature, Refactoring
XL (1+ Woche): Architektur-Änderung, Migration
```

> 💡 **Tipp:** XL-Items in kleinere Tasks aufteilen!

---

### 5. Board-Hygiene

- ✅ Max. 3-5 Items in "In Progress" pro Person
- ✅ Wöchentlich Backlog aufräumen
- ✅ Stale Issues (>60 Tage) schließen oder neu bewerten
- ✅ Done-Items monatlich archivieren
- ✅ Labels konsistent verwenden

---

### 6. Team-Kommunikation

**Issue-Comments nutzen:**
- 💬 Updates zum Fortschritt
- 🤔 Fragen und Diskussionen
- 📸 Screenshots von Ergebnissen
- 🔗 Links zu PRs und Commits

**Mentions:**
- `@rauterfrank-ui` für Teamleiter
- `@team` für alle Team-Mitglieder

---

### 7. Labels effektiv nutzen

Empfohlene Labels zusätzlich zu den Custom Fields:

```
Type:
- bug 🐛
- enhancement ✨
- documentation 📚

Priority:
- critical 🔴
- high-priority 🟠
- low-priority 🟢

Status:
- blocked 🚫
- needs-review 👀
- ready-to-merge ✅
```

---

## 🎓 Weiterführende Ressourcen

### Offizielle Dokumentation

- [GitHub Projects Docs](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Projects Automations](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project)
- [Custom Fields](https://docs.github.com/en/issues/planning-and-tracking-with-projects/understanding-fields)
- [GitHub CLI Projects](https://cli.github.com/manual/gh_project)

### Tutorials

- [Project Board Best Practices](https://github.blog/2022-07-27-planning-next-to-your-code-github-projects-is-now-generally-available/)
- [Kanban Methodology](https://www.atlassian.com/agile/kanban)

### Community

- [GitHub Community Discussions](https://github.com/orgs/community/discussions/categories/projects)
- [GitHub Projects Feedback](https://github.com/github/feedback/discussions/categories/projects-feedback)

---

## ❓ FAQ

### Kann ich Issues aus mehreren Repos hinzufügen?

Ja! GitHub Projects (Beta) unterstützt Cross-Repository-Items. Einfach beim Hinzufügen das Repository auswählen.

### Wie exportiere ich Board-Daten?

Via GitHub CLI oder API:
```bash
gh project item-list $PROJECT_NUMBER --owner rauterfrank-ui --format json > board-export.json
```

### Kann ich mehrere Views erstellen?

Ja! Du kannst beliebig viele Views erstellen:
- Board View (Kanban)
- Table View (Tabelle)
- Roadmap View (Timeline)
- Custom Views mit Filtern

### Wie teile ich das Board mit externen Personen?

1. Settings → Manage access
2. Invite by email oder GitHub username
3. Rechte zuweisen (Read, Write, Admin)

### Werden gelöschte Issues aus dem Board entfernt?

Ja, gelöschte Issues werden automatisch aus allen Projects entfernt.

---

## 🎉 Zusammenfassung

Nach dieser Anleitung hast du:

- ✅ Ein strukturiertes GitHub Project Board
- ✅ 6 Status-Spalten (Backlog → Done)
- ✅ Issues #95-103 im Board
- ✅ Automatisierungsregeln für effizientes Arbeiten
- ✅ Custom Fields (Priority, Effort, Category)
- ✅ CLI-Commands für Power-User
- ✅ Best Practices für langfristigen Erfolg

---

## 📞 Support

Bei Fragen oder Problemen:

1. **GitHub Issues:** [Neues Issue erstellen](https://github.com/rauterfrank-ui/Peak_Trade/issues/new)
2. **Team-Chat:** Slack/Discord/etc.
3. **Dokumentation:** Diese Datei regelmäßig aktualisieren!

---

**Happy Project Management! 🚀**

*Letzte Aktualisierung: 2025-12-17*  
*Erstellt von: @rauterfrank-ui*  
*Version: 1.0*
