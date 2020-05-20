import json
import os
import requests

from backend.logic.stock_data import IEX_BASE_PROD_URL


IEX_KEY = os.getenv("IEX_API_SECRET_PROD")

stocks_to_harvest = [
    "AMZN",
    "TSLA",
    "LYFT",
    "SPXU",
    "NVDA",
    "NKE",
    "MELI"
]

json_records = dict()
for symbol in stocks_to_harvest:
    res = requests.get(f"{IEX_BASE_PROD_URL}/stable/stock/{symbol}/chart/5dm?token={IEX_KEY}")
    json_records[symbol] = res.json()

with open("/tmp/stock_data.json", 'w') as outfile:
    json.dump(json_records, outfile)


def prepare_data_frame_records():
    pass
