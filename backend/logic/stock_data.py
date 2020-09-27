import sys
import time
from datetime import datetime as dt
from re import sub
from typing import List


import pandas as pd
import requests
from backend.database.db import engine
from backend.database.helpers import add_row, query_to_dict
from backend.logic.base import (
    datetime_to_posix,
    during_trading_day,
    get_end_of_last_trading_day,
    SECONDS_IN_A_DAY,
    posix_to_datetime,
    get_trading_calendar,
    get_schedule_start_and_end,
    get_current_game_cash_balance,
)
from backend.tasks.redis import rds
from config import Config
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException
)

TRACKED_INDEXES = ["^IXIC", "^GSPC", "^DJI"]


class SeleniumDriverError(Exception):

    def __str__(self):
        return "It looks like the selenium web driver failed to instantiate properly"


def get_web_driver():
    print("starting selenium web driver...")
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--privileged")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(options=options)
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


def get_symbols_table(n_rows=None, timeout=60):
    driver = get_web_driver()
    url = "https://iextrading.com/trading/eligible-symbols/"
    first_row_xpath = '// *[ @ id = "exchange-symbols"] / table / tbody / tr[1]'
    driver.get(url)
    _ = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, first_row_xpath)))
    rows = driver.find_elements_by_tag_name("tr")
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
    res = requests.get(f"{Config.IEX_API_URL}/stable/stock/{symbol}/quote?token={Config.IEX_API_SECRET}")
    if res.status_code == 200:
        quote = res.json()
        timestamp = quote["latestUpdate"] / 1000
        if Config.ENV == "dev":
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

def get_day_start(start_time_dt: dt):
    start_time = datetime_to_posix(start_time_dt)
    schedule = get_trading_calendar(start_time_dt, start_time_dt)
    if not schedule.empty:
        start_time, _ = get_schedule_start_and_end(schedule)
    return start_time


def retrieve_nasdaq_splits(driver, included_symbols, timeout=45) -> pd.DataFrame:
    url = "https://www.nasdaq.com/market-activity/stock-splits"
    table_xpath = '/html/body/div[4]/div/main/div[2]/div[2]/div[2]/div/div[2]/div/div[3]/div[5]'
    nasdaq_data_column_names = ["symbol", "ratio", "executionDate"]
    driver.get(url)
    table = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, table_xpath)))
    rows = table.find_elements_by_tag_name("tr")
    table_data_array = []
    for row in rows[1:]:
        table_data_entry = dict()
        for data_column in nasdaq_data_column_names:
            table_data_entry[data_column] = row.find_element_by_css_selector(f'*[data-column="{data_column}"]').text
        table_data_array.append(table_data_entry)
    df = pd.DataFrame(table_data_array)
    return df[df["symbol"].isin(included_symbols)]


def parse_nasdaq_splits(df: pd.DataFrame):
    num_cols = ["numerator", "denominator"]
    current_datetime = posix_to_datetime(time.time(), timezone="UTC")  # because selenium defaults to UTC
    current_date = current_datetime.date()
    df["executionDate"] = pd.to_datetime(df["executionDate"])
    df = df[df["executionDate"].dt.date == current_date]
    df = df[df["ratio"].str.contains(":")]  # sometimes the calendar encodes splits as %. We don't handle this for now
    if not df.empty:
        df[num_cols] = df["ratio"].str.split(" : ", expand=True)
        df[num_cols] = df[num_cols].apply(pd.to_numeric)
        df["exec_date"] = get_day_start(current_datetime)
        df = df[num_cols + ["symbol", "exec_date"]]
    return df


def retrieve_yahoo_splits(driver, included_symbols, timeout=15):
    url = "https://finance.yahoo.com/calendar/splits"
    table_x_path = '//*[@id="cal-res-table"]/div[1]/table/tbody'
    label_names = ["Symbol", "Ratio"]
    driver.get(url)
    try:
        table = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, table_x_path)))
    except TimeoutException:
        try:
            couldnt_find_path = '//*[@id="fin-cal-table"]/div/div/span'
            WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, couldnt_find_path)))
            return pd.DataFrame()
        except Exception as e:
            raise e
    rows = table.find_elements_by_tag_name("tr")
    table_data_array = []
    for row in rows:
        table_data_entry = dict()
        for label in label_names:
            table_data_entry[label] = row.find_element_by_css_selector(f'*[aria-label="{label}"]').text
        table_data_array.append(table_data_entry)
    df = pd.DataFrame(table_data_array)
    df = df[df["Symbol"].isin(included_symbols)]
    return df.rename(columns={"Symbol": "symbol", "Ratio": "ratio"})


