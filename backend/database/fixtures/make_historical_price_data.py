import json
from datetime import datetime as dt, timedelta

import numpy as np
import pandas as pd
import pytz

from backend.logic.base import (
    TIMEZONE,
    datetime_to_posix,
    nyse
)

np.random.seed(123)


def make_stock_data_records():
    with open("./database/fixtures/stock_data.json") as json_file:
        stock_data = json.load(json_file)

    timezone = pytz.timezone(TIMEZONE)
    sample_days = list(set([x["date"] for x in stock_data["AMZN"]]))
    sample_days.sort()
    schedule = nyse.schedule(start_date=dt.utcnow() - timedelta(days=15), end_date=dt.utcnow() + timedelta(days=15))
    trading_days = []
    for i in range(5):
        trading_days.append(schedule.iloc[i]["market_open"])

    ixic_value = 10_473.83
    gspc_value = 3_215.57
    dji_value = 27_734.71
    price_records = []
    index_records = []
    for sample_day, simulated_day in zip(sample_days, trading_days):
        for stock_symbol in stock_data.keys():
            sample_day_subset = [entry for entry in stock_data[stock_symbol] if entry["date"] == sample_day]
            for record in sample_day_subset:
                simulated_date = simulated_day.strftime("%Y-%m-%d")
                str_time = f"{simulated_date} {record['minute']}"
                base_date = pd.to_datetime(str_time, format="%Y-%m-%d %H:%M")
                localized_date = timezone.localize(base_date)
                posix_time = datetime_to_posix(localized_date)
                price_records.append(dict(symbol=stock_symbol, price=record["average"], timestamp=posix_time))

        # add synthetic index data as well
        for index in ["^IXIC", "^GSPC", "^DJI"]:
            if index == "^IXIC":
                ixic_value += np.random.normal(ixic_value, 0.03 * ixic_value)
                value = ixic_value
            if index == "^GSPC":
                gspc_value += np.random.normal(gspc_value, 0.03 * ixic_value)
                value = gspc_value
            if index == "^DJI":
                dji_value += np.random.normal(dji_value, 0.03 * ixic_value)
                value = dji_value

            index_records.append(dict(symbol=index, value=value, timestamp=posix_time))

    return price_records, index_records
