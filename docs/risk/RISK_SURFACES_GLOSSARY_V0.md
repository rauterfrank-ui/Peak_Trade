# Risk Surfaces Glossary v0

## Authority and scope note

This glossary is **docs-only**. It changes no runtime behavior, workflow behavior, registry metadata, TOML/config, tests, evidence, market-data state, or execution path. It does not grant **Master V2** approval, **Doubleplay** authority, **First-Live** readiness, operator authorization, or permission to route orders into any live capital path.

The purpose is to preserve **usable wiring knowledge** while preventing future readers from **collapsing** distinct **risk, gate, safety, diagnostic, evidence, and promotion** surfaces into one **ambiguous** authority path. Old and new **docs** can be **provenance**; only **governed** **gate, evidence, and signoff** artifacts define **go-forward** **authority** for any live- or first-live-adjacent action.

## Canonical Master V2 target chain

The following is a **read-model** **ladder** for how **strategy, scope, risk, safety, and execution** are **often discussed** in this repo. It is **not** a single implementation module and **not** a substitute for the **full** **staged enablement** **specs** in `docs&#47;ops&#47;`.

```text
Universe Selection
-> Doubleplay Core
-> Bull Specialist + Bear Specialist
-> Strategy Embedding inside each side
-> Scope / Capital Envelope
-> Risk / Exposure Caps
-> Safety / Kill-Switches
-> staged Execution Enablement
```

## Term table (observed repo surfaces)

| Term / surface | Observed path or symbol (illustrative) | Role in one line | Authority boundary (this glossary) | Master V2 mapping (read) | Do not confuse with | Suggested handling |
|----------------|----------------------------------------|------------------|-----------------------------------|-------------------------|--------------------|--------------------|
| **Scope / Capital Envelope** | `docs&#47;ops&#47;specs&#47;MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md`, capability/scope TOML families | **Semantic** boundary: what strategies/capital lanes may run under which **capability** | **Not** a Python class; **not** a substitute for `RiskGate` or `LiveRiskLimits` | Sits **above** raw portfolio math in **ladder** language | “Risk” as generic VaR/limits in the **core `src` risk** (analytics) package only | **Adapt to M2 (read)**, **Park** in governance specs |
| **Risk / Exposure Caps** | `src&#47;risk&#47;*`, `src&#47;live&#47;risk_limits.py` (`LiveRiskLimits`), parts of `src&#47;ops&#47;gates&#47;risk_gate.py` (`RiskLimits` dataclass) | **Numeric / rule** limits: VaR, notional, exposure, session loss, etc. | Factual in code, **not** by itself a **go-live** decision | Fills the **ladder** step **after** **Scope / Envelope** in planning language | **Scope / Envelope** (semantic lane) or **safety** posture alone | **Keep** + **docs clarify** (this file) |
| **`src.risk_layer.risk_gate.RiskGate`** | `src/risk_layer/risk_gate.py` | **Order-evaluation** orchestrator: audit, optional in-process `KillSwitch` from `PeakConfig` | **Component-level**; **not** the only pre-trade layer in **live** runs | Treated as **Risk / Exposure**-adjacent **enforcement** at the **order** object | `src/ops/gates/risk_gate.py` (different module) or **eligibility** **live** gates | **Keep**, **docs clarify** |
| **`src/ops/gates/risk_gate.py`** (ops **RiskGate** / limits surface) | `src/ops/gates/risk_gate.py` | **Operational** / bounded context **pure** check using `RiskContext`, `RiskLimits`, kill-state file helpers | Factual; **name collision** with `risk_layer` **RiskGate** | Often **pilot/ops** / **bounded** paths | **`risk_layer.RiskGate`** (different design center) | **Keep**, **must not** merge names mentally |
| **execution `RiskHook` (`risk_hook`)** | `src/execution/risk_hook.py` | **Protocol** so execution **evaluates** orders **without** importing `src.risk_layer` **directly** (anti-cycle) | **Interface** contract, **not** a promotion gate | **staged Execution Enablement** (hook seam) | **VaR** suite or `RiskGate` | **Keep**; **Test-only** contract is **optional** (see `tests/execution/test_contracts_risk_hook.py`) |
| **Live gates** | `src/live/live_gates.py` (`check_*_eligibility`, `LiveGateResult`, Doubleplay integration) | **Eligibility** / **tier** / **policy** gating for strategies and portfolios | **Not** the same as **order-level** `RiskGate` | **Universe/Doubleplay**-adjacent **eligibility** | **`RiskGate.evaluate`** in `risk_layer` | **Adapt to M2 (read)** |
| **`SafetyGuard`** | `src/live/safety.py` (used from `src/execution/pipeline.py`, `live_session`) | **Pre-order** **safety** checks in **execution** / live session **flow** | **Safety** layer, not VaR backtest | **Safety / Kill-Switches** neighborhood | **`KillSwitch` package** in `risk_layer` (related theme, different wiring) | **Keep** |
| **`LiveRiskLimits`** | `src/live/risk_limits.py` | Batched order checks: notional, exposure, daily loss, etc. | **Factual** limits; not **Scope / Envelope** | **Risk / Exposure Caps** in **live** **pipeline** | `RiskLayerManager` or **only** the **core `src` risk** **analytics** | **Keep** |
| **`KillSwitch` (package)** | `src/risk_layer/kill_switch/` (e.g. `core.py`, `__init__.py` exports) | In-process and **persisted** **emergency** **state** **machine** and **triggers** | **Critical** for safety narrative; still **not** “permission to go live” | **Safety / Kill-Switches** **layer** in ladder | “Kill switch” **as** only **M2** **approval** (wrong) | **Keep**; **docs** in `docs&#47;risk&#47;KILL_SWITCH*.md` are **provenance** |
| **VaR diagnostics** | `src&#47;risk&#47;*` analytics + `src&#47;risk_layer&#47;var_backtest&#47;*` + `src&#47;risk&#47;validation&#47;*` | **Model** and **backtest** **health** (violations, rolling, **reports**) | **Diagnostics** and **evidence** support, not **promotion** by themselves | Informs **Risk / Exposure** **quality** | **M2** **acceptance** **packets** in **ops** (separate) | **Park / retain** + **Needs deeper** **audit** for mapping |
| **Kupiec POF** | `src&#47;risk_layer&#47;var_backtest&#47;kupiec_pof.py`, `src&#47;risk&#47;validation&#47;*` | **Proportion-of-failures** **test** in **backtest** **suites** | **Statistical** model check | Same **ladder** **step** as **risk** **quality** | **A single** **green** test **as** **Live** “OK” (wrong) | **Keep** |
| **Christoffersen** tests | `src/risk_layer/var_backtest/christoffersen_tests.py` + validation delegation | **Independence** / **conditional** **coverage** **tests** | **Model** **validation** | **Evidence**-grade, **not** **execution** **gate** | **Promotion** without **staged** **artifacts** (wrong) | **Keep** |
| **Duration diagnostics** | `src/risk_layer/var_backtest/duration_diagnostics.py` | **Duration** / **clustering**-style **diagnostics** in **VaR** **backtest** **context** | **Diagnostic** | **Model** **ops** and **skepticism** | **KillSwitch** (different concern) | **Keep**; see `docs&#47;risk&#47;DURATION_DIAGNOSTIC_GUIDE.md` as **provenance** |
| **staged Execution Enablement** | `src/execution/pipeline.py` (governance, env), canary/transport tests, `docs&#47;ops&#47;*` | **Gates** to **turn on** **paths** in **order** (paper/testnet/…) **per** **governance** | **Institutional** **process**; code **enforces** **locks** in places | Ladder’s **last** **read** **step** | A **single** **Risk** **class** in **Python** (wrong) | **Park** in **ops** **specs**; **this** file **clarifies** only |

