import json
import os
from datetime import datetime as dt
import time

import pandas as pd
import pytz
import requests

from backend.logic.stock_data import IEX_BASE_PROD_URL, TIMEZONE

DOWNLOAD = False
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


if __name__ == '__main__':
    if DOWNLOAD:
        stock_data = dict()
        for symbol in stocks_to_harvest:
            res = requests.get(f"{IEX_BASE_PROD_URL}/stable/stock/{symbol}/chart/5dm?token={IEX_KEY}")
            stock_data[symbol] = res.json()

        with open("./database/fixtures/caches/stock_data.json", 'w') as outfile:
            json.dump(stock_data, outfile)
    else:
        with open("./database/fixtures/caches/stock_data.json") as json_file:
            stock_data = json.load(json_file)

    timezone = pytz.timezone(TIMEZONE)
    unique_days = list(set([x["date"] for x in stock_data["AMZN"]]))
    trading_days = pd.bdate_range(end=dt.utcnow(), periods=len(unique_days), freq="B")
    data_entry_array = []
    for actual_day, simulated_day in zip(unique_days, trading_days):
        for symbol in stock_data.keys():
            actual_day_subset = [entry for entry in stock_data[symbol] if entry["date"] == actual_day]
            for record in actual_day_subset:
                simulated_date = simulated_day.strftime("%Y-%m-%d")
                str_time = f"{simulated_date} {record['minute']}"
                base_date = pd.to_datetime(str_time, format="%Y-%m-%d %H:%M")
                localized_date = timezone.localize(base_date)
                utc_date = localized_date.astimezone(pytz.utc)
                posix_time = time.mktime(utc_date.timetuple())
                data_entry_array.append(dict(symbol=symbol, price=record["average"], timestamp=posix_time))

    with open("./database/fixtures/caches/price_records.json", 'w') as outfile:
        json.dump(data_entry_array, outfile)
