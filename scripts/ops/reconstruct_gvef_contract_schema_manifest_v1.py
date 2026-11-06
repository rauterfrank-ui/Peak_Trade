"""Recover the missing V1.5 schema data from retained generator literals only.

Never execute the historical program or derive expectations from current models.
The output is reconstructed data, not a recovered original execution/result.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_ROOT = Path("docs/ops/evidence/self_learning_reconstruction_resolution_v1_2026_11_04")
OUTPUT_ROOT = Path("evidence/research/gvef_blueprint_v15_build_ready_v1/20261004T083919Z")


class ReconstructionError(ValueError):
    """Reject a source shape that the bounded literal extractor does not support."""


def reconstruct_contract_schema_manifest_v1(
    builder_source: str, closure_source: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    tree = ast.parse(builder_source)
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "fields")
    result = helper.body[0]
    if not isinstance(result, ast.Return) or not isinstance(result.value, ast.ListComp):
        raise ReconstructionError("FIELDS_HELPER_SHAPE_UNSUPPORTED")
    comprehension = result.value
    if not isinstance(comprehension.elt, ast.Dict) or len(comprehension.generators) != 1:
        raise ReconstructionError("FIELDS_HELPER_SHAPE_UNSUPPORTED")
    target = comprehension.generators[0].target
    if not isinstance(target, ast.Tuple):
        raise ReconstructionError("FIELDS_HELPER_BINDINGS_UNSUPPORTED")
    names = [n.id for n in target.elts if isinstance(n, ast.Name)]
    values = comprehension.elt.values
    if (
        len(names) != 9
        or not all(isinstance(n, ast.Name) for n in values)
        or [n.id for n in values] != names
    ):
        raise ReconstructionError("FIELDS_HELPER_BINDINGS_UNSUPPORTED")
    columns = [ast.literal_eval(key) for key in comprehension.elt.keys]
    if not all(isinstance(k, str) for k in columns) or len(set(columns)) != 9:
        raise ReconstructionError("FIELDS_HELPER_COLUMNS_UNSUPPORTED")

    def fields(call: ast.AST, *, extra: list[Any] | None = None) -> list[dict[str, Any]]:
        if (
            not isinstance(call, ast.Call)
            or not isinstance(call.func, ast.Name)
            or call.func.id != "fields"
            or call.keywords
        ):
            raise ReconstructionError("SCHEMA_CALL_UNSUPPORTED")
        if any(isinstance(arg, ast.Starred) for arg in call.args):
            if (
                len(call.args) != 1
                or not isinstance(call.args[0], ast.Starred)
                or not isinstance(call.args[0].value, ast.Name)
                or call.args[0].value.id != "extra"
                or extra is None
            ):
                raise ReconstructionError("SCHEMA_EXPANSION_UNSUPPORTED")
            tuples = extra
        else:
            tuples = [ast.literal_eval(arg) for arg in call.args]
        if not all(isinstance(row, (list, tuple)) and len(row) == 9 for row in tuples):
            raise ReconstructionError("SCHEMA_ROW_ARITY_MISMATCH")
        return [dict(zip(columns, row)) for row in tuples]

    schemas: dict[str, Any] = {}
    digest_model = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id == "SCHEMAS":
                if not isinstance(node.value, ast.Dict):
                    raise ReconstructionError("SCHEMAS_LITERAL_REQUIRED")
                schemas = {
                    ast.literal_eval(k): fields(v)
                    for k, v in zip(node.value.keys, node.value.values)
                }
            elif isinstance(target, ast.Name) and target.id == "DIGEST_MODEL":
                digest_model = ast.literal_eval(node.value)
            elif (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == "SCHEMAS"
            ):
                schemas[ast.literal_eval(target.slice)] = fields(node.value)
        elif (
            isinstance(node, ast.For)
            and isinstance(node.target, ast.Tuple)
            and [n.id for n in node.target.elts if isinstance(n, ast.Name)] == ["name", "extra"]
        ):
            if len(node.body) != 1 or not isinstance(node.body[0], ast.Assign):
                raise ReconstructionError("SCHEMA_EXTENSION_BODY_UNSUPPORTED")
            assignment = node.body[0]
            target = assignment.targets[0]
            if (
                not isinstance(target, ast.Subscript)
                or not isinstance(target.value, ast.Name)
                or target.value.id != "SCHEMAS"
                or not isinstance(target.slice, ast.Name)
                or target.slice.id != "name"
            ):
                raise ReconstructionError("SCHEMA_EXTENSION_TARGET_UNSUPPORTED")
            for name, extra in ast.literal_eval(node.iter):
                if name in schemas:
                    raise ReconstructionError("DUPLICATE_SCHEMA_EXTENSION")
                schemas[name] = fields(assignment.value, extra=extra)
    if len(schemas) != 16 or not isinstance(digest_model, dict):
        raise ReconstructionError("SIXTEEN_ORIGINAL_SCHEMAS_AND_DIGEST_MODEL_REQUIRED")
    # Retained closure fix_contract_schema, not a decision inferred from current
    # enums/models: exact literal normalization of its declared fan-out names.
    closure = ast.parse(closure_source)
    canonical_fanout = next(
        ast.literal_eval(n.value)
        for n in closure.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "CANONICAL_FANOUT" for t in n.targets)
    )
    fix = next(
        n
        for n in closure.body
        if isinstance(n, ast.FunctionDef) and n.name == "fix_contract_schema"
    )
    fix_text = ast.get_source_segment(closure_source, fix)
    expected_verdict = "fail-closed; WHOLE_SYSTEM_REPROOF via resolver"
    if (
        'blob.replace("LOCAL|DOWNSTREAM|WHOLE_SYSTEM_REPROOF", enum_str)' not in fix_text
        or expected_verdict not in fix_text
    ):
        raise ReconstructionError("CLOSURE_NORMALIZATION_SHAPE_UNSUPPORTED")
    payload = json.loads(
        json.dumps(dict(schemas=schemas, digest_model=digest_model)).replace(
            "LOCAL|DOWNSTREAM|WHOLE_SYSTEM_REPROOF", "|".join(canonical_fanout)
        )
    )
    payload["digest_model"]["verdicts"]["DIGEST_CHANGED_UNEXPECTED"] = expected_verdict
    provenance = dict(
        reconstruction_method="Bounded AST literal/fields extraction plus exact retained closure normalization; historical code NOT executed; current Pydantic models NOT read",
        builder_source_sha256=hashlib.sha256(builder_source.encode()).hexdigest(),
        closure_source_sha256=hashlib.sha256(closure_source.encode()).hexdigest(),
        closure_fix_source_sha256=hashlib.sha256(fix_text.encode()).hexdigest(),
        schema_count=len(schemas),
        field_count=sum(map(len, schemas.values())),
        original_generated_output_bytes_recovered=False,
        reconstructed_at="2026-11-04",
        runtime_authority="NONE",
    )
    return payload, provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Create only the two exact reconstructed data/provenance files; reject divergent existing files",
    )
    args = parser.parse_args()
    payload, provenance = reconstruct_contract_schema_manifest_v1(
        (SOURCE_ROOT / "gvef_builder.reconstructed.py.txt").read_text(),
        (SOURCE_ROOT / "gvef_closure.reconstructed.py.txt").read_text(),
    )
    raw = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    provenance["contract_manifest_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
    provenance["source_refs"] = [
        str(SOURCE_ROOT / name)
        for name in ("gvef_builder.reconstructed.py.txt", "gvef_closure.reconstructed.py.txt")
    ]
    if args.write:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        for name, text in (
            ("contract_schema_manifest.json", raw),
            (
                "contract_schema_manifest.reconstruction_provenance.json",
                json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            ),
        ):
            path = OUTPUT_ROOT / name
            if path.exists() and path.read_text() != text:
                raise ReconstructionError("DIVERGENT_EXISTING_OUTPUT:" + str(path))
            if not path.exists():
                path.write_text(text)
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
