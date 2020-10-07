import time
from typing import List

import pandas as pd
from backend.config import Config
from backend.database.db import engine
from backend.database.helpers import add_row
from backend.logic.visuals import get_user_information
from backend.logic.base import (
    standardize_email,
    get_user_ids_from_passed_emails,
    get_user_ids
)
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# Exceptions
# ----------
class InvalidEmailError(Exception):

    def __str__(self):
        return "This appears to be an invalid email, or the sendgrid integration is broken"


def get_user_details_from_ids(user_id_list: List[int], label: str = None):
    """There are a couple different cases where we want details about a user given their id. The label helps us to "tag"
    results in the case where we want a way to differentiate different groups in the same array, e.g. suggest_friends
    for the suggest_friend_invites, which details about who you've invited and who's invited you.
    """
    if not user_id_list:
        return []

    sql = f"""
        SELECT id, username, profile_pic, name
        FROM users
        WHERE id IN ({','.join(['%s'] * len(user_id_list))})
    """
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=user_id_list)
    if label is not None:
        df["label"] = label
    return df.to_dict(orient="records")


def get_friend_ids(user_id):
    """Given a user ID, get the IDs of each of this user's friends"""
    with engine.connect() as conn:
        invited_friends = conn.execute("""
            SELECT requester_id
            FROM friends 
            WHERE invited_id = %s
            AND status = 'accepted';
        """, user_id).fetchall()

        requested_friends = conn.execute("""
            SELECT invited_id
            FROM friends
            WHERE requester_id = %s
            AND status = 'accepted';
        """, user_id).fetchall()

    return [x[0] for x in invited_friends + requested_friends]


def get_friend_invite_ids(user_id):
    """Given a user's id, get the list of people who've sent her friend invites"""
    with engine.connect() as conn:
        invited_friends = conn.execute("""
            SELECT f.requester_id, status
            FROM friends f
            INNER JOIN
            (SELECT requester_id, invited_id, max(id) as max_id
              FROM friends
              GROUP BY requester_id, invited_id) grouped_friends
            ON
              grouped_friends.max_id = f.id
            WHERE 
              f.invited_id = %s AND
              status = 'invited';
        """, user_id).fetchall()
    return [x[0] for x in invited_friends]


def get_invited_friend_ids(user_id: int):
    """Given a user's id, get the list of people to whom she's sent friend invites"""
    with engine.connect() as conn:
        invited_friends = conn.execute("""
            SELECT f.invited_id, status
            FROM friends f
            INNER JOIN
            (SELECT requester_id, invited_id, max(id) as max_id
              FROM friends
              GROUP BY requester_id, invited_id) grouped_friends
            ON
              grouped_friends.max_id = f.id
            WHERE 
              f.requester_id = %s AND
              status = 'invited';
        """, user_id).fetchall()
    return [x[0] for x in invited_friends]


def get_suggested_friend_ids(text: str, excluded_ids: List[int]):
    """The excluded_ids list should be a list of user ids that we _don't_ want appearing as suggestions. Naturally, the
    user's own ID should be a part of that list
    """
    to_match = f"{text}%"
    with engine.connect() as conn:
        suggest_query = """
            SELECT id FROM users
            WHERE username LIKE %s
            LIMIT 10;
        """
        result = conn.execute(suggest_query, to_match).fetchall()
    return [x[0] for x in result if x[0] not in excluded_ids]


def get_friend_rejections(user_id):
    with engine.connect() as conn:
        sql = """
            SELECT DISTINCT invited_id
            FROM friends WHERE
            requester_id = %s AND
            status = 'declined'
        """
        result = conn.execute(sql, user_id).fetchall()
    return [x[0] for x in result]


def suggest_friends(user_id: int, text: str):
    """The suggest friends dropdown lists includes information about who you've invited and who's invited you. This
    """
    friend_invite_ids = get_friend_invite_ids(user_id)
    invited_you_details = get_user_details_from_ids(friend_invite_ids, "invited_you")

    invited_friend_ids = get_invited_friend_ids(user_id)
    you_invited_details = get_user_details_from_ids(invited_friend_ids, "you_invited")

    current_friend_ids = get_friend_ids(user_id)
    rejected_request_ids = get_friend_rejections(user_id)
    excluded_ids = current_friend_ids + friend_invite_ids + invited_friend_ids + rejected_request_ids

    suggested_friend_ids = get_suggested_friend_ids(text, excluded_ids)
    suggest_friend_details = get_user_details_from_ids(suggested_friend_ids, "suggested")
    return invited_you_details + you_invited_details + suggest_friend_details


def get_friend_invites_list(user_id: int):
    invite_ids = get_friend_invite_ids(user_id)
    if not invite_ids:
        return []
    details = get_user_details_from_ids(invite_ids)
    return [x["username"] for x in details]


