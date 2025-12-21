# MERGE LOG TEMPLATE (COMPACT)

> Standard: kompakt + fokussiert.  
> Extended Notes nur bei komplexen/riskanteren PRs (Risk != 🟢, Live/Governance/CI-Behavior, große Flächenänderung).

# PR #<NUM> — MERGE LOG

## Summary
PR #<NUM> <kurzer Titel/Outcome in 1 Satz>.

- PR: #<NUM> — <PR Title>
- Merged commit (main): `<sha>`
- Date: <YYYY-MM-DD>
- Chain context (optional):
  - PR #<A> (`<shaA>`) — <1-liner>
  - PR #<B> (`<shaB>`) — <1-liner>

## Motivation / Why
- <Warum war das nötig?>
- <Operator/Dev Nutzen in 1–2 bullets>

## Changes
### Added/Updated
- <Bullet>
- <Bullet>

### Touched files (optional)
- `<path>` — <1-liner>
- `<path>` — <1-liner>

## Verification
- `<command>` ✅
- `<command>` ✅
- Notes: <z.B. docs-only / targeted tests / CI checks>

## Risk Assessment
🟢 **Low** / 🟡 **Medium** / 🔴 **High**
- <1–3 bullets warum>

## Operator How-To
### Do this
- <Konkreter Schritt 1>
- <Konkreter Schritt 2>

### Quick commands (optional)
- `<cmd>`
- `<cmd>`

## Follow-Up Tasks (optional)
- [ ] <konkretes optionales follow-up>
- [ ] <konkretes optionales follow-up>

## References
- PR #<NUM> — <title>
- Related docs: `<path>`, `<path>`

## Extended Notes (optional)
Nur ausfüllen, wenn nötig (Risk != 🟢, Live/Governance/CI-Behavior, viele Module betroffen):
- <Edge cases / Rollback / Operator warnings / Migration notes>
