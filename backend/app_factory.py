from flask import Flask
from flask_migrate import Migrate

from database.db import db
from api import routes as routes


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    migrate = Migrate()

    with app.app_context():
        app.register_blueprint(routes.routes)
        # It's annoying that flask works this way. migrate and models both become part of the application context here
        from backend.database import models
        migrate.init_app(app, db, directory="/home/backend/database/migrations")
        db.drop_all()
        return app
