"""Peak_Trade deterministic Python runtime contract v1.

Stdlib-only. Non-authorizing. Does not create a venv, install packages,
call exchanges, or mutate global machine configuration.

Local/unattended mode requires REPO_ROOT/.venv/bin/python and rejects PATH
fallback. Provisioned mode is a documented CI exception after setup-python.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Mapping

CONTRACT_ID: Final = "pt_python_runtime_contract_v1"
CONTRACT_VERSION: Final = "v1"
CANONICAL_LAUNCHER_REL: Final = Path("scripts/pt")
CANONICAL_INTERPRETER_REL: Final = Path(".venv/bin/python")
REQUIRES_PYTHON: Final = ">=3.10"
REQUIRES_PYTHON_MAJOR: Final = 3
REQUIRES_PYTHON_MINOR: Final = 10
MODE_REPO_VENV: Final = "repo_venv"
MODE_PROVISIONED: Final = "provisioned"
PROVISIONED_ENV: Final = "PT_RUNTIME_MODE"
GITHUB_ACTIONS_ENV: Final = "GITHUB_ACTIONS"

REASON_PASS: Final = "RUNTIME_CONTRACT_PASS"
REASON_REPO_ROOT_UNRESOLVED: Final = "REPO_ROOT_UNRESOLVED"
REASON_VENV_MISSING: Final = "REPO_VENV_PYTHON_MISSING"
REASON_VENV_NOT_EXECUTABLE: Final = "REPO_VENV_PYTHON_NOT_EXECUTABLE"
REASON_UNSUPPORTED_PYTHON: Final = "UNSUPPORTED_PYTHON_VERSION"
REASON_INTERPRETER_MISMATCH: Final = "INTERPRETER_IDENTITY_MISMATCH"
REASON_TRADING_IMPORT_FAILED: Final = "TRADING_IMPORT_FAILED"
REASON_PROVISIONED_REFUSED: Final = "PROVISIONED_MODE_REFUSED"
REASON_PYPROJECT_DRIFT: Final = "PYPROJECT_REQUIRES_PYTHON_DRIFT"

EXIT_PASS: Final = 0
EXIT_UNSUPPORTED_PYTHON: Final = 2
EXIT_VENV_MISSING: Final = 3
EXIT_VENV_NOT_EXECUTABLE: Final = 4
EXIT_INTERPRETER_MISMATCH: Final = 5
EXIT_TRADING_IMPORT_FAILED: Final = 6
EXIT_REPO_ROOT_UNRESOLVED: Final = 7
EXIT_PROVISIONED_REFUSED: Final = 8
EXIT_PYPROJECT_DRIFT: Final = 9

_REASON_EXIT: Final = {
    REASON_PASS: EXIT_PASS,
    REASON_UNSUPPORTED_PYTHON: EXIT_UNSUPPORTED_PYTHON,
    REASON_VENV_MISSING: EXIT_VENV_MISSING,
    REASON_VENV_NOT_EXECUTABLE: EXIT_VENV_NOT_EXECUTABLE,
    REASON_INTERPRETER_MISMATCH: EXIT_INTERPRETER_MISMATCH,
    REASON_TRADING_IMPORT_FAILED: EXIT_TRADING_IMPORT_FAILED,
    REASON_REPO_ROOT_UNRESOLVED: EXIT_REPO_ROOT_UNRESOLVED,
    REASON_PROVISIONED_REFUSED: EXIT_PROVISIONED_REFUSED,
    REASON_PYPROJECT_DRIFT: EXIT_PYPROJECT_DRIFT,
}


@dataclass(frozen=True)
class RuntimeValidation:
    ok: bool
    reason_code: str
    exit_code: int
    mode: str
    repo_root: str
    interpreter: str
    interpreter_version: str
    contract_version: str
    requires_python: str
    trading_origin: str
    diagnostic: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def repo_root_from_this_file(start: Path | None = None) -> Path | None:
    cursor = (start or Path(__file__)).resolve()
    if cursor.is_file():
        cursor = cursor.parent
    for candidate in (cursor, *cursor.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / CANONICAL_LAUNCHER_REL
        ).is_file():
            return candidate
    return None


def load_contract_config(repo_root: Path) -> dict[str, Any]:
    path = repo_root / "config" / "runtime" / "pt_python_runtime_contract_v1.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def pyproject_requires_python(repo_root: Path) -> str | None:
    path = repo_root / "pyproject.toml"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("requires-python"):
            _, _, raw = stripped.partition("=")
            return raw.strip().strip('"').strip("'")
    return None


def resolve_mode(env: Mapping[str, str] | None = None) -> str:
    mapping = os.environ if env is None else env
    if mapping.get(PROVISIONED_ENV, "").strip() == MODE_PROVISIONED:
        return MODE_PROVISIONED
    return MODE_REPO_VENV


def provisioned_mode_allowed(env: Mapping[str, str] | None = None) -> bool:
    mapping = os.environ if env is None else env
    if mapping.get(PROVISIONED_ENV, "").strip() != MODE_PROVISIONED:
        return False
    if mapping.get(GITHUB_ACTIONS_ENV, "").strip().lower() == "true":
        return True
    return mapping.get("PT_RUNTIME_PROVISIONED_OK", "").strip() == "1"


def canonical_interpreter_path(repo_root: Path) -> Path:
    return repo_root / CANONICAL_INTERPRETER_REL


def _venv_root_from_executable(executable: Path) -> Path | None:
    path = Path(executable)
    if path.parent.name in {"bin", "Scripts"}:
        return path.parent.parent
    return None


def is_canonical_running_interpreter(repo_root: Path, running: Path) -> bool:
    """True when this process was launched via REPO_ROOT/.venv/bin/python.

    Compares venv homes, not the fully resolved uv/CPython binary. Multiple
    repository checkouts may share the same CPython build.
    """
    expected = (repo_root / ".venv").resolve()
    invoked_root = _venv_root_from_executable(running)
    if invoked_root is None:
        return False
    return invoked_root.resolve() == expected


def interpreter_version_tuple(executable: Path) -> tuple[int, int, str] | None:
    running_root = _venv_root_from_executable(Path(sys.executable))
    selected_root = _venv_root_from_executable(executable)
    if running_root is None or selected_root is None:
        return None
    if running_root.resolve() != selected_root.resolve():
        return None
    info = sys.version_info
    return int(info.major), int(info.minor), sys.version.split()[0]


def version_satisfies_floor(major: int, minor: int) -> bool:
    return (major, minor) >= (REQUIRES_PYTHON_MAJOR, REQUIRES_PYTHON_MINOR)


def _fail(
    *,
    reason: str,
    mode: str,
    repo_root: Path | None,
    interpreter: Path | None,
    diagnostic: str,
    interpreter_version: str = "",
    trading_origin: str = "",
) -> RuntimeValidation:
    return RuntimeValidation(
        ok=False,
        reason_code=reason,
        exit_code=_REASON_EXIT[reason],
        mode=mode,
        repo_root="" if repo_root is None else str(repo_root),
        interpreter="" if interpreter is None else str(interpreter),
        interpreter_version=interpreter_version,
        contract_version=CONTRACT_VERSION,
        requires_python=REQUIRES_PYTHON,
        trading_origin=trading_origin,
        diagnostic=diagnostic,
    )


def _trading_origin() -> str:
    import importlib.util

    spec = importlib.util.find_spec("trading")
    if spec is None:
        return ""
    if spec.submodule_search_locations:
        return str(list(spec.submodule_search_locations)[0])
    return str(spec.origin or "")


def validate_runtime(
    *,
    repo_root: Path | None = None,
    env: Mapping[str, str] | None = None,
    require_trading_import: bool = True,
    running_executable: Path | None = None,
    check_running_identity: bool = False,
) -> RuntimeValidation:
    mode = resolve_mode(env)
    root = repo_root or repo_root_from_this_file()
    if root is None:
        return _fail(
            reason=REASON_REPO_ROOT_UNRESOLVED,
            mode=mode,
            repo_root=None,
            interpreter=None,
            diagnostic="Cannot resolve repository root (pyproject.toml + scripts/pt required).",
        )

    declared = pyproject_requires_python(root)
    if declared is not None and declared != REQUIRES_PYTHON:
        return _fail(
            reason=REASON_PYPROJECT_DRIFT,
            mode=mode,
            repo_root=root,
            interpreter=None,
            diagnostic=(
                f"Contract floor {REQUIRES_PYTHON} drifts from pyproject.toml "
                f"requires-python={declared}."
            ),
        )

    current = running_executable or Path(sys.executable)

    if mode == MODE_PROVISIONED:
        if not provisioned_mode_allowed(env):
            return _fail(
                reason=REASON_PROVISIONED_REFUSED,
                mode=mode,
                repo_root=root,
                interpreter=current,
                diagnostic=(
                    "Provisioned mode requires PT_RUNTIME_MODE=provisioned and "
                    "GITHUB_ACTIONS=true or PT_RUNTIME_PROVISIONED_OK=1."
                ),
            )
        selected = current
    else:
        selected = canonical_interpreter_path(root)
        if not selected.is_file():
            return _fail(
                reason=REASON_VENV_MISSING,
                mode=mode,
                repo_root=root,
                interpreter=selected,
                diagnostic=(
                    "Canonical interpreter missing. Bootstrap with: uv sync --dev "
                    f"(creates {CANONICAL_INTERPRETER_REL}). Do not use PATH python3."
                ),
            )
        if not os.access(selected, os.X_OK):
            return _fail(
                reason=REASON_VENV_NOT_EXECUTABLE,
                mode=mode,
                repo_root=root,
                interpreter=selected,
                diagnostic=f"Canonical interpreter is not executable: {selected}",
            )
        if check_running_identity and not is_canonical_running_interpreter(root, current):
            return _fail(
                reason=REASON_INTERPRETER_MISMATCH,
                mode=mode,
                repo_root=root,
                interpreter=current,
                diagnostic=(
                    "This process is not the canonical repository interpreter. "
                    f"Use {CANONICAL_LAUNCHER_REL} (never PATH python/python3)."
                ),
            )

    version = interpreter_version_tuple(selected)
    if version is None:
        # selected is canonical venv python but this process is a different
        # interpreter (launcher already checked version via selected -c).
        interpreter_version = ""
        major = REQUIRES_PYTHON_MAJOR
        minor = REQUIRES_PYTHON_MINOR
        version_ok = True
    else:
        major, minor, interpreter_version = version
        version_ok = version_satisfies_floor(major, minor)

    if not version_ok:
        return _fail(
            reason=REASON_UNSUPPORTED_PYTHON,
            mode=mode,
            repo_root=root,
            interpreter=selected,
            interpreter_version=interpreter_version,
            diagnostic=(
                f"Python {interpreter_version} is unsupported. "
                f"Need {REQUIRES_PYTHON}. System 3.9.x is not a Peak_Trade runtime."
            ),
        )

    trading_origin = ""
    if require_trading_import:
        try:
            trading_origin = _trading_origin()
            if not trading_origin:
                raise ModuleNotFoundError("No module named 'trading'")
        except Exception as exc:  # noqa: BLE001 — fail-closed diagnostic
            return _fail(
                reason=REASON_TRADING_IMPORT_FAILED,
                mode=mode,
                repo_root=root,
                interpreter=selected,
                interpreter_version=interpreter_version,
                diagnostic=(
                    "import trading failed under the selected interpreter. "
                    "Do not set PYTHONPATH. Bootstrap with uv sync --dev. "
                    f"error={exc}"
                ),
            )

    return RuntimeValidation(
        ok=True,
        reason_code=REASON_PASS,
        exit_code=EXIT_PASS,
        mode=mode,
        repo_root=str(root),
        interpreter=str(selected),
        interpreter_version=interpreter_version or sys.version.split()[0],
        contract_version=CONTRACT_VERSION,
        requires_python=REQUIRES_PYTHON,
        trading_origin=trading_origin,
        diagnostic="canonical repository runtime validated",
    )


def fingerprint_payload(result: RuntimeValidation) -> dict[str, Any]:
    payload = result.as_dict()
    payload["contract_id"] = CONTRACT_ID
    payload["path_python_fallback_allowed"] = False
    payload["venv_activation_required"] = False
    payload["pyenv_dependency"] = False
    payload["pythonpath_dependency"] = False
    payload["cwd_dependency"] = False
    payload["git_revision"] = _git_revision(Path(result.repo_root) if result.repo_root else None)
    payload["project_name"] = "peak_trade"
    return payload


def _git_revision(repo_root: Path | None) -> str:
    if repo_root is None:
        return ""
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    command = args[0] if args else "validate"
    require_trading = command in {"fingerprint", "runtime-check", "validate"}
    result = validate_runtime(
        require_trading_import=require_trading,
        check_running_identity=True,
    )
    if command in {"fingerprint", "runtime-check"}:
        print(json.dumps(fingerprint_payload(result), indent=2, sort_keys=True))
    else:
        print(f"REASON_CODE={result.reason_code}")
        print(f"EXIT_CODE={result.exit_code}")
        print(f"INTERPRETER={result.interpreter}")
        print(f"DIAGNOSTIC={result.diagnostic}")
    return int(result.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