def get_requester_ids_from_email(email):
    with engine.connect() as conn:
        friend_ids = conn.execute("SELECT requester_id FROM external_invites WHERE invited_email = %s",
                                  email).fetchall()
    if friend_ids:
        return list(set([x[0] for x in friend_ids]))
    return []


def get_friend_details(user_id: int) -> dict:
    friend_ids = get_friend_ids(user_id)
    invited_friend_ids = get_invited_friend_ids(user_id)
    return dict(
        friends=get_user_details_from_ids(friend_ids),
        invited_friends=get_user_details_from_ids(invited_friend_ids)
    )


def respond_to_friend_invite(requester_username, invited_id, decision):
    requester_id = get_user_ids([requester_username])[0]
    add_row("friends", requester_id=requester_id, invited_id=invited_id, status=decision, timestamp=time.time())


# ------- #
# Friends #
# ------- #


def invite_friend(requester_id, invited_id):
    """Since the user is sending the request, we'll know their user ID via their web token. We don't post this
    information to the frontend for other users, though, so we'll look up their ID based on username
    """
    add_row("friends", requester_id=requester_id, invited_id=invited_id, status="invited", timestamp=time.time())


def check_external_game_invite(requester_id: int, invited_user_email: str, game_id: int = None):
    with engine.connect() as conn:
        res = conn.execute("""
            SELECT id FROM external_invites 
            WHERE requester_id = %s AND LOWER(REPLACE(invited_email, '.', '')) = %s AND game_id = %s AND type='game'""",
                           requester_id, standardize_email(invited_user_email), game_id).fetchone()
    if res:
        return True
    return False


def check_platform_invite_exists(requester_id: int, invited_user_email: str):
    with engine.connect() as conn:
        res = conn.execute("""
            SELECT id FROM external_invites 
            WHERE requester_id = %s AND LOWER(REPLACE(invited_email, '.', '')) = %s AND type = 'platform';""",
                           requester_id, standardize_email(invited_user_email)).fetchone()
    if res:
        return True
    return False


def add_to_game_invites_if_registered(game_id, invited_user_email):
    # check and see if the externally invited user is registered in the DB. if they are, add them to the internal
    # invite table as well
    user_id = get_user_ids_from_passed_emails([invited_user_email])
    if user_id:
        add_row("game_invites", game_id=game_id, user_id=user_id[0], status="invited", timestamp=time.time())


def send_invite_email(requester_id, email, email_type="platform"):
    user_information = get_user_information(requester_id)
    name = user_information['name']
    if email_type == "platform":
        message = Mail(
            from_email=Config.EMAIL_SENDER,
            to_emails=email,
            subject=f"Your friend {name} invites you to join Stockbets!",
            html_content=f"""<strong>Hey there your friend {name} has invited you to 
                             join stockbets.io,  You can learn about the mechanics of
                             investing / test different strategies in single player mode, or compete against your
                             friends.  </strong>""")
    if email_type == "game":
        message = Mail(
            from_email=Config.EMAIL_SENDER,
            to_emails=email,
            subject=f"Your friend {name} has invited you to a competition on stockbets.io",
            html_content=f"""<strong>Hey there your friend {name} has invited you to 
                             a multiplayer competition on stockbets.io. Compete to build the the
                             most winning portfolio over the competition either for fun or real stakes. </strong>""")

    sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
    response = sg.send(message)
    if response.status_code == 202:
        return True


def email_platform_invitation(requester_id: int, invited_user_email: str):
    """Sends an email to your friend to joins stockbets, adds a friend request to the username once the person has
    joined
    """
    if check_platform_invite_exists(requester_id, invited_user_email):
        return
    email_response = send_invite_email(requester_id, invited_user_email)
    if not email_response:
        raise InvalidEmailError

    add_row('external_invites', requester_id=requester_id, invited_email=invited_user_email, status="invited",
            timestamp=time.time(), game_id=None, type='platform')


def email_game_invitation(requester_id: int, invited_user_email: str, game_id: int):
    if check_external_game_invite(requester_id, invited_user_email, game_id):
        return
    email_response = send_invite_email(requester_id, invited_user_email, "game")
    if not email_response:
        raise InvalidEmailError

    add_row('external_invites', requester_id=requester_id, invited_email=invited_user_email, status="invited",
            timestamp=time.time(), game_id=game_id, type='game')

    # if a user isn't on the platform and doesn't have an invite, do there here as well
    platform_id = get_user_ids_from_passed_emails([invited_user_email])
    if not check_platform_invite_exists(requester_id, invited_user_email) and not platform_id:
        add_row('external_invites', requester_id=requester_id, invited_email=invited_user_email, status="invited",
                timestamp=time.time(), game_id=None, type='platform')
