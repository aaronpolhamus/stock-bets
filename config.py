from os import getenv


class Config:
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # Database configs
    # ----------------
    db_user = getenv("DB_USER")
    db_password = getenv("DB_PASSWORD")
    db_host = getenv("DB_HOST")
    db_port = getenv("DB_PORT")
    db_name = getenv("DB_NAME")
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8"
    SQLALCHEMY_TRACK_MODIFICATIONS = getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
    SQLALCHEMY_ECHO = bool(getenv("SQLALCHEMY_ECHO"))

    # OAuth credentials
    # -----------------
    GOOGLE_CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")
