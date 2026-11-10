import subprocess
import sys

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import CheckConstraint, UniqueConstraint

import backend.models  # noqa: F401
from backend.database.base import Base


pytestmark = pytest.mark.integration


EXPECTED_TABLES = {
    "review_item",
    "practice_session",
    "practice_session_item",
    "user_daily_goal",
    "ai_usage",
}


def _offline_upgrade_sql() -> str:
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_product_migration_is_the_single_head_and_creates_all_tables():
    """Catches an unlinked revision or any missing product-completion table."""
    script = ScriptDirectory.from_config(Config("alembic.ini"))
    sql = _offline_upgrade_sql()

    assert script.get_heads() == ["product_completion"]
    assert all(f"CREATE TABLE {name}" in sql for name in EXPECTED_TABLES)


@pytest.mark.parametrize(
    ("table_name", "constraint_name"),
    [
        ("review_item", "uq_review_item_user_exercise"),
        ("review_item", "ck_review_item_box"),
        ("review_item", "ck_review_item_attempts"),
        ("practice_session", "ck_practice_session_score"),
        ("practice_session_item", "uq_practice_item_session_position"),
        ("practice_session_item", "uq_practice_item_session_exercise"),
        ("user_daily_goal", "uq_user_daily_goal_user"),
        ("user_daily_goal", "ck_user_daily_goal_target"),
    ],
)
def test_product_constraints_exist_in_metadata_and_migration(
    table_name: str, constraint_name: str
):
    """Catches migration/model drift for invariants consumed by later services."""
    table = Base.metadata.tables[table_name]
    named_constraints = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, (CheckConstraint, UniqueConstraint))
    }

    assert constraint_name in named_constraints
    assert f"CONSTRAINT {constraint_name}" in _offline_upgrade_sql()


def test_product_models_use_aware_instants_and_required_indexes():
    """Catches timezone-naive state and review/AI queries degrading to scans."""
    for table_name in EXPECTED_TABLES:
        table = Base.metadata.tables[table_name]
        for column in table.columns:
            if column.name.endswith("_at"):
                assert column.type.timezone is True, f"{table_name}.{column.name}"

    review_indexes = {index.name for index in Base.metadata.tables["review_item"].indexes}
    usage_indexes = {index.name for index in Base.metadata.tables["ai_usage"].indexes}
    assert "ix_review_item_user_due" in review_indexes
    assert "ix_ai_usage_user_created" in usage_indexes
