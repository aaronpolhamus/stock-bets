from os import getenv


class Config:
    GOOGLE_VALIDATION_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    FACEBOOK_VALIDATION_URL = "https://graph.facebook.com/me"

    # Game settings:
    # --------------
    GAME_STATUS_UPDATE_RATE = 5  # The n-minute interval on which to refresh all active game statuses

    # API security
    # --------
    SECRET_KEY = getenv("SECRET_KEY")
    MINUTES_PER_SESSION = int(getenv("MINUTES_PER_SESSION"))  # how long, in minutes, should a user session be?
    JWT_ENCODE_ALGORITHM = "HS256"

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
    MIGRATIONS_DIRECTORY = "/home/backend/database/migrations"

    # App configurations
    # ------------------
    DEBUG_MODE = bool(getenv("DEBUG_MODE") == "True")  # Run the flask app in debug mode? (useful for development)

    # Testing
    # -------
    TEST_CASE_EMAIL = getenv("TEST_CASE_EMAIL")
    TEST_CASE_UUID = getenv("TEST_CASE_UUID")

    # Distributed processing
    # ----------------------
    REDIS_HOST = getenv('REDIS_HOST')
    RABBITMQ_USER = getenv("RABBITMQ_USER")
    RABBITMQ_PASS = getenv("RABBITMQ_PASS")
    RABBITMQ_HOST = getenv("RABBITMQ_HOST")
    CELERY_BROKER_URL = f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:5672'
    CELERY_RESULTS_BACKEND = f"redis://{getenv('REDIS_HOST')}"

    # Data harvesting
    # ---------------
    IEX_API_PRODUCTION = bool(getenv("IEX_API_PRODUCTION") == "True")
    IEX_API_SECRET_PROD = getenv("IEX_API_SECRET_PROD")
    IEX_API_SECRET_SANDBOX = getenv("IEX_API_SECRET_SANDBOX")