def parse_yahoo_splits(df: pd.DataFrame, excluded_symbols=None):
    if df.empty:
        return df
    current_datetime = posix_to_datetime(time.time(), timezone="UTC")  # because selenium defaults to UTC
    num_cols = ["denominator", "numerator"]
    if excluded_symbols is None:
        excluded_symbols = []
    df = df[~df["symbol"].isin(excluded_symbols)]
    if df.empty:
        del df["ratio"]
        return df
    df[num_cols] = df["ratio"].str.split(" - ", expand=True)
    df[num_cols] = df[num_cols].apply(pd.to_numeric)
    df["exec_date"] = get_day_start(current_datetime)
    return df[["symbol", "exec_date"] + num_cols]


def scrape_stock_splits():
    driver = get_web_driver()
    _included_symbols = query_to_dict("SELECT symbol FROM symbols")
    included_symbols = [x["symbol"] for x in _included_symbols]
    nasdaq_raw_splits = retrieve_nasdaq_splits(driver, included_symbols)
    nasdaq_splits = parse_nasdaq_splits(nasdaq_raw_splits)
    nasdaq_symbols = nasdaq_splits["symbol"].to_list()
    yahoo_raw_splits = retrieve_yahoo_splits(driver, included_symbols)
    yahoo_splits = parse_yahoo_splits(yahoo_raw_splits, nasdaq_symbols)
    df = pd.concat([nasdaq_splits, yahoo_splits])
    if not df.empty:
        with engine.connect() as conn:
            df.to_sql("stock_splits", conn, if_exists="append", index=False)


def get_game_ids_by_status(status="active"):
    with engine.connect() as conn:
        result = conn.execute("""
        SELECT g.id
        FROM games g
        INNER JOIN
        (
          SELECT gs.game_id, gs.status
          FROM game_status gs
          INNER JOIN
          (SELECT game_id, max(id) as max_id
            FROM game_status
            GROUP BY game_id) grouped_gs
          ON
            gs.id = grouped_gs.max_id
          WHERE gs.status = %s
        ) pending_game_ids
        ON
          g.id = pending_game_ids.game_id;""", status).fetchall()
    return [x[0] for x in result]


def get_most_recent_prices(symbols: List):
    if len(symbols) == 0:
        return None
    sql = f"""
        SELECT p.symbol, p.price, p.timestamp
        FROM prices p
        INNER JOIN (
        SELECT symbol, max(id) as max_id
          FROM prices
          GROUP BY symbol) max_price
        ON p.id = max_price.max_id
        WHERE p.symbol IN ({','.join(['%s'] * len(symbols))})
    """
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=symbols)


def get_splits(start_time: float, end_time: float) -> pd.DataFrame:
    if start_time is None:
        start_time = datetime_to_posix(dt.utcnow().replace(hour=0, minute=0))

    if end_time is None:
        end_time = time.time()

    # get active games and symbols
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM stock_splits WHERE exec_date >= %s AND exec_date <= %s", conn, params=[
            start_time, end_time])


def get_active_holdings_for_games(symbol: str) -> pd.DataFrame:
    """This function helps to apply splits and dividends updates across all active stockbets games. It is meant to be
    used with a for-loop that iterates over the stocks of interest
    """
    active_ids = get_game_ids_by_status()
    with engine.connect() as conn:
        return pd.read_sql(f"""
          SELECT user_id, game_id, balance_type, balance, symbol FROM game_balances g
          INNER JOIN (
            SELECT MAX(id) as max_id
            FROM game_balances
            WHERE 
              symbol = %s AND
              game_id IN ({', '.join(['%s'] * len(active_ids))}) AND
              balance > 0
            GROUP BY game_id, user_id
          ) grouped_db
          ON grouped_db.max_id = g.id""", conn, params=[symbol] + active_ids)


def apply_stock_splits(start_time: float = None, end_time: float = None):
    splits = get_splits(start_time, end_time)
    if splits.empty:
        return

    last_prices = get_most_recent_prices(splits["symbol"].to_list())
    for i, row in splits.iterrows():
        symbol = row["symbol"]
        numerator = row["numerator"]
        denominator = row["denominator"]
        exec_date = row["exec_date"]
        df = get_active_holdings_for_games(symbol)
        if df.empty:
            continue

        # make order status updates here. implement dask or spark here when the job getting to heavy to run locally
        # (e.g. see https://docs.dask.org/en/latest/dataframe-api.html#dask.dataframe.read_sql_table)
        df["transaction_type"] = "stock_split"
        df["order_status_id"] = None
        df["timestamp"] = exec_date
        df["fractional_balance"] = df["balance"] * numerator / denominator
        df["balance"] = df["balance"] * numerator // denominator
        df["fractional_balance"] -= df["balance"]

        # identify any fractional shares that need to be converted to cash
        mask = df["fractional_balance"] > 0
        fractional_df = df[mask]
        last_price = float(last_prices.loc[last_prices["symbol"] == symbol, "price"].iloc[0])
        for _, fractional_row in fractional_df.iterrows():
            game_id = fractional_row["game_id"]
            user_id = fractional_row["user_id"]
            cash_balance = get_current_game_cash_balance(user_id, game_id)
            add_row("game_balances",
                    user_id=user_id,
                    game_id=game_id,
                    timestamp=exec_date,
                    balance_type="virtual_cash",
                    balance=cash_balance + fractional_row["fractional_balance"] * last_price,
                    transaction_type="stock_split")

        # write updated balances
        del df["fractional_balance"]
        with engine.connect() as conn:
            df.to_sql("game_balances", conn, index=False, if_exists="append")


