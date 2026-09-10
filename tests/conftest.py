import pytest

from app import create_app
from app.db import init_db


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "DATABASE": str(tmp_path / "test.db"),
        }
    )

    with app.app_context():
        init_db()

    return app


@pytest.fixture
def client(app):
    return app.test_client()