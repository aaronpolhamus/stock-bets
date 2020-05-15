from backend.tasks.celery import app
import sys

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine

from backend.config import Config


@app.task
def ping():
    # silly little test function tha we'll around until the infrastructure hardens a bit
    print("ping!!!")


@app.task(bind=True, default_retry_delay=10)
def update_symbols_table(self):

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver_path = "/home/backend/chromedriver"
    target_url = "https://iextrading.com/trading/eligible-symbols/"

    def get_web_table_object(timeout=20, target=target_url, exec_path=driver_path, chrome_options=options):
        print("starting selenium web driver...")
        driver = webdriver.Chrome(executable_path=exec_path, chrome_options=chrome_options)
        driver.get(target)
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

    try:
        symbols_table = get_symbols_table()
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        print("writing to db...")
        with engine.connect() as conn:
            conn.execute("TRUNCATE TABLE symbols;")
            symbols_table.to_sql("symbols", conn, if_exists="append", index=False)
    except Exception as exc:
        raise self.retry(exc=exc)


if __name__ == '__main__':
    ping()