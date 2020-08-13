from copy import deepcopy
import json
from datetime import datetime as dt, timedelta

import numpy as np
import pandas as pd
import pytz

from backend.logic.base import (
    SECONDS_IN_A_DAY,
    TIMEZONE,
    datetime_to_posix,
    get_trading_calendar
)

np.random.seed(123)


def make_stock_data_records():
    with open("./database/fixtures/stock_data.json") as json_file:
        stock_data = json.load(json_file)

    timezone = pytz.timezone(TIMEZONE)
    sample_days = list(set([x["date"] for x in stock_data["AMZN"]]))
    sample_days.sort()
    schedule = get_trading_calendar(start_date=dt.utcnow() - timedelta(days=15), end_date=dt.utcnow() + timedelta(days=15))
    trading_days = []
    for i in range(5):
        trading_days.append(schedule.iloc[i]["market_open"])

    ixic_value = ixic_value_0 = 10_473.83
    gspc_value = gspc_value_0 = 3_215.57
    dji_value = dji_value_0 = 27_734.71
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
                ixic_value += np.random.normal(0, 0.0005 * ixic_value_0)
                gspc_value += np.random.normal(0, 0.0005 * gspc_value_0)
                dji_value += np.random.normal(0, 0.0005 * dji_value_0)
                index_records.append(dict(symbol="^IXIC", value=ixic_value, timestamp=posix_time))
                index_records.append(dict(symbol="^GSPC", value=gspc_value, timestamp=posix_time))
                index_records.append(dict(symbol="^DJI", value=dji_value, timestamp=posix_time))

    # our simulation requires a full two weeks worth of data. append new entries for indexes and prices adding 7 days
    # worth of time to each.
    extended_price_records = deepcopy(price_records)
    extended_index_records = deepcopy(index_records)
    for price_record, index_record in zip(price_records, index_records):
        pr_copy = deepcopy(price_record)
        pr_copy["timestamp"] += SECONDS_IN_A_DAY * 7
        extended_price_records.append(pr_copy)
        ir_copy = deepcopy(index_record)
        ir_copy["timestamp"] += SECONDS_IN_A_DAY * 7
        extended_index_records.append(ir_copy)

    return extended_price_records, extended_index_records
