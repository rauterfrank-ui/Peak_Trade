# Phase B – research_cli Evidence-Chain

**Goal:** `scripts/research_cli.py` produces a reproducible evidence pack per run_id:

- `artifacts&#47;research&#47;<run_id>&#47;meta.json` (created_utc, python, platform, git_sha, git_status_porcelain, env.PEAKTRADE_SANDBOX, command, run_id)
- Subdirs: `env&#47;`, `logs&#47;`, `reports&#47;`, `plots&#47;`, `results&#47;`

## Usage

```bash
# Auto-generated run_id
python scripts/research_cli.py sweep --sweep-name rsi_reversion_basic --config config/config.toml

# Explicit run_id
python scripts/research_cli.py --run-id my_run_001 report --sweep-name rsi_reversion_basic --format both
```

## Layout (src/ops/evidence.py)

- `EVIDENCE_LAYOUT`: meta.json, env, logs, reports, plots, results
- `ensure_evidence_dirs(base_dir)` – creates base_dir and subdirs
- `write_meta(meta_path, extra)` – writes meta.json with git/python/platform and optional extra fields

## Task

- **B1:** Task-Spec `docs/ops/tasks/TASK_B1_research_cli_evidence_chain.md`
- Implementation: evidence pack skeleton + research_cli integration on branch `feat/research-cli-evidence-chain`.
