# Final Downloads cleanup manifest

**Intake ID:** `20260519T221506Z`
**Repo base:** `main` @ merge of PR #3554 (`downloads_intake_20260519T195748Z`)

## Per-path decisions

| Downloads source | Repo action | External archive (outside Downloads) |
|------------------|-------------|--------------------------------------|
| `peak_trade_imported_archive_20260519T195748Z&#47;` | **No copy** — content already in `downloads_intake_20260519T195748Z` | `processed_originals&#47;peak_trade_imported_archive_20260519T195748Z&#47;` |
| `other MD'S&#47;` (4 MD) | **historical_other_md/** — DUPLICATE_SKIP vs active owners | `processed_originals&#47;other MD'S&#47;` |
| `peak_trade_cursor_direction_lock_briefing_20260519T195748Z&#47;` (3 MD) | **historical_direction_lock/** — CONFLICT_REVIEW historical only | `processed_originals&#47;peak_trade_cursor_direction_lock_briefing_2026-04-16&#47;` |
| `PEAK_TRADE_STRATEGY_VISUAL_MAP_V2_1.pdf` | **external_visual_maps/** (56 KB) | `processed_originals&#47;visual_maps&#47;` |
| `PEAK_TRADE_VISUAL_ARCHITECTURE_PACK_V3.pdf` | **external_visual_maps/** (68 KB) | `processed_originals&#47;visual_maps&#47;` |
| `Anthropic-Cybersecurity-Skills-main&#47;` | **Not vendored** — see THIRD_PARTY manifest | `third_party&#47;Anthropic-Cybersecurity-Skills-main&#47;` |
| `Anthropic-Cybersecurity-Skills-main.zip` | **Not vendored** | `third_party&#47;Anthropic-Cybersecurity-Skills-main.zip` |

## historical_other_md — file notes

| File | Decision |
|------|----------|
| `PEAK_TRADE_UPDATE_OFFICER_V0_RUNBOOK.md` | DUPLICATE_SKIP → Update Officer V0–V10 slices |
| `Peak_Trade_Workflow_Officer_Concept.md` | DUPLICATE_SKIP → `docs&#47;ops&#47;concepts&#47;WORKFLOW_OFFICER_V0_PLAN.md` |
| `Peak_Trade_Cursor_Multi_Agent_Master_Runbook_Founder_Operator.md` | DUPLICATE_SKIP → Frontdoor |
| `CURSOR_MULTI_AGENT_BRIEF.md` | HISTORICAL brief variant |

## historical_direction_lock — file notes

| File | Risk note |
|------|-----------|
| `peak_trade_cursor_direction_lock_briefing_2026-04-16.md` | Binding-direction language — **historical only** |
| `peak_trade_master_direction_lock_and_forensics_briefing_v2_2026-04-16.md` | May reference enablement — **non-authorizing** |
| `peak_trade_doubleplay_core_recovery_memo_2026-04-16.md` | Forensics/orientation — **non-authorizing** |

## SHA256 (binaries)

| File | SHA256 |
|------|--------|
| `PEAK_TRADE_STRATEGY_VISUAL_MAP_V2_1.pdf` | `8a8526faed0b2b6ccc09b2132afbfcd49849257b1e4228a12fa7f380a0b08e13` |
| `PEAK_TRADE_VISUAL_ARCHITECTURE_PACK_V3.pdf` | `2a64a352369b93bff6f38c88f5b7f1490ca4d9b621b628a0000edbc91dfd16ab` |
| `Anthropic-Cybersecurity-Skills-main.zip` | `c32d208c8b054d3da329079a27bd1d4261e4a86ece941ba80618a5df27e53cd7` |

## Secret scan (Peak_Trade text)

- **0** blocked items in Peak_Trade MD/PDF scope.
- Anthropic tree: example patterns in third-party SKILL content (not committed to repo).
