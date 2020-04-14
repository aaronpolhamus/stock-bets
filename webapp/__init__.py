from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.Config')
    db.init_app(app)

    with app.app_context():
        from auth import auth_routes
        app.register_blueprint(auth_routes.auth_bp)
        migrate = Migrate(app, db)
        db.create_all()
        return app
