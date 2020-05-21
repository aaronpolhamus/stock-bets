import unittest

from backend.logic.stock_data import (
    localize_timestamp,
    during_trading_day,
    get_web_table_object,
    extract_row_data,
    get_symbols_table,
    fetch_iex_price,
    fetch_end_of_day_cache,
)


class TestStockDataLogic(unittest.TestCase):
    """Purpose of these tests is to verify that our core operations to harvest stock data for the applications are
    working as expected. These get mocked later in celery and integration testing
    """

    def test_time_handlers(self):
        pass

    def test_get_symbols(self):
        """For now we pull data from IEX cloud. We also scrape their daily published listing of available symbols to
        build the selection inventory for the frontend. Although the core data source will change in the future, these
        operations need to remain intact.
        """
        pass

    def test_price_fetchers(self):
        pass
