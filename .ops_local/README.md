# .ops_local – lokale Ops-Daten (nicht versioniert)

Dieser Ordner enthält lokale, sensible oder generierte Ops-Daten, die **nicht** ins Git-Repository gehören.

## Struktur

> **Scope note**
>
> `.ops_local/secrets/` is currently a manual local storage location for operator-managed credentials and related files.
> It is **not** an automatically loaded secret store in Peak_Trade runtime code.
> If a workflow requires a specific loader, use the documented env-file or script-specific input for that workflow instead.
>

- `secrets/` – AWS Access Keys, Credentials (z.B. `pt-gh-export-consumer_accessKeys.csv`)
- `rclone/` – Rclone-Konfiguration (z.B. `pt_rclone.conf`)

## Hinweis

`.ops_local/` ist in `.gitignore` eingetragen und wird niemals committed.
