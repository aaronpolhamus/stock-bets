"""OAuth setup based mainly on this tutorial: https://realpython.com/flask-google-login/
Next steps:
- Separate out the HTML/CSS from the Python code for easier management:
    - You could use templates.
    - You could also load static files (like JS and CSS) from elsewhere.
- Use a real SSL certificate and get rid of that pesky warning
"""

import json
import os

from flask import Flask, redirect, request, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_restful import Resource, Api
from oauthlib.oauth2 import WebApplicationClient
import requests

from app.user import User
from config import GOOGLE_DISCOVERY_URL, BaseConfig


def get_google_provider_cfg():
    try:
        return requests.get(GOOGLE_DISCOVERY_URL).json()
    except requests.ConnectionError as e:
        raise SystemExit(e)


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
client = WebApplicationClient(BaseConfig.GOOGLE_CLIENT_ID)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.name, current_user.email, current_user.profile_pic
            )
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'


@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
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
        auth=(BaseConfig.GOOGLE_CLIENT_ID, BaseConfig.GOOGLE_CLIENT_SECRET),
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
    user = User(
        name=user_name, email=user_email, username=None, profile_pic=picture
    )

    # Doesn't exist? Add it to the database.
    if not User.get(user_email):
        User.create(user_name, user_email, None, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


class HelloWorld(Resource):
    """a silly endpoint that I have up for now as a sanity check/ example of a different API pattern. Delete later
    """
    def get(self):
        return {"hello": "world"}


api = Api(app)
api.add_resource(HelloWorld, "/hello_world")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, ssl_context="adhoc")
