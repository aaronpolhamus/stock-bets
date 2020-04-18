from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)

    with app.app_context():
        from webapp.auth import auth_routes
        app.register_blueprint(auth_routes.auth_bp)
        # from webapp import models
        migrate = Migrate(app, db, directory="webapp/migrations")
        db.create_all()
        return app
