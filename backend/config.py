from os import getenv


class Config:
    GOOGLE_VALIDATION_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"

    # API security
    # --------
    SECRET_KEY = getenv("SECRET_KEY")
    MINUTES_PER_SESSION = int(getenv("MINUTES_PER_SESSION"))  # how long, in minutes, should a user session be?

    # Database
    # --------
    db_user = getenv("DB_USER")
    db_password = getenv("DB_PASSWORD")
    db_host = getenv("DB_HOST")
    db_port = getenv("DB_PORT")
    db_name = getenv("DB_NAME")
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
    SQLALCHEMY_TRACK_MODIFICATIONS = getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
    SQLALCHEMY_ECHO = bool(getenv("SQLALCHEMY_ECHO"))

    # App configurations
    # ------------------
    DEBUG_MODE = bool(getenv("DEBUG_MODE") == "True")  # Run the flask app in debug mode? (useful for development)