| **Operator / evidence / readiness docs** | `docs&#47;ops&#47;*`, `docs&#47;risk&#47;*` | **Procedures,** **runbooks,** **evidence** **artifacts** | **Provenance**; **M2/First-Live** only via **named** **contracts** in **ops** | Cross-cut **governance** | This **glossary** as **sole** **go** (wrong) | **Keep** separate |

## Name collisions and common misreadings

1. **Two “RiskGate”-named areas:** `src/risk_layer/risk_gate.py` (**class** `RiskGate` for **order** + audit + optional in-process `KillSwitch`) is **not** the same as **`src/ops/gates/risk_gate.py`**, which hosts **separate** **dataclasses** and **pure** **operational** **risk** **checks** (e.g. `RiskContext`, `RiskLimits`, `RiskDecision` as defined **there**). **Do not** **merge** them when reading or refactoring **without** a **governed** **design** **note**.

2. **Live gates vs `RiskGate`:** **`live_gates`** answer **eligibility** / **tiering** / **policy** **questions** (often with **Doubleplay** **hooks**). **`risk_layer.RiskGate`** answers **per-order** **validation** in its **wiring** **pattern**. They are **different** **questions**.

3. **KillSwitch vs live authorization:** A **depressed** or **killed** **switch** **blocks** **trading** in its **wiring**; it does **not** **imply** the **inverse** (that an **un-killed** **state** **equals** **M2/First-Live** **permission**). **Only** current **governance** **artifacts** and **staged** **enablement** **define** that.

4. **Diagnostics vs promotion:** **Kupiec**, **Christoffersen**, **duration** **tools** **inform** **model** **risk**; they are **not** by themselves **Master V2** **readiness** or **evidence** **of** **live** **routing** **right**.

5. **Scope / Capital Envelope vs Risk / Exposure Caps:** The **envelope** is a **governance-semantic** **lane**; **exposure** **caps** are **often** **numeric** and **enforced** in **code** and **config**. **Do** **not** **collapse** **without** **proof** of **equivalence** (rarely valid globally).

## Future work (not this document)

- Any **code/config/import** **re-alignment** **requires** a **separate** **governed** **slice** **after** **read-only** **evidence** and **M2/Doubleplay** **boundary** **review** — this glossary **creates** **none** of that work by itself.  
- **Optional** **later** **test-only** **contracts** may **harden** **documented** **invariants** (e.g. **execution** **does** **not** **import** `src.risk_layer` **in** the **`RiskHook` seam**) — **see** `tests/execution/test_contracts_risk_hook.py`.  
- **No** **runtime** **changes** **follow** from **this** **glossary** **v0**.

## Related read-model docs (non-authority)

- `RISK_LAYER_ALIGNMENT.md` — alignment memo + wiring snapshot (historical + observed surfaces).  
- `RISK_LAYER_OVERVIEW.md` — architecture overview.  
- `RISK_LAYER_V1_GUIDE.md` — usage guide.  
- `docs&#47;ops&#47;specs&#47;MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md` — **Scope / Capital Envelope** (governance spec; **this** file **only** **points** to it).  

End of `RISK_SURFACES_GLOSSARY_V0.md`.
