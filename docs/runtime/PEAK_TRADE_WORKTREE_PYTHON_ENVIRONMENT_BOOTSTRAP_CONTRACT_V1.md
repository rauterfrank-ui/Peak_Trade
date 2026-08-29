# Peak_Trade Worktree Python Environment Bootstrap Contract v1

status: ACTIVE
last_updated: 2026-08-29
owner: Peak_Trade
purpose: Bind each Git checkout or worktree to its own physical Python environment. Not a second SSOT. Not live or execution authority. Not a replacement of scripts/pt.
docs_token: DOCS_TOKEN_PEAK_TRADE_WORKTREE_PYTHON_ENVIRONMENT_BOOTSTRAP_CONTRACT_V1

```text
DOCUMENT_CLASS=SUBORDINATE_RUNTIME_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1
CANONICAL_RUNTIME_OWNER=docs/runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md
BOOTSTRAP_SURFACE=scripts/pt-bootstrap
RUNTIME_LAUNCHER=scripts/pt
WORKTREE_ENVIRONMENT_OWNER=BOUND
WORKTREE_ENVIRONMENT_MODEL=PER_WORKTREE_VENV
EACH_CHECKOUT_OR_WORKTREE_OWNS_ITS_OWN_PYTHON_ENVIRONMENT=true
SHARED_VENV_SYMLINK_ALLOWED=false
RUNTIME_CREATES_VENV=false
RUNTIME_INSTALLS_DEPENDENCIES=false
VIRTUAL_ENV_IS_NOT_CORRECTNESS_AUTHORITY=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
TESTNET_AUTHORIZED=false
CANARY_AUTHORIZED=false
```

## Model

```text
LOCAL_WORKTREE_MODEL=uv_sync_dev + per-worktree .venv + lock-bound fingerprint
CI_MODEL=isolated_checkout + setup-python + pip_install_requirements
SHARED_INVARIANT=code_and_dependency_environment_belong_to_current_checkout
```

Every Git worktree is its own `REPO_ROOT` (`pyproject.toml` + `scripts/pt` + `uv.lock`).

Provision:

```text
git worktree add <path> <branch>
cd <path>
./scripts/pt-bootstrap
./scripts/pt runtime-check
```

`./scripts/pt-bootstrap` runs `uv sync --dev` in that checkout when `.venv` is missing. It refuses a `.venv` symlink and does not unlink it.

## Fingerprint

After successful provision, bootstrap writes:

```text
.venv/.peak_trade_env_fingerprint.json
```

Schema `peak_trade_env_fingerprint_v1` binds:

- Python version string of the checkout interpreter
- sha256 of `uv.lock` raw bytes
- sha256 of `pyproject.toml` raw bytes
- bootstrap and runtime contract ids

The file is local/derived and must not be committed (it lives under ignored `.venv/`).

`scripts/pt` validates the fingerprint before execution in repo-venv mode. It does not auto-sync.

## Fail closed

- missing checkout `.venv` → `./scripts/pt-bootstrap`
- `.venv` is a symlink to another worktree → unsupported, no unlink
- fingerprint missing, malformed, or lock/pyproject/python mismatch → `./scripts/pt-bootstrap`
- editable install bound to another checkout → unsupported

Pytest `conftest.py` path injection is not an environment health proof.
