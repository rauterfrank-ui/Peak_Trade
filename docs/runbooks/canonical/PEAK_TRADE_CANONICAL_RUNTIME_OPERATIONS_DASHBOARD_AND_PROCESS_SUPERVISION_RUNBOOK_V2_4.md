# Peak_Trade Canonical Runtime Operations, Dashboard and Process Supervision Runbook — Canonical V2.4

**DOCUMENT_CLASS:** `FORENSICALLY_RECONCILED_PROPOSED_CANONICAL_OPERATIONS_RUNBOOK`  
**STATUS:** `OWNER_REVIEW_PENDING_REPOSITORY_RATIFICATION`  
**AUTHORITY_EFFECT:** `NON_RUNTIME_AUTHORIZING`  
**SYSTEM:** `Peak_Trade`  
**PRIMARY_SCOPE:** Local runtime execution, process supervision, environment control, public market-data transport, dashboard lifecycle, OHLCV transport, observability, restart and recovery  
**CURRENT_PLATFORM_SCOPE:** `macOS_LOCAL_HOST_FIRST`  
**FUTURE_PLATFORM_SCOPE:** `TESTNET_AND_LIVE_EXECUTION_HOST_COMPATIBLE`  
**CORE_TRADING_LOGIC_CHANGE_ALLOWED:** `false`  
**LIVE_TRADING_AUTHORIZED:** `false`  
**TESTNET_AUTHORIZED:** `false`  
**PAPER_EXCHANGE_ORDERS_AUTHORIZED:** `false`  
**EXCHANGE_CREDENTIAL_USE_AUTHORIZED:** `false`  
**REAL_CAPITAL_MOVEMENT_AUTHORIZED:** `false`  
**RUNTIME_AUTHORIZATION_EFFECT:** `NONE`  
**FORENSIC_BASELINE_HEAD:** `b0e882b9714a615f633fb09b8ee4f9a19f54d470`  
**FORENSIC_BASELINE_BRANCH:** `main`  
**FORENSIC_CAPABILITY:** `CAPABILITY_O0_FORENSIC_RUNTIME_DASHBOARD_AND_PROCESS_TOPOLOGY_AUDIT_V1`  
**STALE_IF_HEAD_DIFFERS:** `true`  
**DOCUMENT_VERSION:** `V2.4`  
**CANONICAL_REPOSITORY_PATH:** `docs/runbooks/canonical/PEAK_TRADE_CANONICAL_RUNTIME_OPERATIONS_DASHBOARD_AND_PROCESS_SUPERVISION_RUNBOOK_V2_4.md`  
**REVISION_CLASS:** `DOCUMENTATION_ONLY_VERSION_NORMALIZATION_AND_REPOSITORY_RATIFICATION`  
**AUTHORITY_CLASSIFICATION:** `DERIVED_DOMAIN_AUTHORITY_ONLY`  
**MASTER_RUNBOOK_PATH:** `docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md`  
**MASTER_RUNBOOK_IS_ONLY_SSOT:** `true`  
**RUNTIME_OPERATIONS_RUNBOOK_IS_SSOT:** `false`  

---

# 0. Purpose

This runbook records the forensically established current topology and defines the target operating model for Peak_Trade runtime execution and observability.

It exists because long-running sessions, public-market-data transport, dashboard startup, OHLCV delivery, PTY handling, proxy inheritance, process lifetime and operator tooling have repeatedly behaved differently depending on how and where they were started.

The problem is not limited to one proxy variable or one failed session. The operating surface must be treated as one coherent system:

```text
Operator / Automation
→ Canonical Launcher
→ Environment Validation
→ Runtime Authorization Boundary
→ Process Supervisor
→ Market-Data Runtime
→ Canonical State and Evidence
→ Read Model / Stream Projection
→ Dashboard Backend
→ Dashboard Frontend
→ Health, Recovery and Audit
```

The target is one reproducible, supervised and testable operational path for:

```text
PUBLIC_MD_NO_ORDER
INTERNAL_SIMULATED_EXECUTION
DASHBOARD_READ_ONLY
FUTURE_TESTNET
FUTURE_LIVE
```

The execution mode may differ, but process ownership, environment semantics, lifecycle handling, health reporting and audit rules must remain consistent.

---

# 1. Prime Directive

Peak_Trade must not depend on ad hoc shell behavior, Cursor tool-shell lifetime, inherited proxy state, manually improvised PTY wrappers or untracked background processes.

Mandatory target:

```text
ONE_CANONICAL_LOCAL_LAUNCH_PATH=true
ONE_ENVIRONMENT_CONTRACT=true
ONE_PROCESS_SUPERVISION_MODEL=true
ONE_HEALTH_MODEL=true
ONE_SHUTDOWN_AND_RECOVERY_MODEL=true
ONE_DASHBOARD_DATA_CONTRACT=true
ONE_OHLCV_TRANSPORT_CONTRACT=true
NO_CURSOR_SHELL_LIFETIME_DEPENDENCY=true
NO_AD_HOC_DAEMONIZATION=true
NO_UNDECLARED_PROXY_INHERITANCE=true
NO_DASHBOARD_TRADING_AUTHORITY=true
```

---

# 2. Non-Authorization Boundary

This runbook does not authorize:

```text
LIVE_TRADING
TESTNET_EXECUTION
PAPER_EXCHANGE_ORDERS
EXCHANGE_CREDENTIAL_USE
PRIVATE_EXCHANGE_ENDPOINTS
REAL_CAPITAL_MOVEMENT
RISK_LIMIT_CHANGES
STRATEGY_CHANGES
MASTER_V2_CHANGES
DOUBLE_PLAY_CHANGES
BULL_BEAR_CHANGES
DYNAMIC_SCOPE_CHANGES
REGIME_THRESHOLD_CHANGES
```

All work under this runbook must preserve:

```text
CORE_LOGIC_CHANGE=false
LIVE_PATH_CHANGED=false
TESTNET_PATH_CHANGED=false
ORDER_SIDE_EFFECT_OCCURRED=false
EXCHANGE_CREDENTIAL_PATH_CHANGED=false
```

---

# 3. Forensically Established Current State

The O0 strict read-only forensic audit completed against repository head:

```text
FORENSIC_STATUS=FORENSIC_COMPLETE
FORENSIC_VERDICT=TOPOLOGY_RECONCILED_WITH_GAPS
FORENSIC_HEAD=b0e882b9714a615f633fb09b8ee4f9a19f54d470
FORENSIC_BRANCH=main
REPOSITORY_MUTATED=false
PROCESS_INTERFERENCE=false
MATCHING_RUNTIME_OR_DASHBOARD_PROCESSES_OBSERVED=none
```

The absence of matching processes in the audit snapshot is not evidence that the governed one-hour session did not exist at another time or under a non-matching process identity. It means only that O0 did not establish a live process topology from that snapshot.

## 3.1 Established operational symptoms

```text
LINUX_SPECIFIC_LAUNCH_ASSUMPTIONS_ON_MACOS=true
SETSID_COMMAND_NOT_PORTABLE=true
PTY_WRAPPER_FAILURE_OBSERVED=true
HEREDOC_STDIN_COLLISION_OBSERVED=true
CURSOR_PROXY_ENV_INHERITANCE_OBSERVED=true
PROXY_BOUNDARY_ABORT_OBSERVED=true
SHORT_LIVED_TOOL_SHELL_PROCESS_DEATH_OBSERVED=true
DASHBOARD_STARTUP_INSTABILITY_REPORTED=true
OHLCV_REALTIME_DELIVERY_INSTABILITY_REPORTED=true
MARKET_DASHBOARD_END_TO_END_TRUST_LOW=true
```

