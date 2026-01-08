#!/usr/bin/env python3
"""
Validate Layer Map Configuration

Validates:
- TOML syntax for all capability scopes and model registry
- Layer mapping completeness (L0-L6)
- Capability scope required fields
- Model registry structure

Usage:
    python scripts/validate_layer_map_config.py
"""

import sys
from pathlib import Path

try:
    import tomli as toml
except ImportError:
    import tomllib as toml


def main():
    workspace = Path(__file__).parent.parent
    errors = []

    print("=" * 60)
    print("Layer Map Configuration Validation")
    print("=" * 60)

    # 1. Validate Model Registry
    print("\n1. Model Registry Validation...")
    registry_path = workspace / "config" / "model_registry.toml"
    try:
        with open(registry_path, "rb") as f:
            registry = toml.load(f)
        print(f"   ✅ {registry_path.name}: Syntax VALID")

        # Check layer mapping completeness
        layers = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
        missing_layers = [l for l in layers if l not in registry.get("layer_mapping", {})]
        if missing_layers:
            errors.append(f"Model Registry: Missing layer mappings: {missing_layers}")
            print(f"   ❌ Missing layer mappings: {missing_layers}")
        else:
            print(f"   ✅ All 7 layers mapped (L0-L6)")

        # Check model definitions
        expected_models = [
            "gpt-5-2-pro", "gpt-5-2", "gpt-5-mini",
            "o3-deep-research", "o3-pro", "o3", "o4-mini-deep-research",
            "deepseek-r1"
        ]
        defined_models = list(registry.get("models", {}).keys())
        missing_models = [m for m in expected_models if m not in defined_models]
        if missing_models:
            errors.append(f"Model Registry: Missing model definitions: {missing_models}")
            print(f"   ❌ Missing models: {missing_models}")
        else:
            print(f"   ✅ All {len(expected_models)} models defined")

    except FileNotFoundError:
        errors.append(f"Model Registry not found: {registry_path}")
        print(f"   ❌ File not found: {registry_path}")
    except Exception as e:
        errors.append(f"Model Registry error: {e}")
        print(f"   ❌ Error: {e}")

    # 2. Validate Capability Scopes
    print("\n2. Capability Scopes Validation...")
    scope_dir = workspace / "config" / "capability_scopes"

    if not scope_dir.exists():
        errors.append(f"Capability scopes directory not found: {scope_dir}")
        print(f"   ❌ Directory not found: {scope_dir}")
    else:
        scope_files = list(scope_dir.glob("*.toml"))
        print(f"   Found {len(scope_files)} capability scope files")

        required_sections = ["scope", "models", "inputs", "outputs", "tooling", "logging", "safety"]

        for scope_file in scope_files:
            try:
                with open(scope_file, "rb") as f:
                    scope_config = toml.load(f)

                # Check required sections
                missing_sections = [s for s in required_sections if s not in scope_config]
                if missing_sections:
                    errors.append(f"{scope_file.name}: Missing sections: {missing_sections}")
                    print(f"   ❌ {scope_file.name}: Missing {missing_sections}")
                else:
                    print(f"   ✅ {scope_file.name}: All required sections present")

                # Check layer_id
                layer_id = scope_config.get("scope", {}).get("layer_id")
                if not layer_id:
                    errors.append(f"{scope_file.name}: Missing layer_id")
                    print(f"   ⚠️  {scope_file.name}: Missing layer_id")
                else:
                    print(f"      Layer: {layer_id}")

            except Exception as e:
                errors.append(f"{scope_file.name}: {e}")
                print(f"   ❌ {scope_file.name}: {e}")

    # 3. Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ VALIDATION FAILED: {len(errors)} error(s)")
        for err in errors:
            print(f"   - {err}")
        return 1
    else:
        print("✅ VALIDATION PASSED: All configurations valid")
        return 0


if __name__ == "__main__":
    sys.exit(main())
