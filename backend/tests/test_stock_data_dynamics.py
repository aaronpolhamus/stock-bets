from datetime import datetime as dt
import time
import unittest
from unittest.mock import patch

import pytz

from backend.logic.base import (
    get_trading_calendar,
    posix_to_datetime,
    during_trading_day,
    datetime_to_posix,
    get_schedule_start_and_end,
    get_next_trading_day_schedule,
    TIMEZONE
)
from backend.logic.base import fetch_price


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
        with patch('backend.logic.base.time') as current_time_mock:
            # Check during trading day just one second before and after open/close
            schedule = get_trading_calendar(actual_date, actual_date)
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
        schedule = get_trading_calendar(nyc_now, nyc_now)
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

    def test_price_fetchers(self):
        symbol = "AMZN"
        amzn_price, updated_at = fetch_price(symbol)
        self.assertIsNotNone(amzn_price)
        self.assertTrue(amzn_price > 0)
        self.assertTrue(posix_to_datetime(updated_at) > dt(2000, 1, 1).replace(tzinfo=pytz.utc))
