"""Repository-truth discovery for Operator-GO / Session-Preregistration surfaces."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.constants_v1 import (
    CAPABILITY_ID,
    CAPABILITY_SOURCE_RELPATHS,
    CLI_RELPATH,
    CONFIG_RELPATH,
    CONTRACT_DOC_RELPATH,
    OBSERVATION_CONFIG_RELPATH,
    OBSERVATION_PACKAGE_RELPATH,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    REQUIRED_DISCOVERY_SYMBOLS,
    SCHEMA_VERSION,
)


@dataclass(frozen=True)
class DiscoveryFactV1:
    fact_id: str
    present: bool
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SessionPreregistrationGoDiscoveryResultV1:
    schema_id: str
    schema_version: str
    capability_id: str
    package_marker: str
    SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT: bool
    blockers: list[str] = field(default_factory=list)
    facts: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _file_exists(repo_root: Path, relpath: str) -> bool:
    path = (repo_root / relpath).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        return False
    return path.is_file()


def _dir_exists(repo_root: Path, relpath: str) -> bool:
    path = (repo_root / relpath).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        return False
    return path.is_dir()


def _module_defines_symbol(repo_root: Path, relpath: str, symbol: str) -> bool:
    path = repo_root / relpath
    if not path.is_file():
        return False
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                return True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == symbol:
                    return True
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == symbol:
                return True
    return False


def _config_declares_schema(repo_root: Path) -> bool:
    path = repo_root / CONFIG_RELPATH
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    required = (
        'schema_version = "paper_shadow_observation_operator_go_session_preregistration.v1"',
        "venue_allowed",
        "market_type_allowed",
        "confirm_token_policy",
        "orders_authorized = false",
        "testnet_authorized = false",
        "live_authorized = false",
        "wallclock_session_execution_allowed = false",
    )
    return all(item in text for item in required)


def discover_session_preregistration_and_operator_go_contract_present_v1(
    *,
    repo_root: Path | None = None,
) -> SessionPreregistrationGoDiscoveryResultV1:
    """True only when versioned contracts, verifier, binding and symbols exist.

    File existence alone is insufficient.
    """
    root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    facts: list[DiscoveryFactV1] = []
    blockers: list[str] = []
    notes = [
        "DISCOVERY_FROM_REPOSITORY_TRUTH",
        "FILE_EXISTENCE_ALONE_INSUFFICIENT",
        "READINESS_IS_NOT_AUTHORIZATION",
        f"PRODUCER_FAMILY={PRODUCER_FAMILY}",
    ]

    for rel in CAPABILITY_SOURCE_RELPATHS:
        present = _file_exists(root, rel)
        facts.append(DiscoveryFactV1(f"SOURCE:{rel}", present, rel))
        if not present:
            blockers.append(f"CAPABILITY_SOURCE_MISSING:{rel}")

    for rel, symbol in REQUIRED_DISCOVERY_SYMBOLS:
        present = _module_defines_symbol(root, rel, symbol)
        facts.append(DiscoveryFactV1(f"SYMBOL:{rel}:{symbol}", present, symbol))
        if not present:
            blockers.append(f"REQUIRED_SYMBOL_MISSING:{symbol}")

    config_ok = _config_declares_schema(root)
    facts.append(DiscoveryFactV1("CONFIG_SCHEMA_COMPLETE", config_ok, CONFIG_RELPATH))
    if not config_ok:
        blockers.append("CONFIG_SCHEMA_INCOMPLETE")

    doc_ok = _file_exists(root, CONTRACT_DOC_RELPATH)
    facts.append(DiscoveryFactV1("CONTRACT_DOC_PRESENT", doc_ok, CONTRACT_DOC_RELPATH))
    if not doc_ok:
        blockers.append("CONTRACT_DOC_MISSING")

    cli_ok = _file_exists(root, CLI_RELPATH)
    facts.append(DiscoveryFactV1("CLI_PRESENT", cli_ok, CLI_RELPATH))
    if not cli_ok:
        blockers.append("CLI_MISSING")

    observation_bound = _dir_exists(root, OBSERVATION_PACKAGE_RELPATH) and _file_exists(
        root, OBSERVATION_CONFIG_RELPATH
    )
    facts.append(
        DiscoveryFactV1(
            "OBSERVATION_CAPABILITY_BINDING_PRESENT",
            observation_bound,
            OBSERVATION_PACKAGE_RELPATH,
        )
    )
    if not observation_bound:
        blockers.append("OBSERVATION_CAPABILITY_BINDING_MISSING")

    # Binding must reference observation readiness producer.
    readiness_path = (
        "src/ops/integrated_paper_shadow_observation_session_v1/readiness_producer_v1.py"
    )
    readiness_text_ok = False
    if _file_exists(root, readiness_path):
        text = (root / readiness_path).read_text(encoding="utf-8")
        readiness_text_ok = (
            "discover_session_preregistration_and_operator_go_contract_present_v1" in text
        )
    facts.append(
        DiscoveryFactV1(
            "OBSERVATION_READINESS_PRODUCER_WIRES_DISCOVERY",
            readiness_text_ok,
            readiness_path,
        )
    )
    if not readiness_text_ok:
        blockers.append("OBSERVATION_READINESS_PRODUCER_NOT_WIRED")

    present = not blockers
    return SessionPreregistrationGoDiscoveryResultV1(
        schema_id=f"{PRODUCER_FAMILY}.discovery",
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        package_marker=PACKAGE_MARKER,
        SESSION_PREREGISTRATION_AND_OPERATOR_GO_CONTRACT_PRESENT=present,
        blockers=sorted(set(blockers)),
        facts=[f.to_dict() for f in facts],
        notes=notes,
    )
