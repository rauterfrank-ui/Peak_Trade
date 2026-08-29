"""Per-checkout Python environment isolation for Peak_Trade worktrees.

Stdlib-only. Non-authorizing. Does not create a venv, install packages,
call exchanges, or follow a shared ``.venv`` symlink as a valid environment.

Local repo-venv mode requires a real ``REPO_ROOT/.venv`` directory owned by
this checkout, a lock-bound fingerprint, and editable source binding to
this checkout. Provisioned CI mode does not use this module.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping
from urllib.parse import unquote, urlparse

SCHEMA_ID: Final = "peak_trade_env_fingerprint_v1"
SCHEMA_VERSION: Final = 1
BOOTSTRAP_CONTRACT_ID: Final = "pt_worktree_environment_bootstrap_v1"
RUNTIME_CONTRACT_ID: Final = "pt_python_runtime_contract_v1"
FINGERPRINT_REL: Final = Path(".venv") / ".peak_trade_env_fingerprint.json"
BOOTSTRAP_SURFACE_REL: Final = Path("scripts/pt-bootstrap")

REASON_VENV_SYMLINK: Final = "REPO_VENV_SYMLINK_UNSUPPORTED"
REASON_VENV_NOT_DIRECTORY: Final = "REPO_VENV_NOT_DIRECTORY"
REASON_UV_LOCK_MISSING: Final = "REPO_UV_LOCK_MISSING"
REASON_ENV_FINGERPRINT_MISSING: Final = "REPO_ENV_FINGERPRINT_MISSING"
REASON_ENV_FINGERPRINT_MALFORMED: Final = "REPO_ENV_FINGERPRINT_MALFORMED"
REASON_ENV_FINGERPRINT_MISMATCH: Final = "REPO_ENV_FINGERPRINT_MISMATCH"
REASON_FOREIGN_SOURCE_BINDING: Final = "REPO_FOREIGN_SOURCE_BINDING"
REASON_SOURCE_BINDING_MISSING: Final = "REPO_SOURCE_BINDING_MISSING"
REASON_ISOLATION_PASS: Final = "WORKTREE_ENV_ISOLATION_PASS"

EXIT_VENV_SYMLINK: Final = 10
EXIT_ENV_FINGERPRINT: Final = 11
EXIT_FOREIGN_SOURCE: Final = 12
EXIT_UV_LOCK_MISSING: Final = 13

_REASON_EXIT: Final = {
    REASON_VENV_SYMLINK: EXIT_VENV_SYMLINK,
    REASON_VENV_NOT_DIRECTORY: EXIT_VENV_SYMLINK,
    REASON_UV_LOCK_MISSING: EXIT_UV_LOCK_MISSING,
    REASON_ENV_FINGERPRINT_MISSING: EXIT_ENV_FINGERPRINT,
    REASON_ENV_FINGERPRINT_MALFORMED: EXIT_ENV_FINGERPRINT,
    REASON_ENV_FINGERPRINT_MISMATCH: EXIT_ENV_FINGERPRINT,
    REASON_FOREIGN_SOURCE_BINDING: EXIT_FOREIGN_SOURCE,
    REASON_SOURCE_BINDING_MISSING: EXIT_FOREIGN_SOURCE,
    REASON_ISOLATION_PASS: 0,
}

_BOOTSTRAP_HINT: Final = (
    "foreign/shared/symlinked worktree environment is unsupported. "
    "Bootstrap with: ./scripts/pt-bootstrap"
)


@dataclass(frozen=True)
class IsolationResult:
    ok: bool
    reason_code: str
    exit_code: int
    diagnostic: str
    uv_lock_sha256: str = ""
    pyproject_sha256: str = ""
    source_binding: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "reason_code": self.reason_code,
            "exit_code": self.exit_code,
            "diagnostic": self.diagnostic,
            "uv_lock_sha256": self.uv_lock_sha256,
            "pyproject_sha256": self.pyproject_sha256,
            "source_binding": self.source_binding,
        }


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def lockfile_hashes(repo_root: Path) -> tuple[str, str]:
    pyproject = repo_root / "pyproject.toml"
    lock = repo_root / "uv.lock"
    return sha256_file(pyproject), sha256_file(lock)


def venv_dir(repo_root: Path) -> Path:
    return repo_root / ".venv"


def fingerprint_path(repo_root: Path) -> Path:
    return repo_root / FINGERPRINT_REL


def _fail(reason: str, diagnostic: str, **extra: str) -> IsolationResult:
    return IsolationResult(
        ok=False,
        reason_code=reason,
        exit_code=_REASON_EXIT[reason],
        diagnostic=diagnostic,
        uv_lock_sha256=extra.get("uv_lock_sha256", ""),
        pyproject_sha256=extra.get("pyproject_sha256", ""),
        source_binding=extra.get("source_binding", ""),
    )


def assert_venv_is_local_directory(repo_root: Path) -> IsolationResult | None:
    venv = venv_dir(repo_root)
    if venv.is_symlink():
        target = venv.readlink()
        return _fail(
            REASON_VENV_SYMLINK,
            (
                f"{_BOOTSTRAP_HINT} "
                f"REPO_ROOT={repo_root} .venv is a symlink to {target}. "
                "Do not reuse another worktree environment. "
                "./scripts/pt-bootstrap will not unlink automatically."
            ),
        )
    return None


def _required_lock_files(repo_root: Path) -> IsolationResult | None:
    if not (repo_root / "uv.lock").is_file():
        return _fail(
            REASON_UV_LOCK_MISSING,
            f"uv.lock missing at {repo_root}. {_BOOTSTRAP_HINT}",
        )
    if not (repo_root / "pyproject.toml").is_file():
        return _fail(
            REASON_UV_LOCK_MISSING,
            f"pyproject.toml missing at {repo_root}. {_BOOTSTRAP_HINT}",
        )
    return None


def fingerprint_payload(
    *,
    python_version: str,
    uv_lock_sha256: str,
    pyproject_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "bootstrap_contract_id": BOOTSTRAP_CONTRACT_ID,
        "runtime_contract_id": RUNTIME_CONTRACT_ID,
        "python_version": python_version,
        "uv_lock_sha256": uv_lock_sha256,
        "pyproject_sha256": pyproject_sha256,
    }


def write_env_fingerprint(repo_root: Path, *, python_version: str) -> Path:
    missing = _required_lock_files(repo_root)
    if missing is not None:
        raise RuntimeError(missing.diagnostic)
    symlink = assert_venv_is_local_directory(repo_root)
    if symlink is not None:
        raise RuntimeError(symlink.diagnostic)
    pyproject_sha, lock_sha = lockfile_hashes(repo_root)
    path = fingerprint_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = fingerprint_payload(
        python_version=python_version,
        uv_lock_sha256=lock_sha,
        pyproject_sha256=pyproject_sha,
    )
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _load_fingerprint(path: Path) -> tuple[dict[str, Any] | None, IsolationResult | None]:
    if not path.is_file():
        return None, _fail(
            REASON_ENV_FINGERPRINT_MISSING,
            (
                f"Environment fingerprint missing: {path}. "
                "Do not copy another worktree .venv. "
                f"{_BOOTSTRAP_HINT}"
            ),
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, _fail(
            REASON_ENV_FINGERPRINT_MALFORMED,
            f"Environment fingerprint malformed at {path}: {exc}. {_BOOTSTRAP_HINT}",
        )
    if not isinstance(payload, dict):
        return None, _fail(
            REASON_ENV_FINGERPRINT_MALFORMED,
            f"Environment fingerprint is not an object: {path}. {_BOOTSTRAP_HINT}",
        )
    return payload, None


def validate_fingerprint(
    repo_root: Path,
    *,
    python_version: str,
) -> IsolationResult:
    missing = _required_lock_files(repo_root)
    if missing is not None:
        return missing
    pyproject_sha, lock_sha = lockfile_hashes(repo_root)
    payload, load_fail = _load_fingerprint(fingerprint_path(repo_root))
    if load_fail is not None:
        return load_fail
    assert payload is not None
    required = (
        "schema_id",
        "schema_version",
        "bootstrap_contract_id",
        "runtime_contract_id",
        "python_version",
        "uv_lock_sha256",
        "pyproject_sha256",
    )
    for key in required:
        if key not in payload:
            return _fail(
                REASON_ENV_FINGERPRINT_MALFORMED,
                f"Environment fingerprint missing key {key}. {_BOOTSTRAP_HINT}",
                uv_lock_sha256=lock_sha,
                pyproject_sha256=pyproject_sha,
            )
    if payload.get("schema_id") != SCHEMA_ID or payload.get("schema_version") != SCHEMA_VERSION:
        return _fail(
            REASON_ENV_FINGERPRINT_MALFORMED,
            f"Environment fingerprint schema mismatch. {_BOOTSTRAP_HINT}",
            uv_lock_sha256=lock_sha,
            pyproject_sha256=pyproject_sha,
        )
    if payload.get("uv_lock_sha256") != lock_sha:
        return _fail(
            REASON_ENV_FINGERPRINT_MISMATCH,
            (f"uv.lock sha256 does not match the environment fingerprint. {_BOOTSTRAP_HINT}"),
            uv_lock_sha256=lock_sha,
            pyproject_sha256=pyproject_sha,
        )
    if payload.get("pyproject_sha256") != pyproject_sha:
        return _fail(
            REASON_ENV_FINGERPRINT_MISMATCH,
            (
                "pyproject.toml sha256 does not match the environment fingerprint. "
                f"{_BOOTSTRAP_HINT}"
            ),
            uv_lock_sha256=lock_sha,
            pyproject_sha256=pyproject_sha,
        )
    if str(payload.get("python_version") or "") != python_version:
        return _fail(
            REASON_ENV_FINGERPRINT_MISMATCH,
            (f"Python version does not match the environment fingerprint. {_BOOTSTRAP_HINT}"),
            uv_lock_sha256=lock_sha,
            pyproject_sha256=pyproject_sha,
        )
    return IsolationResult(
        ok=True,
        reason_code=REASON_ISOLATION_PASS,
        exit_code=0,
        diagnostic="environment fingerprint matches checkout lockfiles",
        uv_lock_sha256=lock_sha,
        pyproject_sha256=pyproject_sha,
    )


def _direct_url_repo_root(raw: Mapping[str, Any]) -> Path | None:
    url = raw.get("url")
    if not isinstance(url, str) or not url.startswith("file:"):
        return None
    parsed = urlparse(url)
    path = unquote(parsed.path or "")
    if not path:
        return None
    return Path(path)


def discover_source_binding(repo_root: Path) -> IsolationResult:
    lib = venv_dir(repo_root) / "lib"
    pth_files = sorted(lib.glob("python*/site-packages/__editable__.peak_trade-*.pth"))
    url_files = sorted(lib.glob("python*/site-packages/peak_trade-*.dist-info/direct_url.json"))
    expected_src = repo_root / "src"
    expected_root = repo_root
    if not pth_files or not url_files:
        return _fail(
            REASON_SOURCE_BINDING_MISSING,
            (
                "Editable peak_trade source binding metadata is missing under "
                f"{lib}. {_BOOTSTRAP_HINT}"
            ),
        )
    for pth in pth_files:
        lines = [
            line.strip()
            for line in pth.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not lines:
            return _fail(
                REASON_FOREIGN_SOURCE_BINDING,
                f"Editable pth is empty: {pth}. {_BOOTSTRAP_HINT}",
            )
        bound = Path(lines[0])
        if bound != expected_src:
            return _fail(
                REASON_FOREIGN_SOURCE_BINDING,
                (f"Editable pth binds {bound} instead of {expected_src}. {_BOOTSTRAP_HINT}"),
                source_binding=str(bound),
            )
    for url_path in url_files:
        try:
            payload = json.loads(url_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _fail(
                REASON_FOREIGN_SOURCE_BINDING,
                f"direct_url.json unreadable at {url_path}: {exc}. {_BOOTSTRAP_HINT}",
            )
        if not isinstance(payload, Mapping):
            return _fail(
                REASON_FOREIGN_SOURCE_BINDING,
                f"direct_url.json is not an object: {url_path}. {_BOOTSTRAP_HINT}",
            )
        bound_root = _direct_url_repo_root(payload)
        if bound_root is None or bound_root != expected_root:
            return _fail(
                REASON_FOREIGN_SOURCE_BINDING,
                (
                    f"direct_url.json binds {bound_root} instead of {expected_root}. "
                    f"{_BOOTSTRAP_HINT}"
                ),
                source_binding="" if bound_root is None else str(bound_root),
            )
    return IsolationResult(
        ok=True,
        reason_code=REASON_ISOLATION_PASS,
        exit_code=0,
        diagnostic="editable source binding matches this checkout",
        source_binding=str(expected_src),
    )


def validate_worktree_environment(
    repo_root: Path,
    *,
    python_version: str,
) -> IsolationResult:
    """Fail-closed local isolation. Ignores VIRTUAL_ENV."""
    symlink = assert_venv_is_local_directory(repo_root)
    if symlink is not None:
        return symlink
    venv = venv_dir(repo_root)
    if not venv.is_dir():
        return _fail(
            REASON_VENV_NOT_DIRECTORY,
            f".venv is not a directory at {venv}. {_BOOTSTRAP_HINT}",
        )
    fp = validate_fingerprint(repo_root, python_version=python_version)
    if not fp.ok:
        return fp
    source = discover_source_binding(repo_root)
    if not source.ok:
        return source
    return IsolationResult(
        ok=True,
        reason_code=REASON_ISOLATION_PASS,
        exit_code=0,
        diagnostic="per-worktree environment isolation proven",
        uv_lock_sha256=fp.uv_lock_sha256,
        pyproject_sha256=fp.pyproject_sha256,
        source_binding=source.source_binding,
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    repo_root_override = None
    if "--repo-root" in args:
        idx = args.index("--repo-root")
        if idx + 1 >= len(args):
            print("REASON_CODE=REPO_ROOT_UNRESOLVED", file=sys.stderr)
            return 7
        repo_root_override = Path(args[idx + 1])
        del args[idx : idx + 2]
    command = args[0] if args else "validate"
    start = Path(__file__).resolve()
    repo_root = repo_root_override
    if repo_root is None:
        for candidate in (start.parent, *start.parents):
            if (candidate / "pyproject.toml").is_file() and (candidate / "scripts/pt").is_file():
                repo_root = candidate
                break
    if repo_root is None or not (repo_root / "pyproject.toml").is_file():
        print("REASON_CODE=REPO_ROOT_UNRESOLVED", file=sys.stderr)
        return 7
    python_version = sys.version.split()[0]
    if command == "write-fingerprint":
        path = write_env_fingerprint(repo_root, python_version=python_version)
        print(str(path))
        return 0
    result = validate_worktree_environment(repo_root, python_version=python_version)
    print(f"REASON_CODE={result.reason_code}", file=sys.stderr)
    print(f"EXIT_CODE={result.exit_code}", file=sys.stderr)
    print(f"DIAGNOSTIC={result.diagnostic}", file=sys.stderr)
    if result.uv_lock_sha256:
        print(f"UV_LOCK_SHA256={result.uv_lock_sha256}", file=sys.stderr)
    if result.pyproject_sha256:
        print(f"PYPROJECT_SHA256={result.pyproject_sha256}", file=sys.stderr)
    if result.source_binding:
        print(f"SOURCE_BINDING={result.source_binding}", file=sys.stderr)
    return int(result.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
