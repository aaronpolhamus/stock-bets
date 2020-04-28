from flask import Blueprint, request
from flask_httpauth import HTTPTokenAuth

auth = HTTPTokenAuth()
routes = Blueprint("routes", __name__)


@routes.route("/", methods=["GET"])
@auth.login_required
def index():
    """A user with a valid token will get a response with basic profile information to be displayed on their landing
    page. Otherwise the API will return a 401, and the front-end will redirect to the Google Login page"""
    data = request.get_json()


@routes.route("/register", methods=["POST"])
def register_user():
    """Following a successful login, this allows us to create a new users. If the user already exists in the DB send
    back a SetCookie to allow for seamless interaction with the API
    """
    data = request.get_json()
    return {"message": "registered successfully"}, 201

