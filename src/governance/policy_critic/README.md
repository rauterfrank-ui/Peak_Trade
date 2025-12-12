# Policy Critic v0

**Read-only governance layer for automated policy review of code changes.**

## Overview

The Policy Critic is a deterministic, evidence-based governance tool that reviews proposed changes (diffs) against security, risk, and operational policies. It complements (never replaces) hard deterministic gates and can only increase friction, never reduce it.

## Key Principles

1. **Read-only**: Never modifies code, only analyzes
2. **Fail-closed**: If unavailable or unclear → deny auto-apply
3. **Evidence-first**: Every violation must reference concrete diff locations
4. **Can brake, never accelerate**: Can block auto-apply, but cannot override hard gates

## Rules (v0)

### 1. NO_SECRETS (BLOCK)
Detects secrets, API keys, and private keys in diffs. Common patterns:
- Private keys (`BEGIN PRIVATE KEY`)
- API keys (`api_key = "sk_..."`)
- AWS credentials
- Passwords

### 2. NO_LIVE_UNLOCK (BLOCK)
Blocks attempts to enable live trading or remove safety locks:
- `enable_live_trading = true`
- `live_mode_armed = true`
- Lock removal patterns
- Safety check disabling

### 3. EXECUTION_ENDPOINT_TOUCH (WARN/BLOCK)
- **BLOCK**: Changes to order execution code (`place_order`, `submit_order`)
- **WARN**: Other changes in `src/execution/`, `src/exchange/`, `src/live/`

### 4. RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION (WARN/BLOCK)
- **BLOCK**: Risk limit changes without justification in context
- **WARN**: Risk limit changes with justification provided

### 5. MISSING_TEST_PLAN (WARN)
Large changes (>50 lines) in critical paths without documented test plan

## Usage

### CLI

```bash
# Basic usage
python scripts/run_policy_critic.py \
  --diff-file changes.diff \
  --changed-files "file1.py,file2.py"

# With context (justification, test plan)
cat > context.json <<EOF
{
  "justification": "Increased limits based on 6mo backtest data",
  "test_plan": "Run integration tests + shadow mode verification",
  "author": "dev_name",
  "related_issue": "ISSUE-123"
}
EOF

python scripts/run_policy_critic.py \
  --diff-file changes.diff \
  --changed-files "config.toml" \
  --context-json context.json

# From git diff
git diff > changes.diff
python scripts/run_policy_critic.py \
  --diff-file changes.diff \
  --changed-files "$(git diff --name-only | tr '\n' ',')"
```

### Exit Codes

- `0`: No blocking violations (ALLOW or REVIEW_REQUIRED)
- `2`: Blocking violations (AUTO_APPLY_DENY)

### Output

JSON to stdout:
```json
{
  "max_severity": "BLOCK",
  "recommended_action": "AUTO_APPLY_DENY",
  "violations": [
    {
      "rule_id": "NO_SECRETS",
      "severity": "BLOCK",
      "message": "API key pattern detected...",
      "evidence": [{"file_path": "config.py", "snippet": "..."}]
    }
  ],
  "minimum_test_plan": ["Run integration tests"],
  "operator_questions": ["Why are limits changed?"],
  "summary": "Policy review: 1 blocking violation(s). Auto-apply DENIED."
}
```

Human summary to stderr (unless `--json-only`)

## Integration with bounded_auto

```python
from src.governance.policy_critic.integration import (
    run_policy_critic_subprocess,
    should_deny_auto_apply,
    merge_policy_result_into_report,
)

# Run policy critic
policy_result, exit_code = run_policy_critic_subprocess(diff_file, changed_files)

# Check if auto-apply should be denied
if should_deny_auto_apply(policy_result):
    # Force manual review
    require_manual_review = True

# Merge into promotion report
promotion_report = merge_policy_result_into_report(report, policy_result)
```

## GitHub Actions Integration

The `.github/workflows/policy_critic.yml` workflow automatically runs on PRs that touch critical paths:
- `src/live/**`
- `src/execution/**`
- `src/exchange/**`
- `src/risk/**`
- `config/**`
- `docs/governance/**`

Workflow fails (exit 2) on blocking violations.

## Testing

```bash
# Run all tests
pytest tests/governance/policy_critic/ -v

# Test specific rule
pytest tests/governance/policy_critic/test_rules.py::TestNoSecretsRule -v
```

All tests are deterministic and require no external dependencies.

## Architecture

```
src/governance/policy_critic/
├── models.py        # Data structures (PolicyCriticInput, PolicyCriticResult, etc.)
├── rules.py         # Deterministic policy rules
├── critic.py        # Main orchestration logic
├── integration.py   # Helpers for bounded_auto integration
└── README.md        # This file

scripts/
└── run_policy_critic.py  # CLI entry point

tests/governance/policy_critic/
├── test_rules.py    # Tests for individual rules
└── test_critic.py   # Tests for orchestration

.github/workflows/
└── policy_critic.yml  # GitHub Actions workflow
```

## Future Extensions (v1+)

- LLM-augmented semantic analysis (advisory only, never permissive)
- Custom rule plugins
- Integration with InfoStream for governance events
- Historical violation tracking
- Rule exemption system (with audit trail)

## Charter

See [docs/governance/LLM_POLICY_CRITIC_CHARTER.md](../../../docs/governance/LLM_POLICY_CRITIC_CHARTER.md) for full governance charter and principles.
