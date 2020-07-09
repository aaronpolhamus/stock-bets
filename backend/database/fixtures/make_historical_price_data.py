import json
from datetime import datetime as dt, timedelta

import pandas as pd
import pytz

from backend.logic.base import (
    TIMEZONE,
    datetime_to_posix,
    nyse
)


def make_stock_data_records():
    with open("./database/fixtures/stock_data.json") as json_file:
        stock_data = json.load(json_file)

    timezone = pytz.timezone(TIMEZONE)
    unique_days = list(set([x["date"] for x in stock_data["AMZN"]]))
    schedule = nyse.schedule(start_date=dt.utcnow() - timedelta(days=15), end_date=dt.utcnow() + timedelta(days=15))
    trading_days = []
    for i in range(5):
        trading_days.append(schedule.iloc[i]["market_open"])
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
