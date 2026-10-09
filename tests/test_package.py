"""Environment smoke test: the package must be importable after uv sync."""


def test_package_imports() -> None:
    import type_speed

    assert type_speed.__version__ == "0.1.0"
