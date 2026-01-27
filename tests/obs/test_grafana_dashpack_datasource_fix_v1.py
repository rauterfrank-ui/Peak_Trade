import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ALLOW_UIDS = {
    "peaktrade-prometheus-local",
    "peaktrade-prometheus-main",
    "peaktrade-prometheus-shadow",
    "peaktrade-prometheus",
}

ALLOW_NAMES = {
    "prometheus-local",
    "prometheus-main",
    "prometheus-shadow",
    "prometheus",
}


@dataclass(frozen=True)
class DsRef:
    path: str
    value: Any


def iter_ds_refs(node: Any, base: str = "") -> Iterable[DsRef]:
    if isinstance(node, dict):
        if "datasource" in node:
            yield DsRef(
                path=f"{base}.datasource" if base else "datasource", value=node["datasource"]
            )
        for k, v in node.items():
            child = f"{base}.{k}" if base else str(k)
            yield from iter_ds_refs(v, child)
    elif isinstance(node, list):
        for i, it in enumerate(node):
            child = f"{base}[{i}]" if base else f"[{i}]"
            yield from iter_ds_refs(it, child)


def load_dashboards() -> list[tuple[Path, dict]]:
    dash_dir = Path("docs") / "webui" / "observability" / "grafana" / "dashboards"
    files = sorted(dash_dir.glob("**/*.json"))
    assert files, f"no dashboards found under {dash_dir}"
    out: list[tuple[Path, dict]] = []
    for p in files:
        out.append((p, json.loads(p.read_text(encoding="utf-8"))))
    return out


def test_no_unknown_datasource_refs_in_dashboards() -> None:
    dashboards = load_dashboards()
    bad: list[str] = []

    for p, doc in dashboards:
        for ref in iter_ds_refs(doc):
            v = ref.value
            if isinstance(v, dict):
                uid = v.get("uid")
                if uid is None:
                    # default datasource is allowed
                    continue
                if not isinstance(uid, str):
                    bad.append(f"{p}:{ref.path} uid_not_string={uid!r}")
                    continue
                if uid.startswith("${DS_") or uid.startswith("$DS_") or uid.startswith("DS_"):
                    bad.append(f"{p}:{ref.path} uid_unresolved_var={uid!r}")
                    continue
                if uid not in ALLOW_UIDS:
                    bad.append(f"{p}:{ref.path} uid_not_allowlisted={uid!r}")
                    continue
            elif isinstance(v, str):
                if v.startswith("${DS_") or v.startswith("$DS_") or v.startswith("DS_"):
                    bad.append(f"{p}:{ref.path} ds_string_unresolved_var={v!r}")
                    continue
                if v not in ALLOW_UIDS and v not in ALLOW_NAMES:
                    bad.append(f"{p}:{ref.path} ds_string_not_allowlisted={v!r}")
                    continue
            else:
                # None / other types are tolerated (Grafana may use default)
                continue

    assert not bad, "unknown datasource refs found:\n" + "\n".join(bad)
