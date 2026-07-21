from __future__ import annotations

import configparser
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PACKAGE_PARENTS = (Path("apps"), Path("libs"), Path("tools"))
CANONICAL_RECIPES = {"boundaries", "check", "fmt", "lint", "test", "typecheck"}


def _recipe_names(justfile: str) -> set[str]:
    pattern = re.compile(r"^([a-z][a-z0-9-]*)(?:\s+[^:]*)?:", re.MULTILINE)
    return set(pattern.findall(justfile))


def _package_paths() -> set[Path]:
    packages: set[Path] = set()
    for parent in PACKAGE_PARENTS:
        parent_path = ROOT / parent
        if not parent_path.is_dir():
            continue
        for candidate in parent_path.iterdir():
            if not candidate.is_dir() or candidate.name.startswith((".", "__")):
                continue
            if parent != Path("tools") or any(
                (candidate / name).exists()
                for name in ("AGENTS.md", "package.json", "pyproject.toml", "src", "tests")
            ):
                packages.add(candidate.relative_to(ROOT))
    return packages


def _pnpm_members(workspace: str) -> set[str]:
    members: set[str] = set()
    in_packages = False
    for line in workspace.splitlines():
        if line and not line[0].isspace():
            in_packages = line.rstrip() == "packages:"
            continue
        if in_packages:
            match = re.match(r"\s+-\s+['\"]?([^'\"#]+?)['\"]?\s*$", line)
            if match:
                members.add(match.group(1))
    return members


def _import_linter_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser(interpolation=None)
    config.read(ROOT / ".importlinter", encoding="utf-8")
    return config


def main() -> None:
    errors: list[str] = []
    package_paths = _package_paths()

    if not package_paths:
        errors.append("no workspace packages were found under apps/, libs/, or tools/")

    for package_path in sorted(package_paths):
        if not (ROOT / package_path / "AGENTS.md").is_file():
            errors.append(f"{package_path} is missing AGENTS.md")

        manifest_names = ("package.json", "pyproject.toml")
        if not any((ROOT / package_path / name).is_file() for name in manifest_names):
            errors.append(f"{package_path} is missing a package manifest")

        if not (ROOT / package_path / "src").is_dir():
            errors.append(f"{package_path} is missing src/")

        if not (ROOT / package_path / "tests").is_dir():
            errors.append(f"{package_path} is missing tests/")

    justfile = (ROOT / "justfile").read_text(encoding="utf-8")
    recipe_names = _recipe_names(justfile)
    agent_guide = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    documented_recipes = set(re.findall(r"`uv run just ([a-z][a-z0-9-]*)`", agent_guide))
    missing_recipes = documented_recipes - recipe_names
    if missing_recipes:
        errors.append(f"AGENTS.md names missing just recipes: {sorted(missing_recipes)}")
    undocumented_recipes = CANONICAL_RECIPES - documented_recipes
    if undocumented_recipes:
        errors.append(f"AGENTS.md is missing canonical commands: {sorted(undocumented_recipes)}")

    if "docs/STRUCTURE.md" not in agent_guide:
        errors.append("AGENTS.md must point to docs/STRUCTURE.md")

    for package_path in sorted(package_paths):
        if package_path.as_posix() not in agent_guide:
            errors.append(f"AGENTS.md repository map is missing {package_path}")
    mapped_packages = {
        Path(path)
        for path in re.findall(r"^- `((?:apps|libs|tools)/[^`]+)`", agent_guide, re.MULTILINE)
    }
    missing_mapped_packages = mapped_packages - package_paths
    if missing_mapped_packages:
        errors.append(
            "AGENTS.md maps packages missing from the repository: "
            f"{sorted(str(path) for path in missing_mapped_packages)}"
        )

    with (ROOT / "pyproject.toml").open("rb") as file:
        root_pyproject = tomllib.load(file)
    uv_members = set(root_pyproject["tool"]["uv"]["workspace"]["members"])
    python_packages = {
        path.as_posix() for path in package_paths if (ROOT / path / "pyproject.toml").is_file()
    }
    if uv_members != python_packages:
        errors.append(
            "uv workspace members do not match Python packages: "
            f"configured={sorted(uv_members)}, found={sorted(python_packages)}"
        )

    pnpm_members = _pnpm_members((ROOT / "pnpm-workspace.yaml").read_text(encoding="utf-8"))
    typescript_packages = {
        path.as_posix() for path in package_paths if (ROOT / path / "package.json").is_file()
    }
    if pnpm_members != typescript_packages:
        errors.append(
            "pnpm workspace members do not match TypeScript packages: "
            f"configured={sorted(pnpm_members)}, found={sorted(typescript_packages)}"
        )

    with (ROOT / "tach.toml").open("rb") as file:
        tach = tomllib.load(file)
    expected_source_roots = {f"{path}/src" for path in python_packages}
    tach_source_roots = set(tach.get("source_roots", []))
    if tach_source_roots != expected_source_roots:
        errors.append(
            "Tach source roots do not match Python packages: "
            f"configured={sorted(tach_source_roots)}, expected={sorted(expected_source_roots)}"
        )

    python_import_roots: set[str] = set()
    for package_path in python_packages:
        source_path = ROOT / package_path / "src"
        import_roots = {
            path.name
            for path in source_path.iterdir()
            if path.is_dir() and (path / "__init__.py").is_file()
        }
        if len(import_roots) != 1:
            errors.append(
                f"{package_path}/src must contain exactly one import package; "
                f"found {sorted(import_roots)}"
            )
        python_import_roots.update(import_roots)
    import_linter = _import_linter_config()
    configured_import_roots = set(import_linter["importlinter"].get("root_packages", "").split())
    if configured_import_roots != python_import_roots:
        errors.append(
            "Import Linter roots do not match Python import packages: "
            f"configured={sorted(configured_import_roots)}, found={sorted(python_import_roots)}"
        )

    layer_modules = set(
        re.findall(
            r"[A-Za-z_][A-Za-z0-9_.]*",
            import_linter["importlinter:contract:package-layers"].get("layers", ""),
        )
    )
    if layer_modules != configured_import_roots:
        errors.append(
            "Import Linter package layers do not cover every root package: "
            f"layers={sorted(layer_modules)}, roots={sorted(configured_import_roots)}"
        )

    backend_package = ROOT / "libs/backend/src/lhf_backend"
    if backend_package.is_dir():
        private_backend_modules = {
            f"lhf_backend.{path.stem}"
            for path in backend_package.glob("_*.py")
            if path.name != "__init__.py"
        }
        protected_backend_modules = set(
            import_linter["importlinter:contract:backend-public-interface"]
            .get("protected_modules", "")
            .split()
        )
        if protected_backend_modules != private_backend_modules:
            errors.append(
                "Import Linter protection does not match backend private modules: "
                f"protected={sorted(protected_backend_modules)}, "
                f"private={sorted(private_backend_modules)}"
            )

    root_package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    boundaries_script = root_package.get("scripts", {}).get("boundaries", "")
    for package_path in sorted(typescript_packages):
        source_root = f"{package_path}/src"
        if source_root not in boundaries_script:
            errors.append(f"root boundaries script does not cruise {source_root}")

    if errors:
        raise SystemExit("\n".join(errors))

    print("Repository structure is current.")


if __name__ == "__main__":
    main()
