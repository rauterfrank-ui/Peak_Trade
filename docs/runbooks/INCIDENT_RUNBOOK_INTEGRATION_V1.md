# Incident Runbook Integration (Phase 84)

## Kontext

Die Live-Alert-Pipeline verknüpft Alerts automatisch mit passenden **Incident-Runbooks**.
Runbooks sind an drei Stellen sichtbar:

1. **Slack-Alerts** – eigener Block `Runbooks:` mit klickbaren Links
2. **E-Mail-Alerts** – Runbooks im Body (z.B. unterhalb der Kernmetrik/Severity)
3. **Live-Alerts-Dashboard (`/alerts`)** – Spalte „Runbooks" mit Badges

Ziel: Operatoren müssen bei kritischen Alerts nicht mehr selbst nach der richtigen Doku suchen, sondern können direkt dem verlinkten Runbook folgen.

---

## Wie erkenne ich, ob ein Alert Runbooks hat?

### In Slack/E-Mail

Im Alert-Text erscheint ein Block wie:

```
Runbooks: [Live Risk Severity] [Alert Pipeline Incident]
```

### Im Dashboard (`/alerts`)

In der Tabelle gibt es eine Spalte **„Runbooks"** mit Badges, z.B.:

- `Live Risk Severity`
- `Alert Pipeline Incident`
- `Exchange Connectivity Incident`

### Kein Runbook vorhanden

Wenn ein Alert **keine** spezifischen Runbooks hat, wird entweder:

- kein Runbook angezeigt, oder
- ein generischer Fallback wie `Generic Incident Runbook` verwendet (abhängig von der Registry-Konfiguration).

---

## Standard-Vorgehen bei Alerts mit Runbooks

### 1. Alert sichten

- Slack/E-Mail oder `/alerts` öffnen
- Severity prüfen (GREEN/YELLOW/RED) und die wichtigsten Metadaten (z.B. Session, Strategy, Environment)

### 2. Passendes Runbook öffnen

- In Slack/E-Mail oder im Dashboard das Runbook-Badge anklicken
- Im Zweifel immer das Runbook mit der höchsten Spezialisierung bevorzugen:
  - z.B. `Exchange Connectivity Incident` vor einem generischen `Generic Incident Runbook`

### 3. Schritte im Runbook abarbeiten

- Checklisten im Runbook strikt durchgehen (Monitoring prüfen, Logs ansehen, ggf. Services/Jobs neu starten, etc.)
- Alle „Stop-Trading"- oder „Switch-to-Safe-Mode"-Anweisungen sind **verpflichtend** zu befolgen

### 4. Ergebnis dokumentieren

- Falls vorgesehen: Ergebnis/Kommentar im entsprechenden Logging-/Incident-Tool oder in der Alert-Historie ergänzen
- Bei wiederkehrenden Issues: Runbook mit einem Hinweis versehen (z.B. TODO für zukünftige Phasen)

---

## Fehlende oder falsche Runbooks

Falls ein Alert offensichtlich ein falsches oder kein Runbook hat:

1. Alert im `/alerts`-Dashboard öffnen
2. Betroffene Runbook-Badges notieren
3. Issue für die Runbook-Registry anlegen (z.B. `Runbook mapping für alert_code=XYZ_SEVERITY_HIGH prüfen`)
4. Bis zur Korrektur das **generische Incident-Runbook** verwenden

So bleibt der Flow stabil, selbst wenn die Registry noch nicht alle Alert-Typen perfekt abdeckt.

---

## Verwandte Runbooks

- [Live Risk Severity Integration](./LIVE_RISK_SEVERITY_INTEGRATION.md)
- [Live Alert Pipeline Slack/Email Runbook](./LIVE_ALERT_PIPELINE_SLACK_EMAIL_RUNBOOK_V1.md)
