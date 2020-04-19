from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager

from database.db import db
from auth.user import User

login_manager = LoginManager()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

    with app.app_context():
        from webapp.auth import routes as auth_routes
        app.register_blueprint(auth_routes.auth_bp)
        migrate = Migrate(app, db, directory="webapp/database/migrations")
        from database import models
        db.create_all()
        return app
