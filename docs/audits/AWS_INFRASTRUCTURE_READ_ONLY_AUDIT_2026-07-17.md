# AWS Infrastructure Read-Only Audit — 2026-07-17

**Status:** PARTIAL inventory (role-scoped AccessDenied on many services)  
**Authority:** `EXPLICIT_OPERATOR_DECISION`  
**Machine SSOT:** [`config/governance/aws_audit_authority_ssot_v1.json`](../../config/governance/aws_audit_authority_ssot_v1.json)

```
AWS_INFRASTRUCTURE_READ_ONLY_AUDIT_2026-07-17=true
BASE_SHA=55388134cb424227449157b051b30a1812454564
AUDIT_UTC=2026-07-17T15:06:27Z
AWS_PROFILE=peak-trade-prearm-v3-audit
AWS_ACCOUNT_ID=511913187493
AWS_PRINCIPAL_ARN=arn:aws:sts::511913187493:assumed-role/peak-trade-operator-readonly-audit-role/<SESSION_REDACTED>
AWS_REGION=eu-central-1
PROFILE_SELECTION_AUTHORITY=EXPLICIT_OPERATOR_DECISION
FALLBACK_PROFILE=peak-trade-operator-readonly-audit-user
PERMISSION_MODE=read_only
SECRET_VALUES_READ=false
AWS_MUTATIONS_PERFORMED=false
AUDIT_CLAIMS_FULL_ACCOUNT_INVENTORY=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
```

## 1. Scope and method

Read-only AWS API inventory against account `511913187493` using profile `peak-trade-prearm-v3-audit` (assumed role `peak-trade-operator-readonly-audit-role`).

- No Secrets Manager value retrieval, no Lambda invoke, no EventBridge/Scheduler mutate, no S3 object read/write, no IAM/OIDC mutations.
- Fallback profile was **not** used (canonical STS succeeded).
- This audit does **not** claim a complete account inventory: the audit role's inline policy intentionally omits most list APIs.

## 2. Repo expectations (evidence priority)

| Expected item | Repo evidence class | Notes |
|---|---|---|
| No Terraform/CloudFormation/CDK | repo-evidenced | No `*.tf` / CFN / CDK trees |
| No GitHub Actions → AWS OIDC | repo-evidenced | No `aws-actions&#47;configure-aws-credentials` |
| Export via rclone + GitHub Secrets | documented | `PT_RCLONE_CONF_B64`, `PT_EXPORT_REMOTE`, `PT_EXPORT_PREFIX` |
| Example bucket `peaktrade-exports` | documented (example) | Phase T / Phase W; may be stale vs live |
| IAM comment `pt-gh-export-consumer` | documented (orphan) | Code comment only; no ARN/policy in repo |
| Lambda / EventBridge / CloudWatch / Secrets Manager as deployed Peak_Trade runtime | stale / design-only | REAL_MARKET_247 future options; not productive deploy SSOT |
| Canonical AWS profile/account in repo before this audit | missing | Operator decision pins account/profile in this SSOT |

## 3. Live findings

### 3.1 IAM role `peak-trade-operator-readonly-audit-role`

| Field | Value |
|---|---|
| Classification | `MATCH` (exists; STS assume succeeded) |
| ARN | `arn:aws:iam::511913187493:role&#47;peak-trade-operator-readonly-audit-role` |
| Created | 2026-05-29 |
| MaxSessionDuration | 3600 |
| Description | Peak Trade remote daemon 247 scoped role |
| Attached managed policies | none |
| Inline policy | `peak-trade-operator-readonly-audit-inline-v0` |

**Trust policy principals:**

- `arn:aws:iam::511913187493:root` → `sts:AssumeRole`
- `arn:aws:iam::511913187493:user&#47;peak-trade-operator-readonly-audit-user` → `sts:AssumeRole`

**Trust observation (DRIFT / hygiene):** allowing account `root` as AssumeRole principal is broader than the explicit audit user. Not a GitHub-OIDC trust. Classified as trust-hygiene drift for the audit role, not as proven live trading authority.

**Inline policy allow surface (summary):**

- `sts:GetCallerIdentity`
- IAM read APIs (`GetRole`, `ListAttachedRolePolicies`, `GetRolePolicy`, …) on `*`
- Budgets read
- CloudWatch `Describe*` / `List*` / `Get*`
- EC2 `Describe*`

**Not granted (explains AccessDenied):** S3 list/head metadata broadly, EventBridge, Scheduler, Lambda, CloudWatch Logs, Secrets Manager, SSM DescribeParameters, CloudTrail, KMS aliases, SNS/SQS, ECR/ECS/EKS, API Gateway, IAM OIDC provider list.

### 3.2 OIDC providers

| Result | `ACCESS_DENIED` on `iam:ListOpenIDConnectProviders` |
|---|---|
| GitHub OIDC trust on audit role | not present in AssumeRole policy |
| Repo expectation | no GHA→AWS OIDC |
| Drift verdict | `UNRESOLVED` for account-wide OIDC inventory; role trust itself has no GitHub OIDC |

### 3.3 S3

