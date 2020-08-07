import hashlib
import time
from datetime import datetime as dt, timedelta
from io import BytesIO
from random import randint, seed
from requests import RequestException

import jwt
import requests
from backend.database.db import engine
from backend.database.helpers import add_row, query_to_dict
from backend.logic.base import standardize_email
from backend.logic.friends import invite_friend, get_requester_ids_from_email
from config import Config
from database.helpers import aws_client

ADMIN_USERS = ["aaron@stockbets.io", "miguel@ruidovisual.com", "charly@captec.io", "jsanchezcastillejos@gmail.com"]
AVATAR_TEXT_COLOR = "FFFEF2"
DEFAULT_AVATAR = 'https://www.pngfind.com/pngs/m/676-6764065_default-profile-picture-transparent-hd-png-download.png'


def check_against_invited_users(email):
    with engine.connect() as conn:
        count, = conn.execute("SELECT count(*) FROM external_invites WHERE invited_email = %s", email).fetchone()
    if count > 0:
        return True
    return False


def create_jwt(email, user_id, username, mins_per_session=Config.MINUTES_PER_SESSION, secret_key=Config.SECRET_KEY):
    payload = {"email": email, "user_id": user_id, "username": username,
               "exp": dt.utcnow() + timedelta(minutes=mins_per_session)}
    return jwt.encode(payload, secret_key, algorithm=Config.JWT_ENCODE_ALGORITHM).decode("utf-8")


def decode_token(req, element="user_id"):
    """Parse user information from the HTTP token that comes with each authenticated request from the frontend
    """
    decoded_session_token = jwt.decode(req.cookies["session_token"], Config.SECRET_KEY)
    return decoded_session_token[element]


def verify_google_oauth(token_id):
    return requests.post(Config.GOOGLE_VALIDATION_URL, data={"id_token": token_id})


def verify_facebook_oauth(access_token):
    return requests.post(Config.FACEBOOK_VALIDATION_URL, data={"access_token": access_token})


def update_profile_pic(user_id: id, new_profile_pic: str, old_profile_pic: str):
    if new_profile_pic != old_profile_pic:
        with engine.connect() as conn:
            conn.execute("UPDATE users SET profile_pic = %s WHERE id = %s;", new_profile_pic, user_id)


def setup_new_user(name: str, email: str, profile_pic: str, created_at: float, provider: str,
                   resource_uuid: str, password: str = None) -> int:
    user_id = add_row("users", name=name, email=email, username=None, profile_pic=profile_pic, created_at=created_at,
                      provider=provider, password=password, resource_uuid=resource_uuid)
    requester_friends_ids = get_requester_ids_from_email(email)
    for requester_id in requester_friends_ids:
        add_row("external_invites", requester_id=requester_id, invited_email=email, status="accepted",
                timestamp=time.time(), type="platform")
        invite_friend(requester_id, user_id)
    return user_id


def get_pending_external_game_invites(invited_email: str):
    """Returns external game invites whose most recent status is 'invited'
    """
    return query_to_dict("""
            SELECT *
            FROM external_invites ex
            INNER JOIN
                 (SELECT LOWER(REPLACE(invited_email, '.', '')) as formatted_email, MAX(id) as max_id
                   FROM external_invites
                   WHERE type = 'game'
                   GROUP BY requester_id, type, game_id, formatted_email) grouped_ex
            ON ex.id = grouped_ex.max_id
            WHERE LOWER(REPLACE(ex.invited_email, '.', '')) = %s AND ex.status = 'invited';    
""", standardize_email(invited_email))


def add_external_game_invites(email: str, user_id: int):
    # is this user already invited to a games?
    external_game_invites = get_pending_external_game_invites(email)
    for entry in external_game_invites:
        add_row("game_invites", game_id=entry["game_id"], user_id=user_id, status="invited", timestamp=time.time())


def make_session_token_from_uuid(resource_uuid):
    with engine.connect() as conn:
        user_id, email, username = conn.execute("SELECT id, email, username FROM users WHERE resource_uuid = %s",
                                                resource_uuid).fetchone()
    return create_jwt(email, user_id, username)


def register_username_with_token(user_id, user_email, candidate_username):
    with engine.connect() as conn:
        matches = conn.execute("SELECT id FROM users WHERE username = %s", candidate_username).fetchone()

    if matches is None:
        with engine.connect() as conn:
            conn.execute("UPDATE users SET username = %s WHERE id = %s;", (candidate_username, user_id))
        return create_jwt(user_email, user_id, candidate_username)

    return None


def send_pic_to_s3(pic: bytes, hash_string: str) -> str:
    s3 = aws_client()
    pic_hash = hashlib.sha224(bytes(hash_string, encoding='utf-8')).hexdigest()
    key = f"profile_pics/{pic_hash}"
    out_img = BytesIO(pic)
    out_img.seek(0)
    s3.put_object(Body=out_img, Bucket=Config.AWS_PUBLIC_BUCKET_NAME, Key=key, ACL="public-read")
    return f"{Config.AWS_PUBLIC_ENDPOINT}/{Config.AWS_PUBLIC_BUCKET_NAME}/{key}"


def upload_image_from_url_to_s3(url: str, resource_uuid: str) -> str:
    try:
        data = requests.get(url, stream=True)
    except RequestException:
        data = requests.get(DEFAULT_AVATAR, stream=True)
    return send_pic_to_s3(data.content, resource_uuid)


def make_avatar_url(email: str):
    """construct url for https://ui-avatars.com/"""
    seed(email)
    r = g = b = 255
    while r + g + b > 255 * 2:
        r = randint(0, 255)
        g = randint(0, 255)
        b = randint(0, 255)
    background = '%02x%02x%02x' % (r, g, b)
    return f"https://ui-avatars.com/api/?name={email[0].upper()}&background={background}&color={AVATAR_TEXT_COLOR}&size=128&font-size=0.7"
