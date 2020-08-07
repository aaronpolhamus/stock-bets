import hashlib
import time
from datetime import datetime as dt, timedelta
from io import BytesIO
from random import randint, seed

import jwt
import requests
from PIL import Image, ImageDraw, ImageFont
from backend.database.db import engine
from backend.database.helpers import add_row, query_to_dict
from backend.logic.base import standardize_email
from backend.logic.friends import invite_friend, get_requester_ids_from_email
from config import Config
from database.helpers import aws_client
from requests import RequestException

ADMIN_USERS = ["aaron@stockbets.io", "miguel@ruidovisual.com", "charly@captec.io", "jsanchezcastillejos@gmail.com"]
DUMMY_AVATAR = 'https://www.pngfind.com/pngs/m/676-6764065_default-profile-picture-transparent-hd-png-download.png'
AVATAR_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


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
    key = upload_image_from_url_to_s3(profile_pic, resource_uuid)
    profile_pic = f"{Config.AWS_PUBLIC_ENDPOINT}/{Config.AWS_PUBLIC_BUCKET_NAME}/{key}"
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


def register_user(name: str, email: str, profile_pic: str, current_time: float, provider: str, resource_uuid: str,
                  password: str = None):
    db_entry = query_to_dict("SELECT * FROM users WHERE resource_uuid = %s", resource_uuid)
    if not db_entry:
        user_id = setup_new_user(name, email, profile_pic, current_time, provider, resource_uuid, password)
    else:
        user_id = db_entry["id"]

    # for both classes of user, check if there are any outstanding game invites to create invitations for
    external_game_invites = get_pending_external_game_invites(email)
    with engine.connect() as conn:
        for entry in external_game_invites:
            # is this user already invited to a game?
            result = conn.execute("SELECT * FROM game_invites WHERE game_id = %s AND user_id = %s", entry["game_id"],
                                  user_id).fetchone()
            if not result:
                add_row("game_invites", game_id=entry["game_id"], user_id=user_id, status="invited",
                        timestamp=time.time())


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
    return key


def upload_image_from_url_to_s3(url: str, resource_uuid: str) -> str:
    try:
        data = requests.get(url, stream=True)
    except RequestException:
        data = requests.get(DUMMY_AVATAR, stream=True)
    return send_pic_to_s3(data.content, resource_uuid)


def make_profile_pic_on_s3(email: str) -> str:
    pic = Avatar.generate(128, email, "png")
    return send_pic_to_s3(pic, email)


class Avatar:
    # https://github.com/maethor/avatar-generator/blob/master/avatar_generator/__init__.py
    FONT_COLOR = (255, 255, 255)
    MIN_RENDER_SIZE = 512
    _font = AVATAR_FONT

    @classmethod
    def generate(cls, size: int, string: str, filetype: str = 'png'):
        """
            Generates a squared avatar with random background color.
            :param size: size of the avatar, in pixels
            :param string: string to be used to print text and seed the random
            :param filetype: the file format of the image (i.e. JPEG, PNG)
        """
        render_size = max(size, Avatar.MIN_RENDER_SIZE)
        image = Image.new('RGB', (render_size, render_size),
                          cls._background_color(string))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(cls._font, 18)
        text = cls._text(string)
        draw.text(cls._text_position(render_size, text, font),
                  text,
                  fill=cls.FONT_COLOR)
        stream = BytesIO()
        image = image.resize((size, size), Image.ANTIALIAS)
        image.save(stream, format=filetype, optimize=True)
        return stream.getvalue()

    @staticmethod
    def _background_color(s):
        """
            Generate a random background color.
            Brighter colors are dropped, because the text is white.
            :param s: Seed used by the random generator
            (same seed will produce the same color).
        """
        seed(s)
        r = v = b = 255
        while r + v + b > 255 * 2:
            r = randint(0, 255)
            v = randint(0, 255)
            b = randint(0, 255)
        return r, v, b

    @staticmethod
    def _text(string):
        """
            Returns the text to draw.
        """
        if len(string) == 0:
            return "#"
        else:
            return string[0].upper()

    @staticmethod
    def _text_position(size, text, font):
        """
            Returns the left-top point where the text should be positioned.
        """
        width, height = font.getsize(text)
        left = (size - width) / 2.0
        # I just don't know why 5.5, but it seems to be the good ratio
        top = (size - height) / 5.5
        return left, top
