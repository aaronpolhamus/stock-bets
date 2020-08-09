"""Not a drill. This logic for handles actual cash payments to/from  users. Treat with great care, and test thoroughly!
"""
import base64
import requests
from backend.config import Config


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
