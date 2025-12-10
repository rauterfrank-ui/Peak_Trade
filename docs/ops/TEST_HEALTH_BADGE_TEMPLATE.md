# Test Health Badge Template

Kopiere diese Snippets in dein `README.md`:

## Standard GitHub Actions Badge

```markdown
[![Test Health](https://github.com/YOUR_ORG/Peak_Trade/actions/workflows/test_health.yml/badge.svg)](https://github.com/YOUR_ORG/Peak_Trade/actions/workflows/test_health.yml)
```

**Ergebnis**:
[![Test Health](https://github.com/YOUR_ORG/Peak_Trade/actions/workflows/test_health.yml/badge.svg)](https://github.com/YOUR_ORG/Peak_Trade/actions/workflows/test_health.yml)

---

## Custom Health Score Badge (shields.io)

### Static Badge (manuell zu aktualisieren)

```markdown
![Health Score](https://img.shields.io/badge/Health%20Score-100%25-brightgreen?style=flat-square&logo=github)
```

**Farben nach Score**:
- 🟢 Green (80-100%): `brightgreen`
- 🟡 Yellow (50-79%): `yellow`
- 🔴 Red (0-49%): `red`

**Ergebnis**:
![Health Score](https://img.shields.io/badge/Health%20Score-100%25-brightgreen?style=flat-square&logo=github)

---

## Dynamic Badge (mit Endpoint)

### Option 1: shields.io Dynamic JSON Badge

1. Erstelle `health-badge.json` im Repo:

```json
{
  "schemaVersion": 1,
  "label": "health",
  "message": "100%",
  "color": "brightgreen"
}
```

2. Badge in README:

```markdown
![Health Score](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/YOUR_ORG/Peak_Trade/main/health-badge.json)
```

3. Update Badge via CI:

```yaml
- name: Update Health Badge
  run: |
    HEALTH_SCORE=$(python -c "import json; data=json.load(open('reports/test_health/${LATEST_DIR}/summary.json')); print(int(data['health_score']))")
    
    # Farbe bestimmen
    if [ "$HEALTH_SCORE" -ge 80 ]; then
      COLOR="brightgreen"
    elif [ "$HEALTH_SCORE" -ge 50 ]; then
      COLOR="yellow"
    else
      COLOR="red"
    fi
    
    # JSON erstellen
    cat > health-badge.json <<EOF
    {
      "schemaVersion": 1,
      "label": "health",
      "message": "${HEALTH_SCORE}%",
      "color": "${COLOR}"
    }
    EOF
    
    git add health-badge.json
    git commit -m "chore: update health badge [skip ci]"
    git push
```

---

## Multiple Profile Badges

```markdown
### Test Health Status

| Profile | Status | Score |
|---------|--------|-------|
| Daily Quick | ![Daily](https://img.shields.io/badge/Daily-100%25-brightgreen) | 100% |
| Weekly Core | ![Weekly](https://img.shields.io/badge/Weekly-100%25-brightgreen) | 100% |
| Full Suite | ![Full](https://img.shields.io/badge/Full-83.3%25-brightgreen) | 83.3% |
| R&D Experimental | ![R&D](https://img.shields.io/badge/R%26D-80%25-brightgreen) | 80% |
```

**Ergebnis**:

| Profile | Status | Score |
|---------|--------|-------|
| Daily Quick | ![Daily](https://img.shields.io/badge/Daily-100%25-brightgreen) | 100% |
| Weekly Core | ![Weekly](https://img.shields.io/badge/Weekly-100%25-brightgreen) | 100% |
| Full Suite | ![Full](https://img.shields.io/badge/Full-83.3%25-brightgreen) | 83.3% |
| R&D Experimental | ![R&D](https://img.shields.io/badge/R%26D-80%25-brightgreen) | 80% |

---

## README Section Template

```markdown
# Peak_Trade

![Test Health](https://github.com/YOUR_ORG/Peak_Trade/actions/workflows/test_health.yml/badge.svg)
![Health Score](https://img.shields.io/badge/Health-100%25-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)

## 📊 System Health

Unser automatisiertes Test-Health-System überwacht kontinuierlich die Code-Qualität:

- **Daily Quick Check**: Täglich um 06:00 UTC
- **Weekly Core Check**: Sonntags um 03:00 UTC
- **Latest Health Score**: 100% 🟢

[Siehe aktuelle Reports →](https://github.com/YOUR_ORG/Peak_Trade/actions/workflows/test_health.yml)

### Test Coverage

| Profile | Checks | Status | Last Run |
|---------|--------|--------|----------|
| 🚀 Daily Quick | 2 | 🟢 100% | 2025-12-10 |
| 📅 Weekly Core | 5 | 🟢 100% | 2025-12-10 |
| 🔬 R&D Experimental | 4 | 🟢 80% | 2025-12-10 |

---

## Installation & Testing

... (rest of README)
```

---

## Badge Styles

shields.io unterstützt verschiedene Styles:

```markdown
# Flat (default)
![](https://img.shields.io/badge/Health-100%25-brightgreen)

# Flat Square
![](https://img.shields.io/badge/Health-100%25-brightgreen?style=flat-square)

# Plastic
![](https://img.shields.io/badge/Health-100%25-brightgreen?style=plastic)

# For the Badge
![](https://img.shields.io/badge/Health-100%25-brightgreen?style=for-the-badge)

# Social
![](https://img.shields.io/badge/Health-100%25-brightgreen?style=social)
```

**Empfehlung**: `flat-square` für modernes Aussehen

---

## Custom Icons

Füge Icons hinzu mit `logo` Parameter:

```markdown
# GitHub Icon
![](https://img.shields.io/badge/Health-100%25-brightgreen?logo=github)

# Python Icon
![](https://img.shields.io/badge/Health-100%25-brightgreen?logo=python)

# Custom Icon
![](https://img.shields.io/badge/Health-100%25-brightgreen?logo=data:image/svg+xml;base64,...)
```

---

## Animated Badge (Advanced)

Für Live-Updates ohne Refresh:

```html
<img src="https://img.shields.io/endpoint?url=https://your-api.com/health-badge" alt="Health Score" />
```

Benötigt:
1. API Endpoint der aktuelle `health-badge.json` liefert
2. CORS-Header für GitHub Pages

---

## Best Practices

✅ **DO**:
- Verwende aussagekräftige Labels
- Halte Farben konsistent (grün=gut, rot=schlecht)
- Verlinke Badges zu relevanten Pages
- Update Dynamic Badges automatisch via CI

❌ **DON'T**:
- Zu viele Badges (max 5-7 im Header)
- Manuelle Badge-Updates (nutze CI)
- Inkonsistente Styles mischen
- Badges ohne Links (nicht klickbar)

---

## Weitere Ressourcen

- [shields.io](https://shields.io/)
- [Simple Icons](https://simpleicons.org/) (für `logo` Parameter)
- [Badge Generator](https://badgen.net/)
- [GitHub Actions Badge](https://docs.github.com/en/actions/managing-workflow-runs/adding-a-workflow-status-badge)
