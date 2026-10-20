import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CONTEXTS = (
    "accounts",
    "catalog",
    "inventory",
    "sales",
    "shifts",
    "purchasing",
    "reporting",
    "settings",
    "shared",
)
FORBIDDEN_ROOTS = {"django", "rest_framework"}


def _domain_modules() -> list[Path]:
    modules: list[Path] = []
    for context in CONTEXTS:
        domain = BACKEND_ROOT / context / "domain"
        if domain.is_dir():
            modules.extend(sorted(domain.rglob("*.py")))
    return modules


def _imported_roots(module_path: Path) -> set[str]:
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def test_domain_packages_were_found():
    assert len(_domain_modules()) > 10


@pytest.mark.parametrize(
    "module_path",
    _domain_modules(),
    ids=lambda path: str(path.relative_to(BACKEND_ROOT)),
)
def test_domain_code_does_not_import_django_or_drf(module_path: Path):
    forbidden = _imported_roots(module_path) & FORBIDDEN_ROOTS

    assert forbidden == set(), f"{module_path.name} imports {sorted(forbidden)}"
