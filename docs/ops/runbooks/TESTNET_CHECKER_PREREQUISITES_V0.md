# Testnet Checker Prerequisites v0

**Status:** ACTIVE  
**Scope:** Read-only prerequisite inventory for `check_testnet_prerequisites_readonly.py`  
**Risk:** LOW — documentation only; **non-runtime** and **non-authorizing**

## Purpose and boundaries

This runbook explains the two **operator or environment** keys that the read-only checker expects to be **present** (not validated for secret correctness) before its JSON `status` can leave `BLOCKED`.

- **Non-runtime:** Following this runbook does not start a scheduler, runtime daemon, paper runtime, paper-validation, Testnet, Live, or any broker or exchange path.
- **Non-authorizing:** Satisfying these prerequisites **does not** set `testnet_authorized`, `live_authorized`, or any execution authority. Readiness at `READY_FOR_REVIEW` remains a **review milestone only**; see `authorization_boundary_v0` in `report_paper_testnet_readiness_status.py` (readiness is not execution authority).

## Current modeled state (Paper or Testnet readiness lane)

| Concept | Expected |
|--------|----------|
| Readiness `status` | May be `READY_FOR_REVIEW` when modeled evidence plus reviewer records are complete |
| Root `testnet_authorized` | `false` |
| Root `live_authorized` | `false` |
| Checker `status` (read-only script) | `BLOCKED` until **both** keys below are present; `READY_FOR_OPERATOR_REVIEW` when present |

The checker and the readiness reporter can disagree on **wording** of status (`BLOCKED` vs `READY_FOR_REVIEW`) by design: the checker only signals **missing declared prerequisites**; the reporter aggregates broader evidence. **Neither** grants Testnet execution.

## Prerequisites (required key names)

The canonical list lives in `scripts/ops/check_testnet_prerequisites_readonly.py` (`REQUIRED_KEYS`).

### `PEAK_TRADE_TESTNET_OPERATOR_GATE_ACK`

- **Purpose:** Declares that a human operator has **explicitly acknowledged** the external Testnet review or gate process (organizational intent), separate from automated readiness JSON.
- **Expected value semantics:** Any **non-empty** value after trim is treated as **present**. The checker **does not** interpret meaning, validate tokens, or compare against secrets.
- **Secret safety:** Do **not** paste real acknowledgements into tickets or logs if they contain sensitive text. Do **not** commit `.env` files or key material. Prefer operator-held environment injection or a private ops channel, not the repo.

### `PEAK_TRADE_TESTNET_CONFIG_DECLARED`

- **Purpose:** Declares that **Testnet-facing configuration intent** exists in the environment (e.g. config is declared for a later phase). Presence is **not** proof that config is correct or safe to trade.
- **Expected value semantics:** Any **non-empty** trimmed value counts as present. No connectivity, credential, or order validation is performed.
- **Secret safety:** Never store API secrets, keys, or passwords in tracked files. Use secret managers or local setups that stay **out of git**. The checker only tests **presence**, never prints values (`value_redacted` is always true in JSON output).

## How to verify (read-only)

### Checker (canonical)

```bash
uv run python scripts/ops/check_testnet_prerequisites_readonly.py --json
```

Optional: supply an env-style file **path you control** (not committed):

```bash
uv run python scripts/ops/check_testnet_prerequisites_readonly.py --json --env-file "$HOME/your-private-path/testnet_prereqs.env"
```

Interpretation:

- `missing` empty and `status` = `READY_FOR_OPERATOR_REVIEW` → both keys resolved for **presence**.
- `checker_boundary_v0` always has `non_authorizing` true and execution flags false.

Keys are resolved from, in order: process environment, then optional `--env-file` (see script). **Do not** rely on this document to set variables; operators set them through their own secret-safe workflow.

### Readiness reporter (optional aggregation)

`uv run python scripts/ops/report_paper_testnet_readiness_status.py` accepts explicit review or record paths only (e.g. `--paper-runtime-evidence-review`, `--testnet-prerequisites-checker-report`, `--external-operator-testnet-gate-record`). It **never** runs the checker for you; pass JSON from the checker if you include that slice.

## Non-goals

- No exchange connectivity or health checks.
- No credential or API-key validation.
- No orders, routing, or Live or Testnet execution.
- No change to incident-stop artifacts or trading logic.

## Required next operator decision

Choose one path (all compatible with **non-execution**):

1. **Resolve prerequisites secret-safely** — Provide non-empty values via operator-controlled channels; re-run the checker and readiness report if needed.
2. **Stop at `READY_FOR_REVIEW`** — Keep the milestone; do not proceed toward Testnet execution until policy and environment are ready.
3. **Monitor 24h Paper observation only** — Leave Testnet work paused; do not conflate Paper observation with Testnet authorization.

## Stop line

No scheduler, runtime daemon, paper runtime, paper-validation, Testnet, Live, broker, exchange, or order-submission path is authorized by satisfying or documenting these prerequisites. This runbook is **docs-only** context for the read-only checker.
