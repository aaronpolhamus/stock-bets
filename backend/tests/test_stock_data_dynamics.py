from datetime import datetime as dt
import time
import unittest

import pandas_market_calendars as mcal
import pytz

from backend.logic.stock_data import (
    posix_to_datetime,
    datetime_to_posix,
    during_trading_day,
    get_web_table_object,
    extract_row_data,
    get_symbols_table,
    fetch_iex_price,
    fetch_end_of_day_cache,
    TIMEZONE
)


class TestStockDataLogic(unittest.TestCase):
    """Purpose of these tests is to verify that our core operations to harvest stock data for the applications are
    working as expected. These get mocked later in celery and integration testing
    """

    def test_time_handlers(self):
        posix_time = 1590165714.1528566
        actual_date = dt(2020, 5, 22, 12, 41, 54, 152857)
        localizer = pytz.timezone(TIMEZONE)
        localized_date = localizer.localize(actual_date)
        self.assertEqual(posix_to_datetime(posix_time), localized_date)
        self.assertAlmostEqual(posix_time, datetime_to_posix(localized_date), 0)

        self.assertTrue(during_trading_day(posix_time))
        posix_time_later = posix_time + 8 * 60 * 60
        self.assertFalse(during_trading_day(posix_time_later))

        # Christmas 2020 is on a Friday, which would normally be a trading day. We use 3pm, which would normally be a
        # trading time. Because this is a holiday, the result should be false
        christmas_2020_3pm = 1608908400
        self.assertFalse(during_trading_day(christmas_2020_3pm))

        # Check during trading day just one second before and after open/close
        nyse = mcal.get_calendar('NYSE')
        schedule = nyse.schedule(actual_date, actual_date)
        start_day, end_day = [datetime_to_posix(x) for x in schedule.iloc[0][["market_open", "market_close"]]]
        self.assertFalse(during_trading_day(start_day - 1))
        self.assertTrue(during_trading_day((start_day + end_day) / 2))
        self.assertFalse(during_trading_day(end_day + 1))

        # Finally, just double-check that the real-time, default invocation works as expected
        posix_now = time.time()
        nyc_now = posix_to_datetime(posix_now)
        schedule = nyse.schedule(nyc_now, nyc_now)
        start_day, end_day = [datetime_to_posix(x) for x in schedule.iloc[0][["market_open", "market_close"]]]
        during_trading = start_day <= posix_now <= end_day
        # there is a non-zero chance that this test will fail at exactly the beginning or end of a trading day
        self.assertEqual(during_trading, during_trading_day())

    def test_get_symbols(self):
        """For now we pull data from IEX cloud. We also scrape their daily published listing of available symbols to
        build the selection inventory for the frontend. Although the core data source will change in the future, these
        operations need to remain intact.
        """
        pass

    def test_price_fetchers(self):
        pass
