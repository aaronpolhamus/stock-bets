from datetime import datetime as dt
import sys
import time

import pandas as pd
import pytz
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from backend.tasks.redis import r
from backend.config import Config

TIMEZONE = 'America/New_York'
IEX_BASE_SANBOX_URL = "https://sandbox.iexapis.com/"
IEX_BASE_PROD_URL = "https://cloud.iexapis.com/"


def localize_timestamp(ts, divide_by=1):
    """Given a POSIX timestamp, return the proper datetime signature for NYC
    """
    utc_dt = dt.utcfromtimestamp(ts / divide_by).replace(tzinfo=pytz.utc)
    tz = pytz.timezone(TIMEZONE)
    return utc_dt.astimezone(tz)


def during_trading_day():
    nyc_time = localize_timestamp(time.time())
    past_open = nyc_time.hour >= 9
    before_close = nyc_time.hour <= 16 and nyc_time.minute <= 30
    business_day = bool(len(pd.bdate_range(nyc_time, nyc_time)))
    return past_open and before_close and business_day


# Selenium web scraper for keeping exchange symbols up to date
# ------------------------------------------------------------
def get_web_table_object(timeout=20):
    print("starting selenium web driver...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(executable_path="/home/backend/chromedriver", chrome_options=options)
    driver.get("https://iextrading.com/trading/eligible-symbols/")
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.TAG_NAME, "table")))


def extract_row_data(row):
    list_entry = dict()
    split_entry = row.text.split(" ")
    list_entry["symbol"] = split_entry[0]
    list_entry["name"] = " ".join(split_entry[2:])
    return list_entry


def get_symbols_table():
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
    if not during_trading_day():
        if r.exists(symbol):
            price, update_time = r.get(symbol).split("_")
            update_time = float(update_time)
            seconds_delta = time.time() - update_time
            ny_update_time = localize_timestamp(update_time)
            if seconds_delta < 16.5 * 60 * 60 and ny_update_time.hour == 16 and ny_update_time.minute >= 29:
                return float(price), update_time
    return None
