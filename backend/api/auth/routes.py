import json

from flask import redirect, request, url_for, Blueprint
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from config import Config
from backend.api.auth.user import User

client = WebApplicationClient(Config.GOOGLE_CLIENT_ID)
auth_bp = Blueprint("auth_bp", __name__)


def get_google_provider_cfg():
    try:
        return requests.get(Config.GOOGLE_DISCOVERY_URL).json()
    except requests.ConnectionError as e:
        raise SystemExit(e)


@auth_bp.route("/")
def index():
    import flask
    flask.current_app.logger.debug(f"*** DEBUG \n {dir(current_user)}***\n")
    if current_user.is_authenticated:
        return {"name": current_user.name, "email": current_user.email, "profile_pic": current_user.profile_pic}

    # if current_user.is_authenticated:
    #     return (
    #         f"<p>Hello, {current_user.name}! You're logged in! Email: {current_user.email}</p>"
    #         "<div><p>Google Profile Picture:</p>"
    #         f"<img src='{current_user.profile_pic}' alt='Google profile pic'></img></div>"
    #         "<a class='button' href='/logout'>Logout</a>"
    #     )
    # else:
    #     return '<a class="button" href="/login">Google Login</a>'


@auth_bp.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@auth_bp.route("/login/callback")
def callback():
    code = request.args.get("code")

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(Config.GOOGLE_CLIENT_ID, Config.GOOGLE_CLIENT_SECRET),
    )

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        user_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        user_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Username blank for now. Build this feature later
    user = User(name=user_name, email=user_email, username=None, profile_pic=picture)

    if not User.get(user_email):
        User.create(user_name, user_email, None, picture)

    login_user(user)
    return redirect(url_for("auth_bp.index"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth_bp.index"))