## 3.2 Established topology truth

```text
CURRENT_AUTHORIZED_MARKET_DASHBOARD=GET_/market_LANDSCAPE_V2_READ_ONLY_CONSUMER
CURRENT_DASHBOARD_HOST=scripts/run_web_dashboard.py
CURRENT_DASHBOARD_BACKEND=src/webui/app.py
CURRENT_DASHBOARD_FRONTEND=market_landscape_v2.html_PLUS_JS_PLUS_CSS
CURRENT_OHLCV_DASHBOARD_TRANSPORT=HTTP_JSON_POLL
MARKET_DASHBOARD_WEBSOCKET_PRESENT=false
MARKET_DASHBOARD_SSE_PRESENT=false
LEGACY_SSE_PRESENT=true_for_live_web_log_stream_only
DASHBOARD_AUTHORITY_EFFECT=NONE
TRADING_RUNTIME_ACTIVATED_BY_DASHBOARD=false
DEDICATED_MARKET_DASHBOARD_SUPERVISOR_PRESENT=false
PRODUCT_PTY_CONTROL_SURFACE_PRESENT=false
CONFIRM_TOKEN_FAMILIES_MULTIPLE=true
UNIFIED_RUNTIME_LOG_ROOT_PRESENT=false
PARALLEL_DASHBOARD_STACKS_PRESENT=true
```

## 3.3 Current defect classification

```text
TRADING_LOGIC_DEFECT=NOT_ESTABLISHED
MARKET_DATA_ALGORITHM_DEFECT=NOT_ESTABLISHED
OPERATING_MODEL_GAP=ESTABLISHED
PROCESS_SUPERVISION_GAP=ESTABLISHED
ENVIRONMENT_CONTROL_GAP=ESTABLISHED
MACOS_PORTABILITY_GAP=ESTABLISHED
DASHBOARD_LIFECYCLE_GAP=ESTABLISHED
DASHBOARD_TRANSPORT_IMPLEMENTATION=HTTP_POLL_CONFIRMED
OHLCV_PROJECTION_PATH=CONFIRMED_WITH_SEPARATE_RUNTIME_AND_DASHBOARD_PRODUCER_FAMILIES
READ_MODEL_AUTO_BINDING=PARTIAL
CONFIRM_TOKEN_FAMILY_FRAGMENTATION=ESTABLISHED
PTY_PRODUCT_LAYER_GAP=NOT_A_DEFECT_UNLESS_EXPLICITLY_REQUIRED
```

## 3.4 Named-document reconciliation

At the forensic baseline, no repository document with the exact canonical name represented by this file was found. Therefore:

```text
NAMED_CANONICAL_RUNTIME_OPERATIONS_RUNBOOK_PRESENT_AT_BASELINE=false
THIS_FILE_REPOSITORY_AUTHORITY_BEFORE_RATIFICATION=NONE
MASTER_RUNBOOK_REMAINS_SUPERIOR_AUTHORITY=true
REPOSITORY_RATIFICATION_REQUIRED=true
```

# 3A. Forensic Current-Topology Inventory

This section records current repository truth. It is descriptive, not an authorization to keep duplicate or legacy paths indefinitely.

## 3A.1 Dashboard hosts and surfaces

```text
CANONICAL_CURRENT_MARKET_SURFACE:
  launcher=scripts/run_web_dashboard.py
  app=src/webui/app.py
  route=GET /market
  ohlcv_api=GET /api/market/landscape/ohlcv
  authority=READ_ONLY_CONSUMER
  lifecycle=manual_dev_uvicorn
  dedicated_supervisor=false

PARALLEL_LEGACY_WEB_STACK:
  launchers=scripts/serve_live_dashboard.py,scripts/live_web_server.py
  app=src/live/web/app.py
  authority=READ_ONLY_OBSERVER
  classification=NON_CANONICAL_PARALLEL_STACK

OTHER_OBSERVER_SURFACES:
  /ops
  /observability
  Double-Play JSON
  R&D surfaces
  execution-watch surfaces
  paper-shadow summary
  knowledge API
  health and CI/ops surfaces
```

The former legacy Market Dashboard product is tombstoned and must not be resurrected without explicit Owner authorization.

## 3A.2 Runtime launch families

Current repository launch families include:

```text
DEVELOPMENT_WEB_HOSTS
REVIEW_AND_PLAYWRIGHT_HOSTS
OFFLINE_EVIDENCE_RUNNERS
GOVERNED_PUBLIC_MD_NO_ORDER_RUNNERS
PAPER_SHADOW_AUTHORIZATION_RUNNERS
OKX_NATIVE_PUBLIC_MD_BINDINGS
OPS_AND_LAUNCHD_OBSERVABILITY_RUNNERS
```

Many `scripts&#47;ops&#47;run_*` files are evidence or capability runners. They are not automatically canonical long-lived process supervisors.

## 3A.3 Read-model ownership

```text
ARCHIVE_ROOT_OWNER=workflow_dashboard_archive_root_v1
DARWIN_DEFAULT_ROOT=~/Library/Application Support/Peak_Trade/workflow_dashboard_v1
REPO_LOCAL_RUNTIME_AS_DASHBOARD_ARCHIVE_TRUTH_ALLOWED=false
UNIVERSE_READMODEL=universe_selection_readmodel.v1.json
OHLCV_READMODEL=okx_selected_instrument_ohlcv_readmodel.v1.json
LANDSCAPE_AGGREGATE=MarketDashboardReadServiceV1
LANDSCAPE_AGGREGATE_IS_SSOT=false
```

Current binding state:

```text
AUTO_OR_DURABLE_BOUND=universe_selection,ohlcv
EXPLICIT_INJECTION_OR_PARTIAL_BINDING=most_trading_projection_slots
NOT_BOUND=autonomy_stage,diagnostics_summary
MISSING_DURABLE_PRODUCER=event_decision_timeline
CANONICAL_CONFIDENCE_FIELD_PRESENT=false
```

`MISSING_SOURCE` is expected where no canonical producer or injection exists; it must not be silently rendered as healthy data.

## 3A.4 OHLCV current path

```text
SERVER_PUBLIC_CLIENT=OkxPublicMarketDataClientV1
PUBLIC_ENDPOINTS=/api/v5/market/candles,/api/v5/market/trades
DASHBOARD_MATERIALIZER=okx_selected_instrument_ohlcv_readmodel_v1.py
OPERATOR_REFRESH=scripts/ops/refresh_okx_market_dashboard_v1.py
CONTINUOUS_REFRESH_DEFAULT_POLL_SECONDS=3
BROWSER_DIRECT_OKX_ACCESS=false
DASHBOARD_TRANSPORT=HTTP_JSON_POLL
SPOT_OR_BTC_WRONG_PRODUCT_BINDING_BLOCKED=true
CREDENTIALS_REQUIRED=false
```

