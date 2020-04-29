from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager

from database.db import db
from api import routes as routes


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    lm = LoginManager(app)
    lm.init_app(app)

    with app.app_context():
        app.register_blueprint(routes.routes)
        # It's annoying that flask works this way. migrate and models both become part of the application context here
        migrate = Migrate(app, db, directory="/home/backend/database/migrations")
        db.create_all()
        return app
