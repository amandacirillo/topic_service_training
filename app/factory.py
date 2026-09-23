"""Flask application factory."""
import os
from typing import Optional

from flask import Flask

TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')


def create_app(config_overrides: Optional[dict] = None) -> Flask:
    from app.models import db
    from app.settings import settings

    app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = settings.flask_debug
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    from app.admin import admin_bp
    from app.api import api_bp
    from app.health import health_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app