| Check | Result |
|---|---|
| `ListBuckets` | `ACCESS_DENIED` |
| Direct `HeadBucket` `peaktrade-exports` | `403 Forbidden` |
| Public Access Block / encryption / versioning | not readable under this role |
| Object download | not performed |

`PUBLIC_S3_EXPOSURE_DETECTED=UNRESOLVED`

### 3.4 EventBridge / Scheduler

| API | Result |
|---|---|
| `events:ListRules` | `ACCESS_DENIED` |
| `scheduler:ListSchedules` | `ACCESS_DENIED` |

`ACTIVE_TRADING_SCHEDULE_DETECTED=UNRESOLVED` (cannot affirm absence or presence)

### 3.5 Lambda

| API | Result |
|---|---|
| `lambda:ListFunctions` | `ACCESS_DENIED` |

No invoke performed. `ACTIVE_ORDER_EXECUTION_DETECTED=UNRESOLVED` for Lambda-triggered execution.

### 3.6 CloudWatch

| API | Result |
|---|---|
| `cloudwatch:DescribeAlarms` | OK — **0** metric/composite alarms returned |
| `logs:DescribeLogGroups` | `ACCESS_DENIED` |

Missing log-group retention assessment: `NOT_VERIFIABLE` under this role.

### 3.7 Secrets Manager / SSM

| API | Result |
|---|---|
| `secretsmanager:ListSecrets` | `ACCESS_DENIED` |
| `ssm:DescribeParameters` | `ACCESS_DENIED` |
| `GetSecretValue` | **not called** (`SECRET_VALUES_READ=false`) |

### 3.8 Other

CloudTrail, KMS aliases, SNS, SQS, ECR, ECS, EKS, API Gateway list APIs: all `ACCESS_DENIED` under audit role.

## 4. Soll/Ist matrix

| ID | Expected | Classification |
|---|---|---|
| `iam_audit_role` | role `peak-trade-operator-readonly-audit-role` | `MATCH` |
| `sts_assumed_role_session` | profile assumes audit role in account `511913187493` | `MATCH` |
| `audit_role_trust_root_principal` | least-privilege AssumeRole trust | `DRIFT` |
| `s3_peaktrade_exports` | docs example bucket | `ACCESS_DENIED` |
| `no_aws_eventbridge_trading_schedule` | no AWS trading schedules (repo: GHA/manual, not AWS EB) | `NOT_VERIFIABLE` |
| `no_lambda_order_execution` | no Lambda order execution deploy | `NOT_VERIFIABLE` |

**Counts**

| Metric | Value |
|---|---|
| Repo expected resources scored | 6 |
| MATCH | 2 |
| DRIFT | 1 |
| MISSING | 0 |
| ACCESS_DENIED (API surfaces) | 16 |
| NOT_VERIFIABLE | 2 |

## 5. Safety conclusion

| Flag | Value | Rationale |
|---|---|---|
| `SECRET_VALUES_READ` | `false` | no GetSecretValue / SecureString get |
| `AWS_MUTATIONS_PERFORMED` | `false` | read-only APIs only |
| `ACTIVE_TRADING_SCHEDULE_DETECTED` | `UNRESOLVED` | EventBridge/Scheduler list denied |
| `ACTIVE_ORDER_EXECUTION_DETECTED` | `UNRESOLVED` | Lambda list denied; no invoke |
| `PUBLIC_S3_EXPOSURE_DETECTED` | `UNRESOLVED` | bucket list/PAB denied; example bucket 403 |
| `IAM_OIDC_TRUST_DRIFT_DETECTED` | `UNRESOLVED` | OIDC provider list denied; audit role has no GH OIDC |

No evidence from readable surfaces shows an active Peak_Trade trading runtime, order executor, or EventBridge trading schedule. Readable CloudWatch alarms: none. Absence cannot be proven for denied surfaces.

## 6. Next actions

### Documentary

1. Keep this audit + `aws_audit_authority_ssot_v1` as the pinned operator authority for account/profile/region.
2. Mark Phase T/W bucket name `peaktrade-exports` as example-only until a readable live match exists.
3. Document that full P3 inventory requires broader read-only IAM than the current audit inline policy.

### AWS mutation required (not performed here)

1. Expand `peak-trade-operator-readonly-audit-inline-v0` with least-privilege **read-only** list/get for: S3 (ListAllMyBuckets + GetBucket*), EventBridge/Scheduler list/get, Lambda list/get-config/policy, Logs DescribeLogGroups, SecretsManager ListSecrets (metadata only), CloudTrail DescribeTrails, IAM ListOpenIDConnectProviders.
2. Optionally tighten AssumeRole trust by removing account `root` principal if not required.

### Operator login / permission required

1. Approve policy expansion PR/change out-of-band, then re-run P3 for denied surfaces.
2. Confirm whether `peaktrade-exports` exists in another account/profile or is obsolete documentation.

## 7. Explicit non-claims

- Does **not** authorize live trading, orders, runtime bridge, or Economic Gate changes.
- Does **not** assert full AWS account inventory completeness.
- Does **not** assert consolidation or decommission of any Peak_Trade path.
