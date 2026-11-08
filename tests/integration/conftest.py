import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.config import settings


PSQL = Path(r"C:\Program Files\PostgreSQL\17\bin\psql.exe")


def _psql(url, database: str, *, command: str | None = None, sql: str | None = None):
    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    args = [
        str(PSQL),
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-h",
        url.host or "127.0.0.1",
        "-p",
        str(url.port or 5432),
        "-U",
        url.username or "postgres",
        "-d",
        database,
    ]
    if command is not None:
        args.extend(["-c", command])

    return subprocess.run(
        args,
        input=sql,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.fixture(scope="session")
def test_database_url():
    if not PSQL.exists():
        pytest.skip("PostgreSQL psql.exe is not installed")

    source_url = make_url(settings.DATABASE_URL)
    database_name = f"llp_test_{uuid.uuid4().hex}"
    admin_database = "postgres"

    try:
        _psql(source_url, admin_database, command=f'CREATE DATABASE "{database_name}"')
    except subprocess.CalledProcessError as error:
        pytest.skip(f"PostgreSQL test database is unavailable: {error.stderr.strip()}")

    test_url = source_url.set(database=database_name)
    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        _psql(test_url, database_name, sql=migration.stdout)
        yield test_url.render_as_string(hide_password=False)
    finally:
        _psql(
            source_url,
            admin_database,
            command=f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)',
        )


@pytest_asyncio.fixture
async def db_session(test_database_url):
    engine = create_async_engine(test_database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.rollback()

    await engine.dispose()
