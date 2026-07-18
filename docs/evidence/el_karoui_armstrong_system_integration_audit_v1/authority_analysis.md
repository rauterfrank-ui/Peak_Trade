# Authority Analysis

## Explicit checks

| Capability | El Karoui | Armstrong OOP | Legacy `ecm_cycle` |
|---|---|---|---|
| Set Bull/Bear directly | No | No | No |
| Set LONG/SHORT directly in MV2 | No | No | No |
| Mutate Dynamic Scope | No | No | No |
| Trigger `transition_state` | No | No | No |
| Override Agreement | No | No | No |
| Bypass Risk gates | No | No | No |
| Force Quantity | No | No | No |
| Set Execution Eligibility | No (blocked) | No (blocked) | No (OBL_B05 KEEP_NONE) |
| Emit Trade Intent into kernel | No | No | No |
| Activate legacy live paths | No (gated) | No (gated) | Config-listed but not MV2 authority |

When invoked as **standalone strategies**, they **do** emit signal series (LONG/FLAT; Armstrong aggressive can SHORT; ecm emits ENTRY/EXIT). That is strategy-layer intent, not Master V2 authority.

## Path classifications

| Path | Classification |
|---|---|
| `ElKarouiVolModel` / strategy offline | `SAFE_INFORMATION_SOURCE` + local `SAFE_RISK_OR_SIZING_CONSUMER` (model-internal multipliers only) / `INACTIVE_OR_UNBOUND` vs MV2 |
| `ArmstrongCycleModel` / strategy offline | same |
| Combi experiment | `SAFE_INFORMATION_SOURCE` / `INACTIVE_OR_UNBOUND` vs MV2 |
| Double Play `ecm_or_armstrong_surface` | `SAFE_NON_AUTHORITY_PROJECTION` |
| Agreement encoding owner lists | `SAFE_NON_AUTHORITY_PROJECTION` / Consumer-only |
| Registry Spec `is_live_ready=True` while class False | `POTENTIAL_COMPETING_AUTHORITY` (metadata live-readiness / AUTH-005) — **not** confirmed MV2 system-state authority |
| Dual `ecm_cycle` vs `armstrong_cycle` identity | `POTENTIAL_COMPETING_AUTHORITY` (AUTH-001/004 identity) — wiring inventory / non-authority notes already document this |
| Confirmed MV2 competing system-state authority | **None** (`CONFIRMED_COMPETING_AUTHORITY` count for Bull/Bear/Scope/Switch = 0) |

## Competing authority count (this audit)
Count of **potential** competing identity/metadata authorities (not MV2 switch authorities): **2**
1. AUTH-001/004-style ECM vs Armstrong dual identity surfaces
2. AUTH-005-style live-readiness metadata triangle (registry vs class vs tiering) affecting both R&D strategies

`COMPETING_AUTHORITY_FOUND=true` for metadata/identity potential.
`DIRECT` MV2 system-state competing authority: **false**.

## Safety controls observed
- Class constants: `IS_LIVE_READY=False`, `TIER=r_and_d`
- `config/strategy_tiering.toml`: `allow_live=false`
- `strategy_switch_sanity_check` default R&D keys include both strategies
- Double Play suitability fail-closed on ECM/Armstrong name alone
- MV2 integration contract classifies both as `research-only`
