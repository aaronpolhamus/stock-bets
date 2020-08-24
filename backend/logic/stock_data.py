import sys
import time
from re import sub

import pandas as pd
import requests
from config import Config
from database.db import engine
from database.helpers import add_row
from logic.base import (
    during_trading_day,
    get_end_of_last_trading_day,
    SECONDS_IN_A_DAY,
    posix_to_datetime,
    get_trading_calendar,
    get_schedule_start_and_end
)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from backend.tasks.redis import rds

IEX_BASE_SANBOX_URL = "https://sandbox.iexapis.com/"
IEX_BASE_PROD_URL = "https://cloud.iexapis.com/"


def get_web_driver(web_driver="chrome"):
    print("starting selenium web driver...")
    if web_driver == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-proxy-server")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1200, 600)

    if web_driver == "firefox":
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-proxy-server")
        options.add_argument("--proxy-server='direct://'")
        options.add_argument("--proxy-bypass-list=*")
        driver = webdriver.Firefox(executable_path="/home/backend/geckodriver", options=options)
        driver.set_window_size(1200, 600)
    return driver


def currency_string_to_float(money_string):
    if type(money_string) == str:
        return float(sub(r'[^\d.]', '', money_string))
    return money_string


def extract_row_data(row):
    list_entry = dict()
    split_entry = row.text.split(" ")
    list_entry["symbol"] = split_entry[0]
    list_entry["name"] = " ".join(split_entry[2:])
    return list_entry


def get_symbols_table(n_rows=None, timeout=20):
    driver = get_web_driver()
    driver.get(Config.SYMBOLS_TABLE_URL)
    table = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.TAG_NAME, "table")))
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


def get_index_value(symbol, timeout=120):
    quote_url = f"{Config.YAHOO_FINANCE_URL}/quote/{symbol}"
    driver = get_web_driver()
    driver.get(quote_url)
    header = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.XPATH, '//*[@id="quote-header-info"]/div[3]/div/div/span[1]')))
    return currency_string_to_float(header.text)


def update_index_value(symbol):
    value = get_index_value(symbol)
    if during_trading_day():
        add_row("indexes", symbol=symbol, value=value, timestamp=time.time())
        return True

    # a bit of logic to get the close of day price
    with engine.connect() as conn:
        max_time = conn.execute("SELECT MAX(timestamp) FROM indexes WHERE symbol = %s;", symbol).fetchone()[0]
        if max_time is None:
            max_time = 0

    ref_day = time.time()
    eod = get_end_of_last_trading_day(ref_day)
    while eod > ref_day:
        ref_day -= SECONDS_IN_A_DAY
        eod = get_end_of_last_trading_day(ref_day)

    if max_time < eod <= time.time():
        add_row("indexes", symbol=symbol, value=value, timestamp=eod)
        return True

    return False


def get_cache_price(symbol):
    data = rds.get(symbol)
    if data is None:
        return None, None
    return [float(x) for x in data.split("_")]


def fetch_price_iex(symbol):
    secret = Config.IEX_API_SECRET_SANDBOX if not Config.IEX_API_PRODUCTION else Config.IEX_API_SECRET_PROD
    base_url = IEX_BASE_SANBOX_URL if not Config.IEX_API_PRODUCTION else IEX_BASE_PROD_URL
    res = requests.get(f"{base_url}/stable/stock/{symbol}/quote?token={secret}")
    if res.status_code == 200:
        quote = res.json()
        timestamp = quote["latestUpdate"] / 1000
        if Config.IEX_API_PRODUCTION is False:
            timestamp = time.time()
        price = quote["latestPrice"]
        return price, timestamp


def fetch_price(symbol, provider="iex"):
    if provider == "iex":
        return fetch_price_iex(symbol)


def set_cache_price(symbol, price, timestamp):
    rds.set(symbol, f"{price}_{timestamp}")


# harvest stock splits
# --------------------

def get_current_day_start_posix():
    start_time = time.time()
    start_time_dt = posix_to_datetime(start_time)
    schedule = get_trading_calendar(start_time_dt, start_time_dt)
    if not schedule.empty:
        start_time, _ = get_schedule_start_and_end(schedule)
    return start_time


def retrieve_nasdaq_splits(driver, timeout=30) -> pd.DataFrame:
    url = "https://www.nasdaq.com/market-activity/stock-splits"
    table_xpath = "/html/body/div[4]/div/main/div[2]/div[2]/div[2]/div/div[2]/div/div[3]/div[5]/div[2]/table/tbody"
    nasdaq_data_column_names = ["symbol", "ratio", "executionDate"]
    driver.get(url)
    table = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, table_xpath)))
    rows = table.find_elements_by_tag_name("tr")
    table_data_array = []
    for row in rows:
        table_data_entry = dict()
        for data_column in nasdaq_data_column_names:
            table_data_entry[data_column] = row.find_element_by_css_selector(f'*[data-column="{data_column}"]').text
        table_data_array.append(table_data_entry)
    return pd.DataFrame(table_data_array)


def parse_nasdaq_splits(df: pd.DataFrame):
    num_cols = ["denominator", "numerator"]
    current_date = posix_to_datetime(time.time()).date()
    df["executionDate"] = pd.to_datetime(df["executionDate"])
    df = df[df["executionDate"].dt.date == current_date]
    df = df[df["ratio"].str.contains(":")]  # sometimes the calendar encodes splits as %. We don't handle this for now
    if not df.empty:
        df[num_cols] = df["ratio"].str.split(" : ", expand=True)
        df[num_cols] = df[num_cols].apply(pd.to_numeric)
        df["exec_date"] = get_current_day_start_posix()
    return df[num_cols + ["symbol", "exec_date"]]


def retrieve_yahoo_splits(driver, timeout=120):
    url = "https://finance.yahoo.com/calendar/splits"
    table_x_path = '//*[@id="cal-res-table"]/div[1]/table/tbody'
    label_names = ["Symbol", "Ratio"]
    driver.get(url)
    table = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, table_x_path)))
    rows = table.find_elements_by_tag_name("tr")
    table_data_array = []
    for row in rows:
        table_data_entry = dict()
        for label in label_names:
            table_data_entry[label] = row.find_element_by_css_selector(f'*[aria-label="{label}"]').text
        table_data_array.append(table_data_entry)
    df = pd.DataFrame(table_data_array)
    return df.rename(columns={"Symbol": "symbol", "Ratio": "ratio"})


def parse_yahoo_splits(df: pd.DataFrame, excluded_symbols=None):
    num_cols = ["numerator", "denominator"]
    if excluded_symbols is None:
        excluded_symbols = []
    df = df[~df["symbol"].isin(excluded_symbols)]
    df[num_cols] = df["ratio"].str.split(" - ", expand=True)
    df[num_cols] = df[num_cols].apply(pd.to_numeric)
    df["exec_date"] = get_current_day_start_posix()
    return df[["symbol", "exec_date"] + num_cols]


def log_stock_splits():
    driver = get_web_driver("firefox")
    nasdaq_raw_splits = retrieve_nasdaq_splits(driver)
    nasdaq_splits = parse_nasdaq_splits(nasdaq_raw_splits)
    nasdaq_symbols = nasdaq_splits["symbol"].to_list()
    yahoo_raw_splits = retrieve_yahoo_splits(driver)
    yahoo_splits = parse_yahoo_splits(yahoo_raw_splits, nasdaq_symbols)
    splits_update = pd.concat([nasdaq_splits, yahoo_splits])
    with engine.connect() as conn:
        splits_update.to_sql("stock_splits", conn, if_exists="append", index=False)
