import re
import subprocess
import sys

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import DateTime

import backend.models  # noqa: F401
from backend.database.base import Base


pytestmark = pytest.mark.integration


def _offline_upgrade_sql() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_migration_history_has_one_head():
    script = ScriptDirectory.from_config(Config("alembic.ini"))

    assert script.get_heads() == ["core_baseline"]


def test_baseline_creates_each_table_once():
    sql = _offline_upgrade_sql()
    created_tables = re.findall(
        r'CREATE TABLE\s+(?:"([^"]+)"|([a-zA-Z_][a-zA-Z0-9_]*))',
        sql,
        flags=re.IGNORECASE,
    )
    names = [quoted or plain for quoted, plain in created_tables]
    duplicates = sorted({name for name in names if names.count(name) > 1})

    assert duplicates == []


def test_baseline_uses_timezone_aware_instants():
    sql = _offline_upgrade_sql()

    assert "TIMESTAMP WITHOUT TIME ZONE" not in sql
    assert "TIMESTAMP WITH TIME ZONE" in sql


def test_models_mark_every_instant_as_timezone_aware():
    timestamp_columns = [
        column
        for table in Base.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, DateTime)
    ]

    assert timestamp_columns
    assert [
        f"{column.table.name}.{column.name}"
        for column in timestamp_columns
        if not column.type.timezone
    ] == []


def test_leaderboard_model_matches_unique_user_index():
    leaderboard = Base.metadata.tables["leaderboard"]

    assert any(
        index.name == "ix_leaderboard_user_id"
        and index.unique
        and [column.name for column in index.columns] == ["user_id"]
        for index in leaderboard.indexes
    )


@pytest.mark.parametrize(
    "constraint_name",
    [
        "uq_hearts_user",
        "uq_streak_user",
        "uq_user_language_user_language",
        "uq_user_exercise_progress_user_exercise",
        "uq_user_progress_user_lesson",
        "uq_exercise_submission_user_key",
    ],
)
def test_baseline_contains_core_unique_constraints(constraint_name: str):
    assert f"CONSTRAINT {constraint_name} UNIQUE" in _offline_upgrade_sql()
