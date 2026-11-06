from __future__ import annotations

SAFE_DEV_PACKAGES: set[str] = {
    "pytest",
    "pytest-cov",
    "ruff",
    "black",
    "mypy",
    "pyright",
    "pre-commit",
    "pip-audit",
    "httpx",
    "tomli",
}

BLOCKED_PACKAGES: set[str] = {
    "fastapi",
    "uvicorn",
    "ccxt",
    "prometheus-client",
    "numpy",
    "pandas",
    "pydantic",
    "pyarrow",
    "urllib3",
    "mlflow",
    "chromadb",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp",
}

# Per-surface operator metadata (category + how findings on this surface should be described).
SURFACE_METADATA: dict[str, dict[str, str]] = {
    "pyproject.toml": {
        "category": "python_dependencies",
        "description": (
            "Dev dependency `{item_name}` declared under pyproject.toml "
            "(optional-dependencies.dev or dependency-groups.dev)."
        ),
    },
    "github_actions": {
        "category": "ci_integrations",
        "description": "GitHub Actions third-party reference `{item_name}` from workflow YAML uses: line.",
    },
}

PROFILES: dict[str, dict[str, object]] = {
    "dev_tooling_review": {
        "surfaces": ["pyproject.toml", "github_actions"],
        "safe_packages": SAFE_DEV_PACKAGES,
        "blocked_packages": BLOCKED_PACKAGES,
        "surface_metadata": SURFACE_METADATA,
    },
}


def surface_category(profile: str, surface: str) -> str:
    meta = _surface_meta_map(profile)
    return meta.get(surface, {}).get("category", "unknown")


def surface_finding_description(profile: str, surface: str, item_name: str) -> str:
    meta = _surface_meta_map(profile)
    tpl = meta.get(surface, {}).get("description", "Scanned item `{item_name}`.")
    return tpl.format(item_name=item_name)


def _surface_meta_map(profile: str) -> dict[str, dict[str, str]]:
    cfg = PROFILES[profile]
    raw = cfg.get("surface_metadata")
    if isinstance(raw, dict):
        return raw  # type: ignore[return-value]
    return SURFACE_METADATA


__all__ = [
    "BLOCKED_PACKAGES",
    "PROFILES",
    "SAFE_DEV_PACKAGES",
    "SURFACE_METADATA",
    "surface_category",
    "surface_finding_description",
]