The productive public-MD runtime and the dashboard OHLCV materializer are separate families at the forensic baseline. Their truth, timing and ownership must be reconciled before claiming one end-to-end canonical stream.

## 3A.5 Process supervision current state

Repository launchd/systemd templates and supervisors exist for online-readiness, status dashboards, soak watches, audit runners and operations loops. They do not currently establish a dedicated lifecycle owner for the Market Landscape V2 uvicorn host.

```text
MARKET_DASHBOARD_START_OWNER=manual
MARKET_DASHBOARD_STOP_OWNER=manual_process_stop
MARKET_DASHBOARD_RESTART_OWNER=manual
MARKET_DASHBOARD_DUPLICATE_START_GUARD=NOT_ESTABLISHED
MARKET_DASHBOARD_CALLER_INDEPENDENT_LIFETIME=NOT_ESTABLISHED
```

## 3A.6 Confirm-token families

The repository contains multiple token families, including productive PSO paths, research/S03 hidden-input paths and live-armed paths. Cross-family substitution is forbidden.

```text
CONFIRM_TOKEN_FAMILY_MUST_BE_EXPLICIT=true
TOKEN_PURPOSE_MUST_MATCH_CAPABILITY=true
TOKEN_FILE_PATH_IS_SENSITIVE=true
TOKEN_FILE_PLAINTEXT_AT_REST_ALLOWED_ONLY_WHERE_CURRENT_CONTRACT_EXPLICITLY_REQUIRES=true
TOKEN_FILE_MODE_0600_MINIMUM=true
TOKEN_FILE_MUST_NOT_ENTER_EVIDENCE_OR_GIT=true
```

## 3A.7 Proxy naming separation

Three unrelated meanings must never be conflated:

```text
HTTP_EGRESS_PROXY=environment/network boundary concern
NO_PROXY_PROMOTION=typed-volatility semantic authority rule
OHLCV_PROXY_STRATEGY=Bouchaud research naming only
```

For governed public-MD paths, uppercase and lowercase HTTP proxy variables remain fail-closed unless a future canonical mode explicitly ratifies another policy.

# 4. Canonical Operational Architecture

## 4.1 Target graph

```text
Owner / Operator / Approved Automation
→ Canonical Command Surface
→ Preflight and Integrity Validation
→ Sanitized Explicit Environment
→ Authorization and Confirm-Token Boundary
→ Process Supervisor
→ Runtime Process Group
   ├─ Market-Data Ingestion
   ├─ Canonical Trading Runtime
   ├─ Persistence / Evidence Writer
   ├─ Read-Model Projector
   ├─ Dashboard Backend
   └─ Health / Metrics Exporter
→ Operator Read-Only Dashboard
```

## 4.2 Authority separation

```text
TRADING_RUNTIME = decision authority
PERSISTENCE = durable state authority
READ_MODEL = derived projection only
DASHBOARD_BACKEND = read-serving boundary only
DASHBOARD_FRONTEND = read-only operator interface
PROCESS_SUPERVISOR = lifecycle authority only
LAUNCHER = startup policy authority only
```

Forbidden flows:

```text
Dashboard → Trading decision
Dashboard → Direct order
Read model → Canonical state overwrite
Supervisor → Alpha mutation
Launcher → Strategy mutation
Venue adapter → Decision mutation
```

---

# 5. Canonical Launcher Contract

## 5.1 Current host and target launcher

The current Market Landscape V2 host is:

```text
scripts/run_web_dashboard.py
```

It is the sole current Market Dashboard host for `/market`, but it is not yet a complete process-supervision control plane. The future repository-owned launcher must become the supported lifecycle entrypoint for all canonical long-running components.

Target canonical surface:

```text
scripts/ops/peak_trade_runtime.py
```

Proposed subcommands:

```text
preflight
start
status
health
logs
stop
restart
recover
verify
```

Proposed modes:

```text
public-md-no-order
dashboard-only
runtime-and-dashboard
shadow
internal-simulated
future-testnet
future-live
```

Future modes remain unauthorized until separately ratified.

## 5.2 Launcher invariants

```text
REAL_LOCAL_REPOSITORY_REQUIRED=true
REAL_DOT_GIT_REQUIRED=true
EXPECTED_SHA_REQUIRED=true
CONFIG_DIGEST_REQUIRED=true
MODE_EXPLICIT=true
SESSION_ID_EXPLICIT=true
NO_IMPLICIT_FALLBACK=true
NO_CURSOR_SANDBOX_GIT=true
NO_CURSOR_TOOL_SHELL_LIFETIME_DEPENDENCY=true
PORTABILITY_VALIDATED=true
```

## 5.3 No shell-fragment authority

Commands such as the following must not become the operational contract:

```text
nohup ... &
setsid ...
script ...
python -c 'os.setsid(...)'
ad hoc heredoc launchers
manual export chains
untracked PID guessing
```

They may be used only inside a repository-owned, tested launcher implementation, never as the operator-facing canonical procedure.

---

# 6. Environment Contract

## 6.1 Allowlist-first environment

The launcher must construct the runtime environment from an explicit allowlist rather than inheriting the complete parent shell environment.

Required categories:

```text
PATH
PYTHONPATH
PYTHONUNBUFFERED
MPLCONFIGDIR
runtime mode
repository SHA
config path and digest
session ID
authorization references
public network permission flag
logging paths
state paths
health endpoints
```

Everything else must be either rejected, stripped or explicitly classified.

## 6.2 Proxy policy

Proxy semantics must be explicit per mode.

For current public-market-data no-order sessions:

```text
HTTP_PROXY_ALLOWED=false
HTTPS_PROXY_ALLOWED=false
ALL_PROXY_ALLOWED=false
http_proxy_ALLOWED=false
https_proxy_ALLOWED=false
all_proxy_ALLOWED=false
NO_PROXY_POLICY=EXPLICITLY_DEFINED_BY_VALIDATOR
no_proxy_POLICY=EXPLICITLY_DEFINED_BY_VALIDATOR
```

The launcher and validator must agree exactly on whether `NO_PROXY` and `no_proxy` are absent or set. The operator must never be told to set values that the runtime later rejects.

Required output:

```text
ENVIRONMENT_POLICY_ID
ENVIRONMENT_DIGEST
PROXY_POLICY_RESULT
REJECTED_ENV_KEYS
SANITIZED_ENV_KEYS
EFFECTIVE_ENV_KEYS
```

## 6.3 Environment drift protection

```text
PARENT_ENV_DIGEST_CAPTURED=true
EFFECTIVE_ENV_DIGEST_CAPTURED=true
UNEXPECTED_ENV_KEY_FAILS_CLOSED=true
RESTART_ENV_MATCH_PROVEN=true
DASHBOARD_ENV_MATCH_PROVEN=true
```

---

# 7. macOS Process Supervision Contract

## 7.1 Platform-native design

The macOS path must not assume Linux utilities are installed.

Required decision:

```text
LOCAL_SUPERVISION_BACKEND = launchd | repository_owned_supervisor
```

The final backend must be chosen after forensic review and a bounded proof of both options.

Preferred long-term direction:

```text
launchd for persistent host-level supervision
repository-owned CLI for configuration, status and lifecycle control
```

## 7.2 Process-group ownership

Each runtime session must have:

