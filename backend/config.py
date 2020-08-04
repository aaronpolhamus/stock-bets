from os import getenv


class Config:
    # Configs set by prod versus dev env
    # ----------------------------------
    ENV = getenv("ENV")
    if ENV == "dev":
        CORS_ORIGINS = "http://localhost:3000"

    if ENV == "prod":
        CORS_ORIGINS = "https://app.stockbets.io"

    # External dependencies:
    # ----------------------
    GOOGLE_VALIDATION_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
    FACEBOOK_VALIDATION_URL = "https://graph.facebook.com/me"
    SYMBOLS_TABLE_URL = "https://iextrading.com/trading/eligible-symbols/"
    YAHOO_FINANCE_URL = "https://finance.yahoo.com/"
    EMAIL_SENDER = getenv('EMAIL_SENDER')
    SENDGRID_API_KEY = getenv('SENDGRID_API_KEY')

    # Game settings:
    # --------------
    # The n-minute interval on which to refresh all active game statuses
    GAME_STATUS_UPDATE_RATE = getenv("GAME_STATUS_UPDATE_RATE")
    # The n-minute interval on which to process all open orders (careful, this costs $$$)
    OPEN_ORDER_PROCESS_RATE = getenv("OPEN_ORDER_PROCESS_RATE")

    # Security
    # --------
    SECRET_KEY = getenv("SECRET_KEY")
    MINUTES_PER_SESSION = int(getenv("MINUTES_PER_SESSION"))  # how long, in minutes, should a user session be?
    JWT_ENCODE_ALGORITHM = "HS256"
    CHECK_WHITE_LIST = bool(getenv("CHECK_WHITE_LIST") == "True")

    # Database
    # --------
    DB_USER = getenv("MYSQL_USER")
    DB_PASSWORD = getenv("MYSQL_ROOT_PASSWORD")
    DB_HOST = getenv("MYSQL_HOST")
    DB_PORT = getenv("MYSQL_PORT")
    DB_NAME = getenv("MYSQL_DATABASE")
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
    SQLALCHEMY_ECHO = bool(getenv("SQLALCHEMY_ECHO") == "True")
    MIGRATIONS_DIRECTORY = "/home/backend/database/migrations"

    # App configurations
    # ------------------
    DEBUG_MODE = bool(getenv("DEBUG_MODE") == "True")  # Run the flask app in debug mode? (useful for development)

    # Testing
    # -------
    TEST_CASE_NAME = getenv("TEST_CASE_NAME")
    TEST_CASE_EMAIL = getenv("TEST_CASE_EMAIL")
    TEST_CASE_UUID = getenv("TEST_CASE_UUID")

    # Distributed processing
    # ----------------------
    REDIS_HOST = getenv('REDIS_HOST')
    RABBITMQ_DEFAULT_USER = getenv("RABBITMQ_DEFAULT_USER")
    RABBITMQ_DEFAULT_PASS = getenv("RABBITMQ_DEFAULT_PASS")
    RABBITMQ_HOST = getenv("RABBITMQ_HOST")
    CELERY_BROKER_URL = f'amqp://{RABBITMQ_DEFAULT_USER}:{RABBITMQ_DEFAULT_PASS}@{RABBITMQ_HOST}:5672'
    CELERY_RESULTS_BACKEND = f"redis://{getenv('REDIS_HOST')}"

    # Data harvesting
    # ---------------
    IEX_API_PRODUCTION = bool(getenv("IEX_API_PRODUCTION") == "True")
    IEX_API_SECRET_PROD = getenv("IEX_API_SECRET_PROD")
    IEX_API_SECRET_SANDBOX = getenv("IEX_API_SECRET_SANDBOX")

    # S3 Credentials
    AWS_ACCESS_KEY_ID = getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = getenv("AWS_SECRET_ACCESS_KEY")
    AWS_ENDPOINT_URL = getenv('AWS_ENDPOINT_URL')
    AWS_PUBLIC_BUCKET_NAME = getenv("AWS_PUBLIC_BUCKET_NAME")
    AWS_PUBLIC_ENDPOINT = getenv("AWS_PUBLIC_ENDPOINT")
