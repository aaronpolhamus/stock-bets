"""Not a drill. This logic for handles actual cash payments to/from  users. Treat with great care, and test thoroughly!
"""
import base64
import time

import requests
from backend.config import Config
from backend.database.helpers import add_row
from backend.database.helpers import query_to_dict


def get_paypal_access_token(client_id=Config.PAYPAL_CLIENT_ID, secret=Config.PAYPAL_SECRET):
    url = "https://api.sandbox.paypal.com/v1/oauth2/token"
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
