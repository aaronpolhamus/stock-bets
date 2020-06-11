import json
import os
from datetime import datetime as dt

import pandas as pd
import pytz
import requests

from backend.logic.base import (
    TIMEZONE,
    datetime_to_posix,
)
from backend.logic.stock_data import IEX_BASE_PROD_URL


DOWNLOAD = False
IEX_KEY = os.getenv("IEX_API_SECRET_PROD")
STOCKS_TO_PULL = [
    "AMZN",
    "TSLA",
    "LYFT",
    "SPXU",
    "NVDA",
    "NKE",
    "MELI"
]


def make_stock_data_records():
    with open("./database/fixtures/stock_data.json") as json_file:
        stock_data = json.load(json_file)

    timezone = pytz.timezone(TIMEZONE)
    unique_days = list(set([x["date"] for x in stock_data["AMZN"]]))
    trading_days = pd.bdate_range(end=dt.utcnow(), periods=len(unique_days), freq="B")
    price_records = []
    for actual_day, simulated_day in zip(unique_days, trading_days):
        for stock_symbol in stock_data.keys():
            actual_day_subset = [entry for entry in stock_data[stock_symbol] if entry["date"] == actual_day]
            for record in actual_day_subset:
                simulated_date = simulated_day.strftime("%Y-%m-%d")
                str_time = f"{simulated_date} {record['minute']}"
                base_date = pd.to_datetime(str_time, format="%Y-%m-%d %H:%M")
                localized_date = timezone.localize(base_date)
                posix_time = datetime_to_posix(localized_date)
                price_records.append(dict(symbol=stock_symbol, price=record["average"], timestamp=posix_time))
    return price_records


if __name__ == '__main__':
    if DOWNLOAD:
        data = dict()
        for symbol in STOCKS_TO_PULL:
            res = requests.get(f"{IEX_BASE_PROD_URL}/stable/stock/{symbol}/chart/5dm?token={IEX_KEY}")
            data[symbol] = res.json()

        with open("./database/fixtures/stock_data.json", 'w') as outfile:
            json.dump(data, outfile)
