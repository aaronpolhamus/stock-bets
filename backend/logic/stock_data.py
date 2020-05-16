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

from backend.config import Config


def localize_timestamp(ts, divide_by=1):
    utc_dt = dt.utcfromtimestamp(ts / divide_by).replace(tzinfo=pytz.utc)
    tz = pytz.timezone('America/New_York')
    return utc_dt.astimezone(tz)


def during_trading_day():
    nyc_time = localize_timestamp(time.time())
    past_open = nyc_time.hour >= 9
    before_close = nyc_time.hour <= 16 and nyc_time.minute <= 30
    business_day = bool(len(pd.bdate_range(nyc_time, nyc_time)))
    return past_open and before_close and business_day


# Selenium web scraper for keeping exchange symbols up to date
# #-----------------------------------------------------------
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
    base_url = "https://sandbox.iexapis.com/" if not Config.IEX_API_PRODUCTION else "https://cloud.iexapis.com/"
    res = requests.get(f"{base_url}/stable/stock/{symbol}/quote?token={secret}")
    if res.status_code == 200:
        quote = res.json()
        timestamp = quote["latestUpdate"] / 1000
        price = quote["latestPrice"]
        return price, timestamp
