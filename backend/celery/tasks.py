import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

EXEC_PATH = "/home/backend/chromedriver"


def get_web_table_object(timeout=10, exec_path=EXEC_PATH, chrome_options=options):
    driver = webdriver.Chrome(executable_path=exec_path, chrome_options=chrome_options)
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
    for i, row in enumerate(rows):
        list_entry = extract_row_data(row)
        if list_entry["symbol"] == "Symbol":
            continue
        row_list.append(list_entry)
        sys.stdout.write(f"\r{i} / {n} rows")
        sys.stdout.flush()

    return pd.DataFrame(row_list)


if __name__ == '__main__':
    symbols_table = get_symbols_table()
    symbols_table.to_csv("/tmp/df.csv")