```text
SUPERVISOR_INSTANCE_ID
SESSION_ID
PROCESS_GROUP_ID
MAIN_PID
CHILD_PID_SET
START_TIME
EXPECTED_DURATION
MODE
REPOSITORY_SHA
CONFIG_DIGEST
AUTHORIZATION_ID_IF_APPLICABLE
HEARTBEAT_PATH
LOG_ROOT
STATE_ROOT
EVIDENCE_ROOT
```

## 7.3 Lifecycle invariants

```text
PROCESS_SURVIVES_CALLER_EXIT=true
PROCESS_SURVIVES_CURSOR_TOOL_COMPLETION=true
PROCESS_GROUP_TERMINATION_DETERMINISTIC=true
ORPHAN_PROCESS_DETECTION=true
DUPLICATE_SESSION_START_BLOCKED=true
SINGLE_WRITER_ENFORCED=true
PID_REUSE_SAFE=true
STALE_PID_FILE_SAFE=true
```

## 7.4 Startup states

```text
OFF
PREFLIGHT
ENV_VALIDATED
AUTH_VALIDATED
STARTING
RUNNING
DEGRADED
STOPPING
STOPPED
FAILED
RECOVERING
OWNER_LOCKED
```

Every transition requires:

```text
reason_code
timestamp
previous_state
new_state
session_id
process_identity
evidence reference
```

---

# 8. Secure Input and Confirm-Token Contract

## 8.1 Current forensic truth

```text
PRODUCT_PTY_PROTOCOL_OWNER_PRESENT=false
GETPASS_OR_HIDDEN_STDIN_PRESENT=true
PEXPECT_OR_PTY_SPAWN_PRODUCT_ENTRYPOINT_PRESENT=false
```

A PTY is currently an execution-environment property, not a Peak_Trade product component. This runbook must not claim that a repository-owned PTY control plane already exists.

## 8.2 Explicit channel ownership

The system must distinguish:

```text
CONTROL_STDIN
SECURE_TOKEN_INPUT
RUNTIME_STDOUT
RUNTIME_STDERR
OPERATOR_TERMINAL
BACKGROUND_PROCESS_IO
```

A heredoc, pipe or wrapper may not silently replace or consume the hidden input channel required by the selected token family.

## 8.3 Confirm-token family matrix

Every authorization-consuming command must declare:

```text
CONFIRM_TOKEN_FAMILY
CONFIRM_TOKEN_PURPOSE
CONFIRM_TOKEN_MINT_PATH
CONFIRM_TOKEN_INPUT_CHANNEL
CONFIRM_TOKEN_STORAGE_POLICY
CONFIRM_TOKEN_EXPIRY_OR_SINGLE_USE_POLICY
```

Cross-family use is forbidden. In particular, productive PSO, research/S03 and future live-armed tokens are not interchangeable.

## 8.4 Secret-handling requirements

```text
CANONICAL_MINT_PATH_USED=true
PLAINTEXT_TOKEN_NOT_LOGGED=true
PLAINTEXT_TOKEN_NOT_IN_PROCESS_ARGS=true
PLAINTEXT_TOKEN_NOT_IN_SHELL_HISTORY=true
PLAINTEXT_TOKEN_NOT_COMMITTED=true
PLAINTEXT_TOKEN_NOT_PACKAGED_AS_EVIDENCE=true
HIDDEN_INPUT_CHANNEL_VERIFIED=true
TOKEN_FILE_PATH_TREATED_AS_SENSITIVE=true
TOKEN_FILE_MODE_0600_IF_FILE_HANDOFF_USED=true
TOKEN_FILE_DELETION_VERIFIED_AFTER_CONSUMPTION=true
TOKEN_FILE_PARENT_DIRECTORY_MODE_0700=true
TOKEN_FILE_CREATED_ATOMIC_EXCLUSIVE=true
TOKEN_FILE_SYMLINK_FOLLOW_FORBIDDEN=true
TOKEN_FILE_EXISTING_TARGET_REJECTED=true
TOKEN_FILE_OWNER_UID_VERIFIED=true
TOKEN_FILE_REGULAR_FILE_VERIFIED=true
TOKEN_FILE_PATH_OUTSIDE_REPOSITORY=true
TOKEN_FILE_PATH_OUTSIDE_EVIDENCE_ROOT=true
TOKEN_FILE_CLEANUP_ON_SUCCESS_FAILURE_AND_SIGNAL=true
```

`PLAINTEXT_TOKEN_IN_MEMORY_ONLY=true` is the preferred target. Where an existing ratified path temporarily requires a mode-0600 token file, that exception must be explicit, capability-scoped, short-lived and verified deleted.

## 8.5 Non-interactive secure orchestration

The target launcher should support secure non-interactive orchestration without asking the Owner to expose or manually retype token material. A repository-owned PTY subsystem is optional; secure hidden-input semantics are mandatory.

A manual prompt is permitted only when repository-enforced security makes safe automation technically impossible.

# 9. Market-Data Transport Contract

## 9.1 Separation of concerns

```text
EXCHANGE_PUBLIC_MD_CLIENT
→ NORMALIZED_MARKET_EVENT
→ DISTINCT_OBSERVATION_ACCEPTOR
→ CANONICAL_MARKET_STATE
→ READ_MODEL_PROJECTOR
→ VERSIONED_READ_MODEL
→ DASHBOARD_HTTP_POLL_API
```

The dashboard must not consume exchange-native payloads directly if canonical normalized events already exist.

## 9.2 Required event fields

At minimum:

```text
instrument_id
venue
market_event_time
ingestion_time
observation_identity
sequence_or_source_identity
price fields
volume fields
interval
quality status
staleness status
source connection state
repository SHA
config digest
runtime session ID
```

## 9.3 Delivery semantics

The transport must define one of:

```text
AT_MOST_ONCE
AT_LEAST_ONCE_WITH_DEDUPLICATION
EXACTLY_ONCE_EFFECTIVELY
```

For dashboard/read-model materialization and HTTP polling, the expected practical target is:

```text
AT_LEAST_ONCE_WITH_DEDUPLICATION
```

Mandatory invariants:

```text
DUPLICATE_EVENT_DOES_NOT_ADVANCE_STATE=true
OUT_OF_ORDER_EVENT_CLASSIFIED=true
STALE_EVENT_VISIBLE=true
DISCONNECTED_STATE_VISIBLE=true
NO_FABRICATED_LIVE_STATE=true
```

---

# 10. OHLCV Matrix Contract

## 10.1 Canonical ownership

The OHLCV matrix must have one canonical producer and one documented projection path.

```text
RAW_OR_NORMALIZED_MARKET_EVENTS
→ CANONICAL_BAR_AGGREGATOR
→ VERSIONED_OHLCV_STATE
→ READ_MODEL
→ DASHBOARD
```

The dashboard must not independently recompute bars using separate timing or aggregation rules unless explicitly classified as a non-authoritative visual approximation.

## 10.2 Required semantics

For every interval:

```text
interval_id
bar_open_time
bar_close_time
first_event_identity
last_event_identity
open
high
low
close
volume
trade_or_sample_count
finalized
revision
quality_status
source_session_id
```

## 10.3 Live update semantics

The contract must distinguish:

```text
IN_PROGRESS_BAR
FINALIZED_BAR
CORRECTED_BAR
MISSING_BAR
STALE_BAR
```

