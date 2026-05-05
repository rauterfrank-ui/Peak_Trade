# P7 Shadow Repeated One-Shot Dry-Run Governance v0

## 1. Purpose

This runbook defines governance for manually repeated P7 Shadow one-shot dry-runs.

It does **not** authorize scheduling, daemon execution, 24/7 operation, Testnet, Live, broker access, exchange access, or order submission.

## 2. Current authorization status

Current status: **manual repeated dry-runs are not pre-authorized**.

A repeated run campaign may only start after an operator explicitly approves the campaign scope for the current session.

The following remain blocked:

- scheduler activation;
- daemon activation;
- cron, launchd, or systemd installation;
- 24/7 Paper/Shadow operation;
- Testnet operation;
- Live operation;
- broker or exchange connectivity;
- order submission.

## 3. Reused canonical surfaces

This governance runbook reuses the existing one-shot and 24/7 boundaries:

- One-shot acceptance: [P7_SHADOW_ONE_SHOT_ACCEPTANCE_CONTRACT_V0.md](P7_SHADOW_ONE_SHOT_ACCEPTANCE_CONTRACT_V0.md)
- Paper/Shadow 24/7 preflight (expected **BLOCKED**): [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md)
- `scripts/ops/p7_ctl.py`
- `scripts/ops/report_paper_shadow_247_preflight_status.py`

The one-shot acceptance contract defines the artifact-level PASS criteria.

The Paper/Shadow 24/7 preflight contract remains `BLOCKED` and must stay separate from manual repeated one-shot dry-runs.

## 4. Repeated-run campaign scope

A repeated-run campaign must define all of the following before the first run:

- campaign identifier;
- exact spec path or fixture family;
- maximum number of runs;
- maximum wall-clock duration;
- cadence between runs if more than one run is requested;
- fresh output directory root;
- artifact-retention rule;
- operator stop condition;
- maximum accepted failures;
- required post-run artifact checks;
- explicit statement that the campaign is not scheduled and not a daemon.

## 5. Output directory rules

Every run must use a fresh empty output directory.

A non-empty output directory must be rejected before runner invocation.

Output directories must be campaign-scoped, for example:

```text
/tmp/peak_trade_p7_shadow_repeated_one_shot_<campaign_id>/run_<n>/
```

Use a new `run_<n>` directory for each invocation (monotonic `n` or ISO timestamps). Do not reuse a directory after a failed or partial run.

## 6. Canonical invocation (per run)

Each run uses the same **dry-run** invocation class as the one-shot acceptance contract, with operator-chosen `--outdir` and `--spec`:

```bash
uv run python scripts/ops/p7_ctl.py run-shadow \
  --dry-run \
  --outdir <fresh-empty-outdir> \
  --spec <campaign-spec-path>
```

Non-`--dry-run` modes, network-backed flags, and broker or exchange options are out of scope for this runbook.

## 7. Per-run operator checklist

Before each run:

- Confirm the campaign record (section 4) is still valid.
- Confirm prior run artifacts are archived or deleted per retention (section 10).
- Allocate a new empty `--outdir` under the campaign root (section 5).
- Confirm no scheduler or daemon changes are pending for this workstream.

After each run:

- Inspect stderr and exit code before proceeding.
- Run the post-run checks in section 8.

## 8. Post-run artifact checks

Treat a run as **failed for governance purposes** if tooling exits non-zero, stderr shows unexpected errors, or the artifact layout does not match the one-shot contract.

**Repo CI parity:** committed fixtures are checked by:

```bash
uv run pytest tests/ops/test_p7_shadow_one_shot_acceptance_contract_v0.py -q
```

**A fresh local outdir** is not exercised by that test alone. After a run, compare filenames under the outdir to the one-shot contract and, if needed, call `validate_p7_shadow_one_shot_artifact_bundle()` from `tests/ops/p7_shadow_one_shot_acceptance_bundle_v0.py` in a REPL or small local helper—**do not** commit raw `/tmp` output.

For a **minimum** manual check: assert the **eleven** relative JSON paths listed in the one-shot acceptance contract exist under the outdir and contain no absolute path strings (leading `/`) in serialized JSON values.

## 9. Stop conditions

**STOP** the campaign and escalate if:

- any run leaves the agreed dry-run mode;
- repeated failures exceed **maximum accepted failures**;
- tooling or policy ambiguity invalidates the campaign record;
- any stakeholder requests scheduling, 24/7 operation, or Testnet/Live paths;
- preflight or org policy indicates **BLOCKED** and the campaign cannot respect that boundary.

Do not interpret a successful dry-run or passing repo tests as Paper/Shadow 24/7 approval. Check [`PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md`](PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) and `report_paper_shadow_247_preflight_status` only as **read-only** diagnostics.

## 10. Retention and hygiene

- Keep local outdirs only as long as the campaign retention rule requires; then delete or archive outside the repo.
- Do not commit personal machine paths or secrets into fixtures or docs.
- When updating golden fixtures, follow [P7_SHADOW_ONE_SHOT_ACCEPTANCE_CONTRACT_V0.md](P7_SHADOW_ONE_SHOT_ACCEPTANCE_CONTRACT_V0.md) and normalize paths to repo-relative strings.

## Repeated-run stability interpretation

Repeated-run campaign comparison must allow expected run-local volatility while still rejecting **business-critical artifact drift**.

Allowed volatility includes `created_at_utc`, run-local output paths, and **Evidence-Manifest hashes** for timestamped or path-bearing artifacts.

The campaign must fail if stable business-critical artifacts drift after volatility normalization. Stable artifacts include the Shadow session summary, the P5a trade plan advisory, P7 fills (including `p7&#47;fills.json`), and P7 account state.

## 11. Revision

- **v0** — Initial governance: manual repeated one-shot dry-runs only; no scheduler or daemon authority.
