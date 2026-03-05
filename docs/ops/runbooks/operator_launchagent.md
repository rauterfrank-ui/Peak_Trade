# Operator LaunchAgent (macOS)

Ziel
- `operator_all.sh` täglich automatisch ausführen (auch wenn du den Laptop zuklappst — beim nächsten Wake/Login läuft es wieder).
- Logs und Evidence bleiben lokal unter `out/ops/`.

Install (empfohlen)
- `START_HOUR=7 START_MINUTE=15 STRICT_ALERTS=true scripts&#47;ops&#47;install_operator_all_launchagent.sh`

Defaults
- Uhrzeit: 07:15 (lokale Zeit)
- `RUN_E2E=true`
- `RUN_ONE_SHOT=true`
- `RUN_REGISTRY=true`
- `STRICT_ALERTS=true`
- `RunAtLoad=true` (läuft zusätzlich beim Login/Load)

Logs
- `out&#47;ops&#47;launchd&#47;operator_all.stdout.log`
- `out&#47;ops&#47;launchd&#47;operator_all.stderr.log`

Status
- `launchctl list | rg -n "com\.peaktrade\.operator_all" -S`

Uninstall
- `scripts&#47;ops&#47;uninstall_operator_all_launchagent.sh`

Hinweis
- Diese Runbooks/Plists sind **nur lokal relevant**. `out/` bleibt untracked.
- Das Label wird robust aus der Plist gelesen (PlistBuddy: `Print :Label`).


Profile modes
- Full: `MODE=full` (default)
- Registry-only strict: `MODE=registry_only STRICT_ALERTS=true`
