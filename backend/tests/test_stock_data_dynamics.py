from datetime import datetime as dt
import time
import unittest
from unittest.mock import patch

import pandas_market_calendars as mcal
import pytz

from backend.logic.base import (
    datetime_to_posix,
    TIMEZONE
)
from backend.tasks.redis import rds
from backend.logic.stock_data import (
    posix_to_datetime,
    during_trading_day,
    get_symbols_table,
    fetch_iex_price,
    fetch_end_of_day_cache,
    get_schedule_start_and_end,
    get_next_trading_day_schedule,
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

        mexico_date = actual_date.replace(hour=11)
        localizer = pytz.timezone("America/Mexico_City")
        localized_date = localizer.localize(mexico_date)
        self.assertAlmostEqual(posix_time, datetime_to_posix(localized_date), 0)

        # Pre-stage all of the mocked current time values that will be called sequentially in the tests below.
        # ----------------------------------------------------------------------------------------------------
        with patch('backend.logic.stock_data.time') as current_time_mock:
            # Check during trading day just one second before and after open/close
            nyse = mcal.get_calendar('NYSE')
            schedule = nyse.schedule(actual_date, actual_date)
            start_day, end_day = [datetime_to_posix(x) for x in schedule.iloc[0][["market_open", "market_close"]]]

            current_time_mock.time.side_effect = [
                posix_time,  # during trading day
                posix_time + 8 * 60 * 60,  # 8 hours later--after trading day
                1608908400,  # Christmas 2020, Friday, 11am in NYC. We want to verify that we're accounting for holidays
                start_day - 1,  # one second before trading day
                (start_day + end_day) / 2,  # right in the middle of trading day
                end_day + 1  # one second after trading day
            ]

            self.assertTrue(during_trading_day())
            self.assertFalse(during_trading_day())
            self.assertFalse(during_trading_day())
            self.assertFalse(during_trading_day())
            self.assertTrue(during_trading_day())
            self.assertFalse(during_trading_day())

        # Finally, just double-check that the real-time, default invocation works as expected
        posix_now = time.time()
        nyc_now = posix_to_datetime(posix_now)
        schedule = nyse.schedule(nyc_now, nyc_now)
        during_trading = False
        if not schedule.empty:
            start_day, end_day = [datetime_to_posix(x) for x in schedule.iloc[0][["market_open", "market_close"]]]
            during_trading = start_day <= posix_now <= end_day

        # FYI: there is a non-zero chance that this test will fail at exactly the beginning or end of a trading day
        self.assertEqual(during_trading, during_trading_day())

    def test_schedule_handlers(self):
        """These test functions that live in logic.stock_data, but are used when processing orders during game play
        """
        sat_may_23_2020 = dt(2020, 5, 23)
        next_trading_schedule = get_next_trading_day_schedule(sat_may_23_2020)
        start_and_end = get_schedule_start_and_end(next_trading_schedule)
        start_day, end_day = [posix_to_datetime(x) for x in start_and_end]
        localizer = pytz.timezone(TIMEZONE)
        expected_start = localizer.localize(dt(2020, 5, 26, 9, 30))
        expected_end = localizer.localize(dt(2020, 5, 26, 16, 0))
        self.assertEqual(start_day, expected_start)
        self.assertEqual(end_day, expected_end)

    def test_get_symbols(self):
        """For now we pull data from IEX cloud. We also scrape their daily published listing of available symbols to
        build the selection inventory for the frontend. Although the core data source will change in the future, these
        operations need to remain intact.
        """
        symbols_table = get_symbols_table(3)
        self.assertEqual(symbols_table.shape, (3, 2))
        self.assertEqual(symbols_table.iloc[0]["symbol"][0], 'A')

    @patch('backend.logic.stock_data.time')
    def test_price_fetchers(self, current_time_mock):
        symbol = "AMZN"
        amzn_price, updated_at = fetch_iex_price(symbol)
        self.assertIsNotNone(amzn_price)
        self.assertTrue(amzn_price > 0)
        self.assertTrue(posix_to_datetime(updated_at) > dt(2000, 1, 1).replace(tzinfo=pytz.utc))

        # As above, mock in the current time values that we want to test for. Here each test value need to be
        # duplicated since time.time() gets called inside during_trading_day and then again in fetch_end_of_day_cache
        # -----------------------------------------------------------------------------------------------------------
        amzn_test_price = 2000
        off_hours_time = 1590192953
        end_of_trade_time = 1590177600

        current_time_mock.time.side_effect = [
            off_hours_time,  # Same-day look-up against a valid cache
            off_hours_time,
            off_hours_time + 5 * 24 * 60 * 60,  # Look-up much later than the last cached entry
            off_hours_time + 5 * 24 * 60 * 60,
            off_hours_time,  # back to the same-day look-up, but we'll reset the cache to earlier in the day
            off_hours_time
        ]

        rds.set(symbol, f"{amzn_test_price}_{end_of_trade_time - 30}")
        cache_price, cache_time = fetch_end_of_day_cache(symbol)
        self.assertEqual(amzn_test_price, cache_price)
        self.assertEqual(end_of_trade_time - 30, cache_time)

        # time cache is inspected is a long way ahead of when the cache was last updated...
        null_result, _ = fetch_end_of_day_cache(symbol)
        self.assertIsNone(null_result)

        # cache isn't current as of the last minute of trading day
        rds.set(symbol, f"{amzn_test_price}_{end_of_trade_time - 61}")
        null_result, _ = fetch_end_of_day_cache(symbol)
        self.assertIsNone(null_result)
