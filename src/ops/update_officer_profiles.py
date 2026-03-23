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

PROFILES: dict[str, dict[str, object]] = {
    "dev_tooling_review": {
        "surfaces": ["pyproject.toml", "github_actions"],
        "safe_packages": SAFE_DEV_PACKAGES,
        "blocked_packages": BLOCKED_PACKAGES,
    },
}

__all__ = ["PROFILES", "SAFE_DEV_PACKAGES", "BLOCKED_PACKAGES"]
