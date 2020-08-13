"""Not a drill. This logic for handles actual cash payments to/from  users. Treat with great care, and test thoroughly!
"""
import base64
import json
import time
from typing import List
import uuid as uuid_gen

import requests
from backend.config import Config
from backend.database.helpers import add_row
from backend.database.helpers import query_to_dict

STOCKBETS_COMMISION = 0.1
PERCENT_TO_USER = (1 - STOCKBETS_COMMISION)


# Exceptions
# ----------
class MissingProfiles(Exception):

    def __str__(self):
        return "The combination of user ids and payment provider provided wasn't able to match all users"


class SendPaymentError(Exception):

    def __str__(self):
        return "Request to send payment to user was unsuccessful"


def get_paypal_access_token(client_id=Config.PAYPAL_CLIENT_ID, secret=Config.PAYPAL_SECRET, base_url=Config.PAYPAL_URL):
    url = f"{base_url}/v1/oauth2/token"
    payload = 'grant_type=client_credentials'
    encoded_auth = base64.b64encode((client_id + ':' + secret).encode())
    headers = {
        'Authorization': f'Basic {encoded_auth.decode()}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.request("POST", url, headers=headers, data=payload)
    assert r.status_code == 200
    return r.json()["access_token"]


def check_payment_profile(user_id: int, processor: str, uuid: str, payer_email: str):
    """Check to see if a payment profile entry exists for a user. If not create profile. Return profile_id
    """
    profile_entry = query_to_dict("""
        SELECT * FROM payment_profiles 
        WHERE user_id = %s AND uuid = %s AND processor = %s AND payer_email = %s
        ORDER BY timestamp DESC LIMIT 1;""", user_id, uuid, processor, payer_email)
    if profile_entry:
        return profile_entry[0]["id"]
    return add_row("payment_profiles", user_id=user_id, processor=processor, uuid=uuid, payer_email=payer_email,
                   timestamp=time.time())


def get_payment_profile_uuids(user_ids: List[int], processor="paypal"):
    profile_entries = query_to_dict(f"""
        SELECT * FROM payment_profiles p
        INNER JOIN (
          SELECT user_id, MAX(id) AS max_id
          FROM payment_profiles
          WHERE user_id IN ({",".join(["%s"] * len(user_ids))}) AND processor = %s
          GROUP BY user_id) grouped_profiles
        ON p.id = grouped_profiles.max_id;""", user_ids + [processor])
    if len(profile_entries) != len(user_ids):
        raise MissingProfiles
    return profile_entries


def send_paypal_payment(uuids: List[int], amount: float, payment_type: str, email_content: str = None,
                        email_subject: str = None, note_content: str = None, currency: str = "USD",
                        base_url=Config.PAYPAL_URL, api_endpoint: str = "v1/payments/payouts",
                        sender_batch_id: str = None):
    if sender_batch_id is None:
        sender_batch_id = f"payout_{payment_type}_{time.time()}_{str(uuid_gen.uuid4())}"

    url = f"{base_url}/{api_endpoint}"
    access_token = get_paypal_access_token()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    items = [{
        "recipient_type": "PAYPAL_ID",
        "amount": {
            "value": amount,
            "currency": currency
        },
        "note": note_content,
        "receiver": uuid} for uuid in uuids]

    payload = {
        "sender_batch_header": {
            "sender_batch_id": sender_batch_id,
            "email_subject": email_subject,
            "email_message": email_content
        },
        "items": items
    }
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    if response.status_code != 201:
        raise SendPaymentError
