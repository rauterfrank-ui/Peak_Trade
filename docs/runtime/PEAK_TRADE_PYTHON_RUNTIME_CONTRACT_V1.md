# Peak_Trade Python Runtime Contract v1

```text
AUTHORITY_CLASS=OPERATIVE_RUNTIME_CONTRACT
RUNTIME_AUTHORIZATION_EFFECT=NONE
CONTRACT_ID=pt_python_runtime_contract_v1
CANONICAL_LAUNCHER=scripts/pt
CANONICAL_INTERPRETER=.venv/bin/python
REQUIRES_PYTHON=>=3.10
PATH_PYTHON_FALLBACK_ALLOWED=false
VENV_ACTIVATION_REQUIRED=false
```

This is the current supported Python execution model for Peak_Trade.

It does **not** authorize Live, Testnet, orders, credentials, or capital movement.

## Identity

Same repository revision + same config + same declared runtime must select the
same interpreter and import model. Selection must not depend on PATH, pyenv,
shell activation, IDE interpreter, caller cwd, or `PYTHONPATH`.

Machine-readable SSOT for the version floor is `pyproject.toml`
`requires-python = ">=3.10"`. Recommended local interpreter is the repository
`.venv` (currently provisioned as CPython 3.11.x). Python 3.9 is **not** a
supported project runtime.

## Bootstrap versus runtime

Bootstrap (operator-invoked):

```text
./scripts/pt-bootstrap
```

That surface runs `uv sync --dev` in the current checkout when `.venv` is missing, writes a lock-bound fingerprint under `.venv/`, and refuses a `.venv` symlink to another worktree. See [`PEAK_TRADE_WORKTREE_PYTHON_ENVIRONMENT_BOOTSTRAP_CONTRACT_V1.md`](PEAK_TRADE_WORKTREE_PYTHON_ENVIRONMENT_BOOTSTRAP_CONTRACT_V1.md).

Runtime must only validate and use the provisioned environment. Runtime must
not create a venv, install packages, or source `.venv&#47;bin&#47;activate`.

Git worktrees are separate checkouts. Shared mutable `.venv` reuse via symlink
is unsupported.

## Canonical commands

```text
./scripts/pt-bootstrap
./scripts/pt runtime-check
./scripts/pt fingerprint
./scripts/pt -m pytest -q
./scripts/pt -c "import trading"
make bootstrap
make runtime-check
```

Root trampoline `pt` execs `scripts/pt`.

## Prohibited on current operative local surfaces

- bare `python`
- bare `python3`
- `#!&#47;usr&#47;bin&#47;env python3` as a supported way to start Peak_Trade
- `source .venv&#47;bin&#47;activate` as the correctness mechanism
- arbitrary `PYTHONPATH` / `sys.path` mutation as the runtime solution
- direct `src/` execution for package code

## Documented exceptions

- **CI provisioned interpreter:** GitHub Actions may bind a pinned interpreter
  after `setup-python`. Set `PT_RUNTIME_MODE=provisioned` only in CI or with
  `PT_RUNTIME_PROVISIONED_OK=1`. The launcher then uses `pythonLocation&#47;bin&#47;python`
  or `PT_PROVISIONED_PYTHON`. Local PATH `python`/`python3` remains prohibited.
- **Pytest `tests/conftest.py`:** inserts `src` and repo root for test
  collection only.
- **Shebangs on non-operative scripts:** not a runtime API. Invoke through
  `scripts/pt`.
- **A small set of existing offline-eval wrappers** resolve
  `.venv&#47;bin&#47;python` directly and fail closed if it is missing. New surfaces
  must use `scripts/pt`.

## Agents

Never infer the interpreter from the terminal. If `scripts/pt` `runtime-check`
fails: HARD STOP. Do not improvise `PYTHONPATH`, PATH `python3`, or package
installs.