Mandatory behavior:

```text
IN_PROGRESS_BAR_CAN_UPDATE=true
FINALIZED_BAR_IMMUTABLE_UNLESS_CORRECTION_CONTRACT=true
CORRECTION_INCREMENTS_REVISION=true
DASHBOARD_SHOWS_FINALIZATION_STATE=true
DASHBOARD_SHOWS_LAST_EVENT_TIME=true
DASHBOARD_SHOWS_TRANSPORT_LAG=true
```

## 10.4 Matrix integrity

```text
NO_INTERVAL_CROSS_CONTAMINATION=true
NO_INSTRUMENT_CROSS_CONTAMINATION=true
NO_DUPLICATE_FINALIZATION=true
NO_SILENT_GAP_FILL=true
NO_LOCAL_BROWSER_TIME_AUTHORITY=true
```

---

# 11. Read Model and Dashboard Contract

## 11.1 Read-model requirement

The dashboard must consume a dedicated read model instead of querying mutable runtime internals or reconstructing trading truth independently.

```text
CANONICAL_STATE
→ READ_MODEL_PROJECTOR
→ VERSIONED_READ_MODEL
→ DASHBOARD_API
→ DASHBOARD_UI
```

## 11.2 Dashboard authority

```text
READ_ONLY_CONSUMER=true
TRADING_INPUT=false
SSOT=false
AUTHORITY_EFFECT=NONE
DIRECT_ORDER_SUBMIT=false
DIRECT_RUNTIME_STATE_MUTATION=false
```

## 11.3 Current canonical route and transport

```text
CANONICAL_MARKET_ROUTE=GET /market
CANONICAL_OHLCV_API=GET /api/market/landscape/ohlcv
TRANSPORT=HTTP_JSON_POLL
WEBSOCKET_REQUIRED=false
SSE_REQUIRED=false
BROWSER_DIRECT_VENUE_ACCESS=false
```

WebSocket or SSE adoption requires a separate capability and must not be treated as a closure prerequisite for the current Landscape V2 contract.

## 11.4 Dashboard lifecycle

The dashboard stack must have explicit components:

```text
DASHBOARD_BACKEND
DASHBOARD_FRONTEND
STREAM_OR_POLL_TRANSPORT
READ_MODEL_STORE
HEALTH_ENDPOINT
```

Each component requires independent status, logs and restart behavior.

## 11.5 Real-time definition

“Live” or “real-time” must not be used without a measured contract.

Required metrics:

```text
source_event_age_ms
ingestion_latency_ms
projection_latency_ms
transport_latency_ms
render_latency_ms
end_to_end_latency_ms
last_successful_update
poll_connection_state
reconnect_count
dropped_event_count
duplicate_event_count
out_of_order_event_count
```

Suggested classification to be ratified after measurement:

```text
REALTIME_HEALTHY
REALTIME_DEGRADED
STALE
DISCONNECTED
REPLAYING
```

## 11.6 No green dashboard on stale data

```text
STALE_DATA_MUST_BE_VISIBLE=true
DISCONNECTED_STATE_MUST_BE_VISIBLE=true
LAST_UPDATE_TIME_MUST_BE_VISIBLE=true
SOURCE_SESSION_ID_MUST_BE_VISIBLE=true
REPOSITORY_SHA_MUST_BE_VISIBLE=true
CONFIG_DIGEST_MUST_BE_VISIBLE=true
```

---

# 12. Health, Heartbeat and Observability

## 12.1 Component health

Each long-running component must emit:

```text
process_alive
heartbeat_time
last_success_time
last_error_time
error_class
restart_count
input_lag
output_lag
queue_depth
state_commit_position
evidence_cursor
```

## 12.2 Composite health

The system health must be derived, not guessed:

```text
HOST_HEALTH
MARKET_DATA_HEALTH
RUNTIME_HEALTH
PERSISTENCE_HEALTH
READ_MODEL_HEALTH
DASHBOARD_BACKEND_HEALTH
DASHBOARD_FRONTEND_HEALTH
END_TO_END_DATA_HEALTH
```

## 12.3 Health authority

Health may block startup or trigger degradation but must not alter trading decisions.

```text
HEALTH_HAS_ALPHA_AUTHORITY=false
HEALTH_MAY_BLOCK_NEW_ENTRY=true_only_via_canonical_safety_contract
HEALTH_MAY_TRIGGER_RESTART=true_only_via_pre_ratified_policy
```

---

# 13. Logging and Audit Contract

## 13.1 Structured logs

All components must use structured logs with:

```text
timestamp
level
component
session_id
process_id
repository_sha
config_digest
event_type
reason_code
correlation_id
```

## 13.2 Secret safety

```text
SECRETS_IN_LOGS=false
CONFIRM_TOKEN_IN_LOGS=false
AUTHORIZATION_SECRET_IN_LOGS=false
EXCHANGE_CREDENTIALS_IN_LOGS=false
```

## 13.3 Log roots

Target canonical layout:

```text
var/runtime/<session_id>/
  supervisor/
  market_data/
  trading_runtime/
  read_model/
  dashboard_backend/
  dashboard_frontend/
  health/
```

Repository tracking policy must be explicit. At the forensic baseline, no single unified product log-root owner exists. Runtime logs should generally remain outside tracked source paths, while verified evidence packages may be materialized under `docs&#47;evidence&#47;` according to existing contracts.

---

# 14. Shutdown, Restart and Recovery

## 14.1 Graceful shutdown

```text
STOP_REQUESTED
→ NEW_INPUT_BLOCKED
→ IN_FLIGHT_WORK_DRAINED_OR_CLASSIFIED
→ STATE_COMMITTED
→ EVIDENCE_CURSOR_UPDATED
→ CHILDREN_STOPPED
→ SUPERVISOR_STOPPED
→ FINAL_STATUS_WRITTEN
```

## 14.2 Crash recovery

```text
PROCESS_CRASH_DETECTED
→ SESSION_FENCED
→ STATE_AND_WRITER_CHECK
→ RECONCILIATION
→ RECOVERY_POLICY_EVALUATION
→ RESTART_OR_OWNER_LOCK
```

## 14.3 Recovery invariants

```text
NO_DUPLICATE_CONFIRMATION_ADVANCE=true
NO_DUPLICATE_FILL=true
NO_DUPLICATE_BAR_FINALIZATION=true
NO_DUPLICATE_READ_MODEL_COMMIT=true
NO_STALE_DASHBOARD_GREEN_STATE=true
RECONCILIATION_BEFORE_ALPHA=true
```

---

# 15. Failure Taxonomy

Required classes:

```text
ENVIRONMENT_POLICY_FAILURE
PROXY_POLICY_FAILURE
PLATFORM_PORTABILITY_FAILURE
PTY_BINDING_FAILURE
TOKEN_INPUT_FAILURE
PROCESS_START_FAILURE
PROCESS_LIFETIME_FAILURE
PROCESS_SUPERVISION_FAILURE
NETWORK_CONNECTIVITY_FAILURE
DNS_FAILURE
RATE_LIMIT_FAILURE
PUBLIC_MD_PROTOCOL_FAILURE
MARKET_EVENT_NORMALIZATION_FAILURE
OHLCV_AGGREGATION_FAILURE
READ_MODEL_PROJECTION_FAILURE
DASHBOARD_BACKEND_FAILURE
DASHBOARD_FRONTEND_FAILURE
STREAM_TRANSPORT_FAILURE
STALE_DATA_FAILURE
PERSISTENCE_FAILURE
EVIDENCE_FAILURE
RECOVERY_FAILURE
WRITER_CONFLICT
```

