import pytest

from app.factory import create_app
from app.models import db


@pytest.fixture()
def app():
    application = create_app({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def api_headers():
    from app.settings import settings
    return {'X-API-KEY': settings.api_key}
