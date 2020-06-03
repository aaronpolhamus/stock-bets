from typing import List

from sqlalchemy import select

from backend.database.helpers import retrieve_meta_data
from backend.database.db import db_session


def get_friend_ids(user_id):
    """Given a user ID, get the IDs of each of this user's friends
    """
    with db_session.connection() as conn:
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

        db_session.remove()
    return [x[0] for x in invited_friends + requested_friends]


def get_friend_invite_ids(user_id):
    with db_session.connection() as conn:
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
        db_session.remove()
    return [x[0] for x in invited_friends]


def get_names_from_ids(user_id_list: List[int]):
    users = retrieve_meta_data(db_session.connection()).tables["users"]
    result = db_session.execute(select([users.c.username], users.c.id.in_(user_id_list))).fetchall()
    return [x[0] for x in result]
