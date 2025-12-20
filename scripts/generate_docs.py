#!/usr/bin/env python3
"""
Automatically generate API documentation from docstrings.
"""

from pathlib import Path


def generate_module_doc(module_path: Path, output_dir: Path, src_dir: Path):
    """Generate markdown documentation for a Python module."""
    # Calculate relative module path from src directory
    relative_path = module_path.relative_to(src_dir)
    module_name = str(relative_path).replace("/", ".").replace(".py", "")

    # Skip __pycache__ and other special directories
    if "__pycache__" in str(module_path) or module_path.name.startswith("."):
        return

    # Create output file path
    output_file = output_dir / f"{module_name}.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Generate markdown with mkdocstrings syntax
    with open(output_file, "w") as f:
        f.write(f"# {module_name}\n\n")
        f.write(f"::: src.{module_name}\n")
        f.write("    options:\n")
        f.write("      show_source: true\n")
        f.write("      show_root_heading: true\n")

    print(f"✅ Generated: {output_file}")


def generate_package_index(package_path: Path, output_dir: Path, src_dir: Path):
    """Generate index page for a package."""
    relative_path = package_path.relative_to(src_dir)
    package_name = str(relative_path).replace("/", ".")

    output_file = output_dir / package_name.replace(".", "/") / "index.md"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Find all modules in package
    modules = []
    for py_file in package_path.glob("*.py"):
        if py_file.name != "__init__.py":
            modules.append(py_file.stem)

    with open(output_file, "w") as f:
        f.write(f"# {package_name}\n\n")
        f.write(f"Package overview for `{package_name}`.\n\n")

        if modules:
            f.write("## Modules\n\n")
            for module in sorted(modules):
                f.write(f"- [{module}]({module}.md)\n")

    print(f"✅ Generated: {output_file}")


def main():
    """Generate docs for all modules."""
    src_dir = Path("src")
    docs_dir = Path("docs/api")

    # Clean and recreate API docs directory
    if docs_dir.exists():
        import shutil

        shutil.rmtree(docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    print("🔍 Generating API documentation...\n")

    # Generate docs for each Python file
    for py_file in src_dir.rglob("*.py"):
        if py_file.name != "__init__.py":
            generate_module_doc(py_file, docs_dir, src_dir)

    # Generate package index pages
    for package_dir in src_dir.rglob("*"):
        if (
            package_dir.is_dir()
            and (package_dir / "__init__.py").exists()
            and "__pycache__" not in str(package_dir)
        ):
            generate_package_index(package_dir, docs_dir, src_dir)

    print("\n✅ API documentation generated successfully!")
    print(f"📁 Output directory: {docs_dir}")
    print("\n💡 Next steps:")
    print("  1. Build docs: mkdocs build")
    print("  2. Serve locally: mkdocs serve")
    print("  3. Deploy: mkdocs gh-deploy")


if __name__ == "__main__":
    main()
