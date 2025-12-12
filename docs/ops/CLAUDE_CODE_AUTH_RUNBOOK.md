# Claude Code – Auth (OAuth 401) Runbook

Wenn du im Peak_Trade Workflow eine Meldung bekommst wie:

> OAuth token has expired … 401 authentication_error

## Quick Fix (Standard)

1. **Claude Code starten**

   ```bash
   claude
   ```

2. In der **Claude Code Session**:
   * `/permissions` (optional, aber hilfreich)
   * `/logout`

3. **Claude Code schließen** (komplett beenden)

4. **Claude Code neu starten**

   ```bash
   claude
   ```

5. In der neuen Session:
   * `/login`

## Hard Reset (wenn 401 bleibt)

Nutze das Script, um mögliche `auth.json` zu finden/zu löschen:

```bash
# zeigt Kandidaten + Anweisung
scripts/claude_code_auth_reset.sh

# löscht auth.json (falls vorhanden) + zeigt Anweisung
scripts/claude_code_auth_reset.sh --purge
```

Danach den **Quick Fix** erneut durchführen.

## macOS Keychain (letzter Schritt)

Wenn es immer noch hängt:

* **Schlüsselbundverwaltung** öffnen
* nach **Claude** / **Anthropic** suchen
* entsprechende Einträge entfernen
* danach `claude` neu starten und `/login` durchführen

## Hinweis

* `/login`, `/logout`, `/permissions` funktionieren **nur innerhalb** einer laufenden Claude Code Session.

## Weitere Ressourcen

* [Claude Code Official Docs](https://code.claude.com/docs/)
* [IAM & Authentication Guide](https://code.claude.com/docs/en/iam.md)
* [Troubleshooting Guide](https://code.claude.com/docs/en/troubleshooting.md)

## Credential Storage (macOS)

Claude Code speichert Credentials verschlüsselt im macOS Keychain:
* Claude.ai credentials
* API credentials
* Azure Auth
* Bedrock Auth
* Vertex Auth

Bei persistierenden Problemen können diese Einträge manuell aus der Schlüsselbundverwaltung entfernt werden.
