from datetime import datetime as dt, timedelta
import sys
import time

import pandas as pd

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from backend.tasks.redis import rds
from backend.config import Config
from backend.logic.base import (
    posix_to_datetime,
    nyse,
    get_schedule_start_and_end
)

IEX_BASE_SANBOX_URL = "https://sandbox.iexapis.com/"
IEX_BASE_PROD_URL = "https://cloud.iexapis.com/"


def during_trading_day():
    posix_time = time.time()
    nyc_time = posix_to_datetime(posix_time)
    schedule = nyse.schedule(nyc_time, nyc_time)
    if schedule.empty:
        return False
    start_day, end_day = get_schedule_start_and_end(schedule)
    return start_day <= posix_time < end_day


def get_next_trading_day_schedule(current_day: dt):
    """For day orders we need to know when the next trading day happens if the order is placed after hours.
    """
    schedule = nyse.schedule(current_day, current_day)
    while schedule.empty:
        current_day += timedelta(days=1)
        schedule = nyse.schedule(current_day, current_day)
    return schedule


# Selenium web scraper for keeping exchange symbols up to date
# ------------------------------------------------------------
def get_web_table_object(timeout=20):
    print("starting selenium web driver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(chrome_options=options)
    driver.get(Config.SYMBOLS_TABLE_URL)
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.TAG_NAME, "table")))


def extract_row_data(row):
    list_entry = dict()
    split_entry = row.text.split(" ")
    list_entry["symbol"] = split_entry[0]
    list_entry["name"] = " ".join(split_entry[2:])
    return list_entry


def get_symbols_table(n_rows=None):
    table = get_web_table_object()
    rows = table.find_elements_by_tag_name("tr")
    row_list = list()
    n = len(rows)
    print(f"extracting available {n} rows of symbols data...")
    for i, row in enumerate(rows):
        list_entry = extract_row_data(row)
        if list_entry["symbol"] == "Symbol":
            continue
        row_list.append(list_entry)
        sys.stdout.write(f"\r{i} / {n} rows")
        sys.stdout.flush()
        if n_rows and len(row_list) == n_rows:
            # just here for low-cost testing
            break

    return pd.DataFrame(row_list)


# Functions for accessing and storing price data
# ----------------------------------------------
def fetch_iex_price(symbol):
    secret = Config.IEX_API_SECRET_SANDBOX if not Config.IEX_API_PRODUCTION else Config.IEX_API_SECRET_PROD
    base_url = IEX_BASE_SANBOX_URL if not Config.IEX_API_PRODUCTION else IEX_BASE_PROD_URL
    res = requests.get(f"{base_url}/stable/stock/{symbol}/quote?token={secret}")
    if res.status_code == 200:
        quote = res.json()
        timestamp = quote["latestUpdate"] / 1000
        price = quote["latestPrice"]
        return price, timestamp


def fetch_end_of_day_cache(symbol):
    """This function checks whether a symbol has a current end-of-trading day cache. If it does, and a user is on the
    platform during non-trading hours, we can use this updated value. If there isn't a valid cache entry we'll return
    None and use that a trigger to pull data
    """
    posix_time = time.time()
    if not during_trading_day():
        if rds.exists(symbol):
            price, update_time = rds.get(symbol).split("_")
            update_time = float(update_time)
            seconds_delta = posix_time - update_time
            ny_update_time = posix_to_datetime(update_time)
            if seconds_delta < 16.5 * 60 * 60 and ny_update_time.hour == 15 and ny_update_time.minute >= 59:
                return float(price), update_time
    return None, None


def get_all_active_symbols(db_session):
    with db_session.connection() as conn:
        result = conn.execute("""
        SELECT DISTINCT gb.symbol FROM
        game_balances gb
        INNER JOIN
          (SELECT DISTINCT game_id
          FROM game_status
          WHERE status = 'active') active_ids
        ON gb.game_id = active_ids.game_id
        WHERE gb.balance_type = 'virtual_stock';
        """)
        db_session.remove()

    return [x[0] for x in result]
