# P7 Shadow One-Shot Dry-Run Acceptance Contract v0

## 1. Purpose

This contract defines acceptance criteria for a **controlled local** P7 Shadow **one-shot** **dry-run** artifact bundle.

It is based on a successful local dry-run whose outputs are preserved as committed test fixtures under:

- `tests/fixtures/p7_shadow_one_shot_acceptance_v0/`

Passing the automated checks in this slice **does not** change operational status. It only freezes **shape and hygiene** of JSON artifacts from the approved **dry-run** code path.

## 2. Scope and boundaries

**In scope**

- One local invocation class equivalent to:

```bash
uv run python scripts/ops/p7_ctl.py run-shadow \
  --dry-run \
  --outdir <fresh-empty-outdir> \
  --spec tests/fixtures/p6/shadow_session_min_v1_p7.json
```

- **Eleven** JSON files under the outdir, matching relative paths and schemas asserted by
  `validate_p7_shadow_one_shot_artifact_bundle()` in
  `tests/ops/p7_shadow_one_shot_acceptance_bundle_v0.py`.

**Explicitly out of scope (not authorized by this document)**

- 24/7 operation, scheduling, daemon activation
- Live, Testnet, broker, exchange, or real order submission
- Treating CI/test pass as **Paper/Shadow 24/7** readiness or activation

For 24/7 preflight status and activation boundaries, see
[`PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md`](PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) (expected **BLOCKED** until a separate governed update).

## 3. PASS / FAIL

**PASS** when:

- `uv run pytest tests/ops/test_p7_shadow_one_shot_acceptance_contract_v0.py -q` exits 0.
- Bundle validator reports no `AssertionError` (exact file set, portable path strings, forbidden-token scan, required keys per artifact).

**FAIL** when:

- Any committed fixture is missing, extra, or invalid JSON.
- Any string value in bundled JSON looks like an absolute filesystem path (leading `/`).
- Concatenated bundle text matches the curated deny-list (e.g. `testnet`, `broker`, `https://`) — heuristic, not a substitute for design review.

## 4. Operator notes

- Use a **fresh empty** `--outdir`; `p7_ctl` rejects non-empty outdirs.
- After a real dry-run, compare only **relative** filenames under the outdir to the fixture set; normalize machine-specific absolute paths before committing (repo-relative strings only).
- Do not point production or personal `/tmp` trees at tests; fixtures and tests read only `tests&#47;fixtures&#47;...` and `tmp_path` copies.
- For **manual repeated** dry-runs (campaign rules, retention, stop conditions), see [P7_SHADOW_REPEATED_ONE_SHOT_DRY_RUN_GOVERNANCE_V0.md](P7_SHADOW_REPEATED_ONE_SHOT_DRY_RUN_GOVERNANCE_V0.md).

## 5. Implementation references

| Artifact | Role |
|----------|------|
| `tests&#47;fixtures&#47;p7_shadow_one_shot_acceptance_v0&#47;*.json` | Golden bundle |
| `tests/ops/p7_shadow_one_shot_acceptance_bundle_v0.py` | Validator |
| `tests/ops/test_p7_shadow_one_shot_acceptance_contract_v0.py` | Contract tests |

This document does **not** require invoking `p7_ctl` in CI; tests are static against committed fixtures.
