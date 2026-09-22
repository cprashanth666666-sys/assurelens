"""Guards for the ways this application can be correct in source and broken
when deployed.

Both cases below shipped undetected on Day 1 and were only found when the
image was built and run for the first time.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from app.config import Settings
from app.seed.controls import FRAMEWORK_FILES, controls_directory

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = REPO_ROOT / "backend" / "Dockerfile"


def test_controls_directory_honours_the_setting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The container sets CONTROLS_DIR explicitly.

    Deriving the path from the source tree yielded "/controls" in the image —
    a location that existed only because docker-compose happened to bind-mount
    it there, and which does not exist on a real deployment.
    """
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/d")
    monkeypatch.setenv("CONTROLS_DIR", "/opt/assurelens/controls")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assert controls_directory() == Path("/opt/assurelens/controls")
    finally:
        get_settings.cache_clear()


def test_controls_directory_falls_back_to_the_repo_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unset value means "derive it", which is right for a venv checkout."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/d")
    monkeypatch.delenv("CONTROLS_DIR", raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assert controls_directory() == REPO_ROOT / "controls"
    finally:
        get_settings.cache_clear()


def test_the_library_actually_exists_where_we_point() -> None:
    for filename in (*FRAMEWORK_FILES, "meridian_scope.yaml"):
        assert (REPO_ROOT / "controls" / filename).exists(), filename


def test_dockerfile_ships_the_control_library() -> None:
    """The library is the product's content, not a fixture.

    Building from ./backend left it out of the image entirely, so a deployed
    backend would have come up with an empty control library and a 404 on
    /api/engagement — schema right, application useless.
    """
    text = DOCKERFILE.read_text(encoding="utf-8")

    assert "COPY controls/" in text
    assert "CONTROLS_DIR=" in text


def test_dockerfile_creates_the_package_stub_before_installing() -> None:
    """pyproject declares `packages = ["app"]`, resolved at install time.

    Installing before the source is copied fails with "package directory 'app'
    does not exist". The stub keeps the dependency layer cacheable, which on a
    free-tier host is minutes per deploy.
    """
    text = DOCKERFILE.read_text(encoding="utf-8")
    install = re.search(r"COPY backend/pyproject\.toml.*?pip install", text, re.S)

    assert install, "dependency layer not found in Dockerfile"
    assert "mkdir -p app" in install.group(0)


def test_settings_default_leaves_controls_dir_unset() -> None:
    """A hardcoded default would hide the container/source distinction again."""
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None, database_url="postgresql+psycopg://u:p@h:5432/d"
    )
    assert settings.controls_dir == ""


def test_estate_seed_uses_core_executemany_not_orm_bulk_insert() -> None:
    """A performance guard with a correctness-shaped failure mode.

    `insert(Model)` is an ORM bulk insert that fetches generated primary keys
    back, which degrades to one `INSERT ... RETURNING` per row. Swapping the
    Core form for it took the estate seed from 4 seconds to 9 minutes, and
    nothing failed -- the data was identical, so only the clock showed it.

    The regression was introduced while silencing a type error, which is
    exactly how it would come back.
    """
    tree = ast.parse(
        (REPO_ROOT / "backend" / "app" / "seed" / "meridian.py").read_text(
            encoding="utf-8"
        )
    )

    # Parsed rather than grepped: the module docstring explains this very
    # distinction, and a regex over the text matched the explanation.
    orm_bulk = [
        node.args[0].id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "insert"
        and node.args
        and isinstance(node.args[0], ast.Name)
    ]

    assert not orm_bulk, (
        f"ORM bulk insert used for {orm_bulk}; use insert(_table(Model)) so "
        f"psycopg can executemany"
    )


def test_estate_wipe_does_not_synchronise_the_session() -> None:
    """Deleting 110,000 rows through the ORM's default strategy loads every
    one into the identity map to reconcile in-memory objects. Nothing reads
    them afterwards, so there is nothing to reconcile."""
    source = (REPO_ROOT / "backend" / "app" / "seed" / "meridian.py").read_text(
        encoding="utf-8"
    )

    assert "synchronize_session=False" in source


