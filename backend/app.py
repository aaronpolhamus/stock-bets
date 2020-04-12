from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

if __name__ == "__main__":
    from api import *
    app.run(host="0.0.0.0")
