import requests
from backend.database.db import db
from flask import Blueprint, request, jsonify, abort
from flask_httpauth import HTTPTokenAuth
import secrets

auth = HTTPTokenAuth()
routes = Blueprint("routes", __name__)

GOOGLE_VALIDATION_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"


@routes.route("/", methods=["GET"])
@auth.login_required
def index():
    """A user with a valid token will get a response with basic profile information to be displayed on their landing
    page. Otherwise the API will return a 401, and the front-end will redirect to the Google Login page"""
    data = request.get_json()
    # auth.login_required has already validated the user

    # send back basic information for the user's landing page

    pass


@routes.route("/register", methods=["POST"])
def register_user():
    """Following a successful login, this allows us to create a new users. If the user already exists in the DB send
    back a SetCookie to allow for seamless interaction with the API. token_id comes from response.tokenId where the
    response is the returned value from the React-Google-Login component
    """
    token_id = request.json["tokenId"]
    # validate the user with Google
    response = requests.post(GOOGLE_VALIDATION_URL, data={"id_token": token_id})
    if response.status_code == 200:
        decoded_json = response.json()
        user_email = decoded_json["email"]
        # if the user is valid, check to see if we already have them in our DB
        user = db.engine.execute("SELECT * FROM users WHERE email = %s", user_email).fetchone()
        if not user:
            # if not, make an entry
            db.engine.execute("INSERT INTO users (name, email, username, profile_pic) VALUES (%s, %s, %s, %s)",
                              (decoded_json["given_name"], user_email, None, decoded_json["picture"]))

        # refresh the user's session token and return to the client for local storage and http auth
        session_token = secrets.token_hex()
        db.engine.execute("UPDATE users SET session_token = %s WHERE email = %s;", (session_token, user_email))
        return jsonify({"session_token": session_token})

    abort(response.status_code, "tokenId from Google OAuth failed verification")