def scrape_dividends(date: dt = None, timeout: int = 120) -> pd.DataFrame:
    if date is None:
        date = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if get_trading_calendar(date, date).empty:
        return pd.DataFrame()
    day_of_month = str(date.day)
    month = date.strftime('%B %Y')
    driver = get_web_driver()
    driver.get('https://www.thestreet.com/dividends/index.html')
    table_x_path = '//*[@id="listed_divdates"]/table/tbody[2]'
    if day_of_month != str(dt.now().day):
        click_calendar(day_of_month, month, driver, timeout)
    next_page = True
    first_page = True
    dividends_table = []
    while next_page:
        table = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, table_x_path)))
        dividends_table += get_table_values(table)
        next_page = click_next_page(table, first_page)
        first_page = False
    df = pd.DataFrame(dividends_table, columns=['symbol', 'company', 'amount', 'yield', 'exec_date'])
    del df['yield']
    df["amount"] = df['amount'].replace('[\$,]', '', regex=True).astype(float)
    dividend_exdate = pd.to_datetime(df['exec_date'].iloc[0])
    posix_dividend_exdate = datetime_to_posix(dividend_exdate)
    df['exec_date'] = posix_dividend_exdate
    df.drop_duplicates(inplace=True)
    with engine.connect() as conn:
        df.to_sql("dividends", conn, if_exists="append", index=False)


def insert_dividends_to_db(dividends: pd.DataFrame):
    with engine.connect() as conn:
        dividends.to_sql('dividends', conn, if_exists='append', index=False)


def calculate_dividends_for_stock(stock, dividend, dividend_id):
    df = get_active_holdings_for_games(stock)
    if df.empty:
        return df
    df['amount'] = df['balance'] * dividend
    df['dividend_id'] = dividend_id
    return df


def apply_dividends_to_stocks(date: dt = None):
    dividends = get_dividends_of_date(date)
    if dividends is None:
        return None

    for _, row in dividends.iterrows():
        df = calculate_dividends_for_stock(row["symbol"], row["amount"], row["id"])
        df.apply(lambda _r: add_virtual_cash(_r['game_id'], _r['user_id'], _r['dividend_id'], _r['amount']), axis=1)


def add_virtual_cash(game_id: int, user_id: int, dividend_id: int, amount: float):
    current_cash = get_current_game_cash_balance(user_id, game_id) + amount
    now = datetime_to_posix(dt.now())
    add_row("game_balances", user_id=user_id, game_id=game_id, timestamp=now, balance_type='virtual_cash',
            balance=current_cash, dividend_id=dividend_id)


def get_dividends_of_date(date: dt = None) -> pd.DataFrame:
    if date is None:
        date = dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
    posix = datetime_to_posix(date)
    df = pd.DataFrame(query_to_dict(f"select * from dividends where exec_date={posix}"))
    return df


def get_table_values(table) -> list:
    rows = table.find_elements_by_tag_name('tr')
    current_rows = []
    for row in rows:
        current_rows.append(row.text.split('\n'))
    return current_rows


def select_day_in_calendar(month, day_of_month) -> int:
    calendar_days = month.text.split('\n')
    day_index = 0
    for day in calendar_days:
        if day == day_of_month:
            return day_index
        if len(day) > 2:
            day_index += len(day.split())
        else:
            day_index += 1


def click_calendar(day_of_month, target_month, driver, timeout) -> None:
    choose_month(driver, target_month)
    calendar_x_path = '//*[@id="cal1_0"]/tbody'
    month = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, calendar_x_path)))
    day_index = select_day_in_calendar(month, day_of_month)
    day_x_path = f'//*[@id="cal1_0_cell{day_index}"]/a'
    day_cell = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, day_x_path)))
    day_cell.click()


def click_next_page(driver, first) -> bool:
    page = 3
    if first:
        page = 1
    button_x_path = f'/html/body/div[8]/div[2]/div[1]/table/tbody/tr/td/div[2]/div[2]/div[3]/a[{page}]'
    try:
        next_button = driver.find_element_by_xpath(button_x_path)
    except NoSuchElementException:
        return False
    if next_button is not None:
        next_button.click()
        return True
    return False


def choose_month(driver, month):
    back_row_xpath = '//*[@id="cal1_0"]/thead/tr[1]/th/div/a'
    current_month_xpath = '//*[@id="cal1_0"]/thead/tr[1]/th/div'
    current_month = driver.find_element_by_xpath(current_month_xpath).text.split('\n')[-1]
    while current_month != month:
        back_arrow = driver.find_element_by_xpath(back_row_xpath)
        back_arrow.click()
        current_month = driver.find_element_by_xpath(current_month_xpath).text.split('\n')[-1]
