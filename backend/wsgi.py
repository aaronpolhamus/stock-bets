from backend.app_factory import create_app

from config import Config

app = create_app()


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=Config.DEBUG_MODE, ssl_context=("cert.pem", "key.pem"))
