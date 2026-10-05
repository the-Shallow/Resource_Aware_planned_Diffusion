from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_project_documentation_exists():
    assert (REPOSITORY_ROOT / "CODEBASE_ANALYSIS.md").is_file()
    assert (REPOSITORY_ROOT / "CONTRIBUTING.md").is_file()
    assert (REPOSITORY_ROOT / "docs" / "PROJECT_SETUP.md").is_file()


def test_project_packages_exist():
    package_root = REPOSITORY_ROOT / "semantic_parallel"
    assert (package_root / "__init__.py").is_file()
    assert (package_root / "scheduler" / "__init__.py").is_file()
    assert (package_root / "distributed" / "__init__.py").is_file()
    assert (package_root / "profiling" / "__init__.py").is_file()
