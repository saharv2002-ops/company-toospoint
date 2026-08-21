"""Shared pytest fixtures.

Integration tests that need a real Postgres are gated behind the
`POSTGRES_TEST_URL` env var. Locally, run:

    docker compose -f infra/docker-compose.yml up -d db
    export POSTGRES_TEST_URL=postgresql+psycopg://churnscope:churnscope_dev@localhost:5432/churnscope
    pytest

In CI, the postgres service in .github/workflows sets POSTGRES_TEST_URL.

Tests that don't need a DB (Pydantic schema tests, health test) run
regardless.
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_db
from app.main import app
from app.models import Base

POSTGRES_TEST_URL = os.environ.get("POSTGRES_TEST_URL")
requires_postgres = pytest.mark.skipif(
    POSTGRES_TEST_URL is None,
    reason="POSTGRES_TEST_URL not set — run docker compose up db and export it",
)


@pytest.fixture(scope="session")
def engine():
    if POSTGRES_TEST_URL is None:
        pytest.skip("POSTGRES_TEST_URL not set")
    eng = create_engine(POSTGRES_TEST_URL, future=True)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db(engine):
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session: Session = TestingSession()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(text(f'TRUNCATE TABLE "{table.name}" CASCADE'))
        session.commit()
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(engine, db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
