from flask import Flask
from flask_migrate import Migrate

from backend.database.db import db
from backend.api import routes as routes
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.register_blueprint(routes.routes)
    db.init_app(app)
    migrate = Migrate(app, db, directory=Config.MIGRATIONS_DIRECTORY)
    migrate.init_app(app, db)
    return app

from backend.database import models