Every failure must answer:

```text
ROOT_CAUSE_CLASS
AFFECTED_COMPONENT
SESSION_ID
FIRST_FAILURE_TIME
LAST_GOOD_TIME
DATA_LOSS_POSSIBLE
STATE_DIVERGENCE_POSSIBLE
AUTOMATIC_RECOVERY_ALLOWED
OWNER_ACTION_REQUIRED
```

---

# 16. Failure-Injection Program

Before closure, test at least:

1. Cursor shell exits immediately after launch.
2. Parent terminal closes.
3. `setsid` unavailable.
4. Hidden-input channel unavailable.
5. stdin replaced by pipe.
6. heredoc collides with secure input or consumes it.
7. uppercase proxy variables present.
8. lowercase proxy variables present.
9. `NO_PROXY` policy mismatch.
10. DNS failure.
11. public endpoint timeout.
12. HTTP 429 and bounded backoff.
13. process crash during active market-data stream.
14. dashboard backend crash.
15. dashboard browser poll disconnect or repeated HTTP failure.
16. read-model projector or materializer restart.
17. duplicate market event.
18. out-of-order market event.
19. missed OHLCV interval.
20. duplicate bar finalization.
21. stale dashboard connection showing cached data.
22. host sleep and wake.
23. local clock jump.
24. stale PID file.
25. duplicate session start.
26. writer conflict.
27. log path unavailable.
28. evidence path unavailable.
29. graceful shutdown timeout.
30. restart with persisted active state.

---

# 17. Capability Sequence

The implementation should be dependency-bound.

## Phase O0 — Forensic Operating-System and Runtime Topology Audit — COMPLETE

**Capability ID:**

```text
CAPABILITY_O0_FORENSIC_RUNTIME_DASHBOARD_AND_PROCESS_TOPOLOGY_AUDIT_V1
```

Required outputs:

```text
ALL_CURRENT_LAUNCH_PATHS_ENUMERATED=true
ALL_PROCESS_OWNERS_ENUMERATED=true
ALL_PROXY_CONSUMERS_ENUMERATED=true
ALL_PTY_DEPENDENCIES_ENUMERATED=true
ALL_DASHBOARD_COMPONENTS_ENUMERATED=true
ALL_OHLCV_PRODUCERS_ENUMERATED=true
ALL_READ_MODEL_PATHS_ENUMERATED=true
ALL_NETWORK_CLIENTS_ENUMERATED=true
ALL_HEALTH_ENDPOINTS_ENUMERATED=true
ALL_STATE_AND_LOG_ROOTS_ENUMERATED=true
```

Completion baseline:

```text
STATUS=FORENSIC_COMPLETE
VERDICT=TOPOLOGY_RECONCILED_WITH_GAPS
HEAD=b0e882b9714a615f633fb09b8ee4f9a19f54d470
NO_REPOSITORY_MUTATION=true
```

## Phase O1 — Canonical Environment and Platform Contract

**Capability ID:**

```text
CAPABILITY_O1_CANONICAL_ENVIRONMENT_AND_MACOS_PLATFORM_CONTRACT_V1
```

Close:

```text
environment allowlist
proxy semantics
macOS portability
repository and config binding
startup preflight
```

## Phase O2 — Canonical Launcher and Supervisor

**Capability ID:**

```text
CAPABILITY_O2_CANONICAL_LOCAL_LAUNCHER_AND_PROCESS_SUPERVISION_V1
```

Close:

```text
single launcher
process groups
session registry
PID safety
status/stop/restart
caller-independent lifetime
```

## Phase O3 — Secure Confirm-Token and Hidden-Input Handoff

**Capability ID:**

```text
CAPABILITY_O3_SECURE_CONFIRM_TOKEN_FAMILY_AND_HIDDEN_INPUT_HANDOFF_V1
```

Close:

```text
token-family matrix
hidden token channel
no stdin collision
non-interactive secure flow
no plaintext exposure
mode-0600 file exception lifecycle where unavoidable
```

## Phase O4 — Market-Data and OHLCV Transport Reconciliation

**Capability ID:**

```text
CAPABILITY_O4_CANONICAL_PUBLIC_MD_AND_OHLCV_TRANSPORT_RECONCILIATION_V1
```

Close:

```text
one canonical normalized event path
one bar producer
interval semantics
finalization and correction semantics
deduplication and ordering
```

## Phase O5 — Read Model and Dashboard Rebuild

**Capability ID:**

```text
CAPABILITY_O5_CANONICAL_READ_MODEL_AND_MARKET_DASHBOARD_REBUILD_V1
```

Close:

```text
read-only projection
dashboard backend/frontend lifecycle
real-time metrics
stale/disconnected states
instrument and interval isolation
```

## Phase O6 — Health, Recovery and Failure Injection

**Capability ID:**

```text
CAPABILITY_O6_RUNTIME_HEALTH_RECOVERY_AND_FAILURE_INJECTION_CLOSURE_V1
```

Close:

```text
component health
composite health
restart and recovery
failure taxonomy
bounded retry
host sleep/wake
```

## Phase O7 — Governed End-to-End Operational Evidence

**Capability ID:**

```text
CAPABILITY_O7_GOVERNED_END_TO_END_RUNTIME_AND_DASHBOARD_EVIDENCE_V1
```

Evidence ladder:

```text
launcher smoke
long-running public-MD session
dashboard HTTP-poll continuity
OHLCV matrix continuity
process crash/recovery
dashboard restart without runtime restart
runtime restart with read-model recovery
multi-session continuity
```

## Phase O8 — Canonical Operations Activation

**Capability ID:**

```text
CAPABILITY_O8_CANONICAL_RUNTIME_OPERATIONS_ACTIVATION_V1
```

Only this phase may deauthorize the old launch paths and mark the new operating path canonical.

---

# 18. Mandatory Evidence Metrics

```text
startup_attempt_count
startup_success_count
startup_failure_count
startup_latency_ms
process_restart_count
unexpected_process_exit_count
orphan_process_count
proxy_policy_failure_count
pty_failure_count
authorization_handoff_failure_count
network_connect_attempt_count
network_connect_success_count
dns_failure_count
rate_limit_event_count
market_event_count
duplicate_event_count
out_of_order_event_count
stale_event_count
ohlcv_in_progress_update_count
ohlcv_finalized_count
ohlcv_correction_count
ohlcv_gap_count
read_model_commit_count
read_model_replay_count
dashboard_connection_count
dashboard_reconnect_count
dashboard_stale_transition_count
end_to_end_latency_p50_ms
end_to_end_latency_p95_ms
end_to_end_latency_p99_ms
session_elapsed_seconds
graceful_shutdown_success
recovery_success
repository_unchanged
config_unchanged
orders_submitted
credentials_used
```

---

# 19. Closure Criteria

This program is closed only when:

