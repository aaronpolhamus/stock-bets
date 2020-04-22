from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager

from database.db import db
from backend.api.auth.user import User
from backend.api.auth import routes as auth_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    lm = LoginManager(app)
    lm.init_app(app)

    @lm.user_loader
    def load_user(user_id):
        user = User.get(user_id)
        return user

    with app.app_context():
        app.register_blueprint(auth_routes.auth_bp)
        # It's annoying that flask works this way. migrate and models both become part of the application context here
        migrate = Migrate(app, db, directory="/home/backend/database/migrations")
        from backend.database import models
        db.create_all()
        return app
