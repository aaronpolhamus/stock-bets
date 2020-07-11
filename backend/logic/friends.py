import time
from typing import List

import pandas as pd

from backend.database.helpers import add_row
from backend.database.db import engine
from backend.logic.base import get_user_id


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


def get_invited_friend_ids(user_id):
    """Given a user's id, get the list of people to whom he's sent friend invites"""
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


def suggest_friends(user_id, text):
    """The suggest friends dropdown lists includes information about who you've invited and who's invited you. This
    should go elswhere at some point
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


def get_friend_details(user_id: int):
    friend_ids = get_friend_ids(user_id)
    return get_user_details_from_ids(friend_ids)


def respond_to_friend_invite(requester_username, invited_id, decision):
    requester_id = get_user_id(requester_username)
    add_row("friends", requester_id=requester_id, invited_id=invited_id, status=decision, timestamp=time.time())

# ------- #
# Friends #
# ------- #


def invite_friend(requester_id, invited_username):
    """Since the user is sending the request, we'll know their user ID via their web token. We don't post this
    information to the frontend for other users, though, so we'll look up their ID based on username
    """
    invited_id = get_user_id(invited_username)
    add_row("friends", requester_id=requester_id, invited_id=invited_id, status="invited", timestamp=time.time())