```text
ONE_CANONICAL_LOCAL_LAUNCH_PATH=true
MACOS_PORTABILITY_PROVEN=true
CURSOR_SHELL_LIFETIME_INDEPENDENCE_PROVEN=true
ENVIRONMENT_ALLOWLIST_ACTIVE=true
PROXY_POLICY_UNAMBIGUOUS=true
HIDDEN_INPUT_HANDOFF_PROVEN=true
CONFIRM_TOKEN_HANDOFF_PROVEN=true
PROCESS_SUPERVISION_PROVEN=true
DUPLICATE_SESSION_BLOCKED=true
GRACEFUL_SHUTDOWN_PROVEN=true
CRASH_RECOVERY_PROVEN=true
PUBLIC_MD_TRANSPORT_PROVEN=true
OHLCV_PRODUCER_AUTHORITY_UNAMBIGUOUS=true
OHLCV_POLL_UPDATE_CONTINUITY_PROVEN=true
OHLCV_FINALIZATION_PROVEN=true
READ_MODEL_AUTHORITY_UNAMBIGUOUS=true
DASHBOARD_READ_ONLY=true
DASHBOARD_STALE_STATE_VISIBLE=true
DASHBOARD_DISCONNECT_STATE_VISIBLE=true
END_TO_END_LATENCY_MEASURED=true
LONG_RUNNING_CONTINUITY_PROVEN=true
FAILURE_INJECTION_PASS=true
OLD_AD_HOC_LAUNCH_PATHS_DEAUTHORIZED=true
CORE_LOGIC_CHANGE=false
LIVE_TESTNET_ORDER_BOUNDARY_PRESERVED=true
```

---

# 20. Immediate Execution Order

This runbook must not interrupt any currently running governed session. O0 has completed read-only and did not mutate the repository or interfere with processes.

Execution order:

```text
1. Allow the current governed session to finish without interference.
2. Finalize, verify and preserve its evidence separately from prior aborted attempts.
3. Bind evidence to repository SHA and config digest.
4. Update repository truth documents and the Notion mirror only under explicit authorization.
5. Ratify this V2.4 document into the repository as the named Canonical Runtime Operations Runbook.
6. Execute O1: canonical environment, proxy and macOS platform contract.
7. Execute O2: canonical dashboard/runtime launcher and process-supervision lifecycle.
8. Execute O3: confirm-token family matrix and secure hidden-input handoff.
9. Execute O4: reconcile productive public-MD and dashboard OHLCV producer ownership.
10. Execute O5: close durable read-model bindings, expected MISSING_SOURCE semantics and dashboard lifecycle.
11. Execute O6 failure injection and recovery.
12. Execute O7 governed end-to-end evidence.
13. Only O8 may deauthorize legacy launch paths.
```

Hard constraints:

```text
NO_PROXY_ONLY_PATCH_BEFORE_O1=true
NO_DASHBOARD_REBUILD_BEFORE_OWNER_AND_PRODUCER_RECONCILIATION=true
NO_LEGACY_STACK_DELETION_BEFORE_DEPENDENCY_PROOF=true
NO_RUNNING_SESSION_INTERFERENCE=true
```

# 21. Mandatory Cursor Assignment Header

Every implementation command under this runbook must include:

```text
OWNER_GO=true
CAPABILITY_ID=<id>
EXPECTED_ORIGIN_MAIN_SHA=<sha>
CORE_LOGIC_CHANGE_ALLOWED=false
LIVE_TRADING_ALLOWED=false
TESTNET_ALLOWED=false
PAPER_EXCHANGE_ORDERS_ALLOWED=false
EXCHANGE_CREDENTIAL_USE_ALLOWED=false
REAL_CAPITAL_MOVEMENT_ALLOWED=false
NETWORK_SESSION_ALLOWED=<true|false>
AUTHORIZATION_CONSUMPTION_ALLOWED=<true|false>
RULESET_MUTATION_ALLOWED=false
NOTION_MUTATION_ALLOWED=<true|false>
```

Mandatory output:

```text
STATUS
VERDICT
TASK
CAPABILITY_ID
EXPECTED_ORIGIN_MAIN_SHA
ACTUAL_HEAD_SHA
ACTUAL_ORIGIN_MAIN_SHA
HEAD_EQUALS_ORIGIN_MAIN
CURRENT_LAUNCH_PATHS
CURRENT_PROCESS_OWNERS
CURRENT_ENVIRONMENT_POLICY
CURRENT_PROXY_POLICY
CURRENT_HIDDEN_INPUT_MODEL
CURRENT_CONFIRM_TOKEN_FAMILY
CURRENT_DASHBOARD_TOPOLOGY
CURRENT_OHLCV_TOPOLOGY
FILES_CHANGED
CORE_LOGIC_CHANGED
CONFIG_CHANGED
NETWORK_SESSION_STARTED
AUTHORIZATION_CONSUMED
ORDERS_SUBMITTED
CREDENTIALS_USED
TESTS_RUN
FAILURE_INJECTION_RESULTS
RUNNING_SESSION_INTERFERED
EVIDENCE_CREATED
EVIDENCE_VERIFIED
NOTION_UPDATED
HARD_STOP
HARD_STOP_REASON
NEXT_SAFE_STEP
```

---

# 21A. Canonical Gap Register

## 21A.1 Security gaps requiring closure

```text
GAP_CONFIRM_TOKEN_FAMILY_FRAGMENTATION=OPEN
GAP_TOKEN_FILE_RESIDUAL_PLAINTEXT_RISK=OPEN
GAP_WEBUI_SHARED_PROCESS_WRITE_SURFACE_BLAST_RADIUS=OPEN
GAP_NON_LOCALHOST_BIND_EXPOSURE=OPEN
GAP_LEGACY_SSE_LOG_EXPOSURE=OPEN
GAP_NETWORK_GUARD_COVERAGE_PROOF=OPEN
GAP_DEFAULT_LOOPBACK_BIND_POLICY=OPEN
GAP_CORS_DEFAULT_DENY_POLICY=OPEN
GAP_TRUSTED_PROXY_HEADER_POLICY=OPEN
```

Required decisions:

- Separate or strictly gate write-capable Knowledge POST surfaces from the read-only Market Landscape host.
- Default-bind all dashboard hosts to loopback; non-loopback binding requires an explicit security mode and authentication contract.
- Default host binding: `127.0.0.1` (and `::1` where supported).
- Non-loopback binding must fail closed unless an explicit security mode is enabled.
- `CORS_DEFAULT_DENY=true` unless explicitly overridden.
- `TRUSTED_PROXY_HEADERS_DISABLED_UNLESS_EXPLICITLY_CONFIGURED=true`.
- Legacy SSE log exposure remains disabled by default unless explicitly authorized.
- Prove every public-MD HTTP client passes the canonical network-boundary guard.
- Inventory and classify all token files and verify exclusion from tracked and evidence paths.

## 21A.2 Operational gaps requiring closure

```text
GAP_SINGLE_OPERATOR_PROCESS_MAP=OPEN
GAP_DEDICATED_MARKET_DASHBOARD_SUPERVISOR=OPEN
GAP_ARCHIVE_ROOT_AMBIGUITY=OPEN
GAP_INJECTION_ONLY_EMPTY_SLOTS=OPEN
GAP_PARALLEL_DASHBOARD_OPERATOR_CONFUSION=OPEN
GAP_UNIFIED_LOG_ROOT=OPEN
GAP_END_TO_END_RECOVERY_COMMAND=OPEN
GAP_HISTORICAL_SHA_SEAL_CLASSIFICATION=OPEN
```