def test_seed_skips_an_existing_estate() -> None:
    """The boot command runs the seed on every restart.

    The control library is upserted each time, so edits ship with the deploy.
    The estate is not: it is bulk data derived from a seed, so rebuilding
    24,000 rows on every restart changes nothing and takes long enough to
    fail a platform health check, leaving the service flapping.
    """
    source = (REPO_ROOT / "backend" / "app" / "seed" / "meridian.py").read_text(
        encoding="utf-8"
    )

    assert "def estate_is_populated" in source
    assert "force" in source, "a forced re-seed must still be possible"


def test_render_boots_migrate_then_seed_then_serve() -> None:
    """Order matters: a schema without content is a 404 on every endpoint."""
    render = (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")

    migrate = render.index("alembic upgrade head")
    seed = render.index("python -m app.seed")
    serve = render.index("uvicorn app.main:app")

    assert migrate < seed < serve


def test_dockerignore_excludes_the_local_virtualenv() -> None:
    """A 495 MB Windows virtualenv was being copied into a Linux image.

    `COPY backend/ ./` takes everything the build context contains, and
    without a .dockerignore the context was the whole repository -- venv and
    node_modules included. Useless in the image, and large enough that the
    upload alone could exhaust a free-tier build.
    """
    ignored = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")

    for pattern in (".venv/", "node_modules/", ".git/"):
        assert pattern in ignored, f"{pattern} must not enter the build context"


def test_dockerignore_excludes_env_files() -> None:
    """A secret copied into a layer stays in that layer even if a later one
    deletes it."""
    ignored = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")

    assert ".env" in ignored
    assert "!.env.example" in ignored, "the template is safe and useful"


def test_production_image_omits_test_tooling() -> None:
    """pytest, ruff and mypy have no business in a deployed container."""
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert '.[dev]' not in dockerfile
    assert 'pip install "."' in dockerfile


def test_declared_dependencies_are_actually_imported() -> None:
    """scipy, pandas and scikit-learn were declared and never imported: 227 MB
    of nothing.

    The gate's statistics are hand-implemented on purpose, so the maths is
    visible and unit-tested against published values rather than delegated to
    a library. Carrying the library anyway was pure weight.
    """
    pyproject = (REPO_ROOT / "backend" / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    dependencies = pyproject.split("dependencies = [")[1].split("]")[0]

    for unused in ("scipy", "scikit-learn", "pandas"):
        assert unused not in dependencies, (
            f"{unused} is declared; import it or drop it"
        )


def test_render_blueprint_pins_no_region() -> None:
    """Render's blueprint spec on `region`: "You can't modify this value after
    creation."

    Adding it to services that already existed made every blueprint sync fail
    -- and because the sync failed, the image fix that actually mattered could
    never deploy. A one-line optimisation blocked the repair of the thing it
    was optimising.
    """
    import yaml

    blueprint = yaml.safe_load(
        (REPO_ROOT / "render.yaml").read_text(encoding="utf-8")
    )

    for service in blueprint["services"]:
        assert "region" not in service, (
            f"{service['name']} pins a region; that field is immutable after "
            f"creation and will fail the sync on an existing service"
        )


def test_estate_completeness_is_not_judged_by_one_table() -> None:
    """Using principals as a proxy for "the estate is seeded" held until a
    migration added a table. The proxy then reported complete while the new
    table stayed empty, and the control depending on it gated for no evidence
    on a deployment that looked perfectly healthy."""
    source = (REPO_ROOT / "backend" / "app" / "seed" / "meridian.py").read_text(
        encoding="utf-8"
    )

    assert "_ESTATE_TABLES" in source
    assert "AssetRecord," in source.split("_ESTATE_TABLES")[1][:400]
