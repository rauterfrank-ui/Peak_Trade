"""Shared pin fixtures for the guardian framework. Historical pins stay historical."""

from __future__ import annotations

from typing import Any

AUTHORIZED_COMMIT = "2f07e9cc6d22400f719b5db26ede746c76a9cce0"
AUTHORIZED_TREE = "069d556cdad7393aaab0bf5d51d67e0220fe8d20"
CENSUS_EMBEDDED_PIN = "6216201d7acbc771f84b6b6884eccc41359927cf"
LANDSCAPE_EMBEDDED_COMMIT = "e5d9296fb269208b06980518d410b4f2b616bf5b"
LANDSCAPE_EMBEDDED_TREE = "6422bfde79fd5aa45d2939a821980abf9aa4e3df"
GRAPH_ABSENT_PIN = "0000000000000000000000000000000000000000"
GRAPH_LEGACY_PIN = "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a"

SCOPE_FIELDS = (
    "domain_functional_members",
    "external_interfaces_under_observation",
    "external_references_only",
    "explicitly_out_of_scope",
    "unresolved",
)


def honest_provenance(**overrides: str) -> dict[str, dict[str, str]]:
    body = {
        "census": {"pin": CENSUS_EMBEDDED_PIN, "currency": "HISTORICAL"},
        "landscape": {
            "commit_pin": LANDSCAPE_EMBEDDED_COMMIT,
            "tree_pin": LANDSCAPE_EMBEDDED_TREE,
            "currency": "HISTORICAL",
        },
        "graph": {"pin": GRAPH_ABSENT_PIN, "currency": "ABSENT"},
        "domain_evidence": {
            "commit_pin": AUTHORIZED_COMMIT,
            "tree_pin": AUTHORIZED_TREE,
        },
    }
    if "census_pin" in overrides:
        body["census"]["pin"] = overrides["census_pin"]
    if "census_currency" in overrides:
        body["census"]["currency"] = overrides["census_currency"]
    if "landscape_commit" in overrides:
        body["landscape"]["commit_pin"] = overrides["landscape_commit"]
    if "landscape_tree" in overrides:
        body["landscape"]["tree_pin"] = overrides["landscape_tree"]
    if "landscape_currency" in overrides:
        body["landscape"]["currency"] = overrides["landscape_currency"]
    if "graph_pin" in overrides:
        body["graph"]["pin"] = overrides["graph_pin"]
    if "graph_currency" in overrides:
        body["graph"]["currency"] = overrides["graph_currency"]
    return body


def scope_of(
    members: list[str] | None = None,
    *,
    interfaces: list[str] | None = None,
    references: list[str] | None = None,
    excluded: list[str] | None = None,
    unresolved: list[str] | None = None,
) -> dict[str, list[str]]:
    return {
        "domain_functional_members": ["node-a"] if members is None else members,
        "external_interfaces_under_observation": [] if interfaces is None else interfaces,
        "external_references_only": [] if references is None else references,
        "explicitly_out_of_scope": [] if excluded is None else excluded,
        "unresolved": [] if unresolved is None else unresolved,
    }


def chain_scope() -> dict[str, list[str]]:
    return scope_of(["node-a", "node-b", "node-c", "node-d"])


def bind_kwargs(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "authoritative_commit_sha": AUTHORIZED_COMMIT,
        "authoritative_tree_sha": AUTHORIZED_TREE,
        "declared_commit_sha": AUTHORIZED_COMMIT,
        "declared_tree_sha": AUTHORIZED_TREE,
        "provenance": honest_provenance(),
        "scope": scope_of(),
    }
    payload.update(overrides)
    return payload