## 21A.3 Canonical classifications

```text
GET_/market=CANONICAL_CURRENT_MARKET_DASHBOARD
scripts/run_web_dashboard.py=CANONICAL_CURRENT_MARKET_DASHBOARD_HOST_PENDING_SUPERVISION
src/live/web=NON_CANONICAL_PARALLEL_OBSERVER_STACK
CLI_HEALTH_AND_OPERATOR_DASHBOARDS=NON_CANONICAL_OBSERVERS
HTTP_JSON_POLL=RATIFIED_CURRENT_LANDSCAPE_TRANSPORT
MARKET_DASHBOARD_WEBSOCKET=NOT_PRESENT_NOT_REQUIRED
MARKET_DASHBOARD_SSE=NOT_PRESENT_NOT_REQUIRED
LEGACY_LIVE_WEB_SSE=NON_CANONICAL_LOG_STREAM
PRODUCT_PTY_CONTROL_PLANE=NOT_PRESENT_NOT_REQUIRED_BY_CURRENT_CONTRACT
HIDDEN_CONFIRM_TOKEN_INPUT=REQUIRED
DASHBOARD_TRADING_AUTHORITY=false
```

# 22. Closing Principle

Peak_Trade cannot be considered operationally trustworthy when the trading core is correct but the host process, environment, market-data transport or dashboard path is nondeterministic.

The required end state is:

```text
Started deterministically
→ Environment verified
→ Process supervised
→ Market data connected
→ Events normalized
→ OHLCV projected
→ Runtime state persisted
→ Read model updated
→ Dashboard rendered
→ Health measured
→ Failures classified
→ Recovery bounded
→ Evidence verified
```

The central rule is:

```text
A successful manual start is not an operating model.
A running process is not supervised.
A visible dashboard is not fresh data.
A live-looking chart is not a verified transport path.
A proxy workaround is not an environment contract.
A PTY workaround is not a secure launch architecture.
```



---

# CANONICAL RECONCILIATION AND FORENSIC TRUTH ADDENDUM (V2.4)

This addendum imports mandatory operational governance from the Canonical Master Runbook without modifying trading authority.

## Master-Runbook Derived Invariants

```text
RUNBOOK_BOOTSTRAP_REQUIRED=true
RUNBOOK_READ_COMPLETE=true
RUNBOOK_USED_AS_SINGLE_IMPLEMENTATION_AUTHORITY=true
NO_PARALLEL_SEMANTIC_MODEL=true

REAL_LOCAL_TERMINAL_REQUIRED=true
REAL_LOCAL_REPOSITORY_REQUIRED=true
REAL_DOT_GIT_REQUIRED=true
SANDBOX_GIT_EXECUTION_ALLOWED=false
SANDBOX_FALLBACK_ALLOWED=false
CURSOR_SANDBOX_ALLOWED=false
LOCAL_USER_SANDBOX_ALLOWED=false
ANY_VIRTUALIZED_GIT_SANDBOX_ALLOWED=false
ONLY_REAL_LOCAL_TERMINAL_AND_REAL_REPOSITORY_ALLOWED=true

CORE_LOGIC_CHANGE=false
MASTER_V2_AUTHORITY_UNCHANGED=true
DOUBLE_PLAY_AUTHORITY_UNCHANGED=true
RISK_AUTHORITY_UNCHANGED=true
SAFETY_AUTHORITY_UNCHANGED=true

DASHBOARD_TRADING_AUTHORITY=false
READ_MODEL_DERIVED_PROJECTION_ONLY=true
READ_MODEL_SSOT=false
READ_MODEL_AUTHORITY_EFFECT=NONE
READ_MODEL_TRADING_AUTHORITY=false

CONFIRM_TOKEN_CANONICAL_PATH_USED=true
CONFIRM_TOKEN_PLAINTEXT_EXPOSED=false
CONFIRM_TOKEN_PERSISTED=false_as_target
CONFIRM_TOKEN_FILE_EXCEPTION_EXPLICIT_AND_EPHEMERAL=true
CONFIRM_TOKEN_SHELL_HISTORY=false

OWNER_MERGE_GO_REQUIRED=true
MERGE_ONLY_AFTER_GREEN_AND_SHA_MATCH=true
RULESET_MUTATION_ONLY_WITH_EXPLICIT_OWNER_MERGE_GO=true

RUNNING_GOVERNED_SESSION_NOT_INTERRUPTED=true
UNTRACKED_EVIDENCE_PRESERVED=true
TRACKED_WORKTREE_VALIDATED=true
REPOSITORY_SHA_VALIDATED=true
```

## Mandatory Local Git Preflight

```bash
pwd
git rev-parse --show-toplevel
git rev-parse --git-dir
git status --short
git branch --show-current
git rev-parse HEAD
git fetch origin --prune
git rev-parse origin/main
git diff --stat origin/main...HEAD
```



## Master Authority and SSOT Exclusivity

This runbook derives its authority exclusively from the Peak_Trade Master Runbook.

Under no circumstances may this document be interpreted as, promoted to, or treated as a second Single Source of Truth (SSOT).

```text
MASTER_RUNBOOK_IS_THE_ONLY_SSOT=true

SECOND_SSOT_ALLOWED=false
SECOND_SSOT_PERMITTED=false
SECOND_SSOT_CREATION_FORBIDDEN=true

THIS_DOCUMENT_IS_SSOT=false
THIS_DOCUMENT_MAY_NOT_BECOME_SSOT=true
THIS_DOCUMENT_MUST_NOT_DECLARE_SSOT=true
THIS_DOCUMENT_MUST_NOT_IMPLY_SSOT=true

MASTER_RUNBOOK_SUPREMACY=true
MASTER_RUNBOOK_PRECEDENCE=ABSOLUTE

DOMAIN_AUTHORITY_ONLY=true
AUTHORITY_DERIVED_FROM_MASTER_RUNBOOK=true

CONFLICT_WITH_MASTER_RUNBOOK_ALLOWED=false
CONFLICT_RESOLUTION=MASTER_RUNBOOK_ALWAYS_WINS

NO_RUNTIME_DOCUMENT_MAY_OVERRIDE_MASTER=true
NO_DOMAIN_DOCUMENT_MAY_OVERRIDE_MASTER=true
NO_FUTURE_DOCUMENT_MAY_ESTABLISH_PARALLEL_SSOT=true
```

Normative rule:

> The Peak_Trade Master Runbook is the one and only Single Source of Truth (SSOT) for the entire system. No other document, runbook, specification, capability, architecture document, or future artifact may declare, imply, or function as a second SSOT. This Runtime Operations Runbook is a domain-specific operational reference only. Its authority is strictly derived from, subordinate to, and bounded by the Master Runbook. In every real or perceived conflict, ambiguity, overlap, or inconsistency, the Master Runbook shall prevail without exception.


## Operational Clarifications

- Dashboard, Read Model, OHLCV transport and process supervision remain operational infrastructure only.
- No dashboard component may become a trading authority.
- Every new Cursor session must bootstrap from the canonical Master Runbook before repository mutation.
- Every Cursor task must either return the next executable command or a justified HARD_STOP.
