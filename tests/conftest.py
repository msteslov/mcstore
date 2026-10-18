from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from mcstore.api import app
from mcstore.database import Base, build_engine, get_session


@pytest.fixture
def session(tmp_path) -> Iterator[Session]:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    test_engine = build_engine(database_url)
    Base.metadata.create_all(test_engine)
    test_session_factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with test_session_factory() as test_session:
        yield test_session
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def client(session: Session) -> Iterator[TestClient]:
    def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
