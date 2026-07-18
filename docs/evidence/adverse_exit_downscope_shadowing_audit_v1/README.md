# Adverse Exit / Downscope Shadowing Audit v1

```text
SLICE=ADVERSE_EXIT_DOWNSCOPE_SHADOWING_AUDIT_V1
BASE_MAIN=2cb140bf3121d7e474e9f8475f97750957587329
PR_5338=MERGED (squash)
BRANCH=audit/adverse-exit-downscope-shadowing-v1
PRODUCTIVE_FILES_CHANGED=false
STATUS=FAIL
RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED
LIVE_AUTHORIZED=false
ORDERS=false
```

## Phase A

PR #5338 squash-merged to `main` at `2cb140bf…` after full required-check green verification.
Remote head branch deleted. Foreign untracked / stashes untouched.

## Phase B Verdict

Productive class-F shadowing: under research `adverse < up`, downscope matches are
selected as `adverse_exit_candidate`, then mapped to `SCOPE_UNKNOWN`, so
`transition_state` never receives `DOWNSCOPE_*`. Exit PolicySignal still fires.

## Artifacts

| File | Purpose |
|------|---------|
| `audit_summary.md` | Verdict + counts |
| `authority_and_ordering_map.md` | Owners + pipeline order |
| `findings.tsv` | Classified fundstellen |
| `searched_paths.txt` | rg inventory |
| `pr_5338_merge_verification.txt` | Merge proof |
| `test_results.txt` | Focused contracts |

## Safety

Read-only audit. Evidence-only commits. No runtime/orders/live.
