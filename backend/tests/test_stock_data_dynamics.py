import time
import unittest
from datetime import datetime as dt
from unittest.mock import patch

import pandas as pd
import pytz
from backend.database.fixtures.mock_data import simulation_end_time
from backend.logic.base import (
    get_active_balances,
    get_trading_calendar,
    posix_to_datetime,
    during_trading_day,
    datetime_to_posix,
    get_schedule_start_and_end,
    get_next_trading_day_schedule,
    TIMEZONE,
    get_current_game_cash_balance
)
from backend.logic.stock_data import (
    fetch_price,
    get_stock_splits,
    apply_stock_splits,
    get_most_recent_prices, parse_dividends
)
from backend.tests import BaseTestCase


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

    def test_harvest_stock_splits_external_integration(self):
        """the first part of this test makes sure the external integration works. asserting anything in particular is
        tricky, since the "right" answer depends completely on the day. We prefer to maintain the integration with the
        external resource, rather than to artificially mock it. This test will behave differently on days when there
        are no stock splits for one or more of the targeted resources"""
        get_stock_splits()


class TestStockSplitsInternal(BaseTestCase):

    def test_internal_splits_logic(self):
        """test_harvest_stock_splits_external_integration ensures that our external integration is working. this test
        verifies that once we have splits they are appropriately applied to users balances. we'll cover a straight-
        forward split, a split that leaves fractional shares, and a reverse split that leaves fractional shares"""
        game_id = 3
        user_id = 1
        exec_date = simulation_end_time + 1
        splits = pd.DataFrame([
            {"symbol": "AMZN", "numerator": 5, "denominator": 1, "exec_date": exec_date},
            {"symbol": "TSLA", "numerator": 5, "denominator": 2, "exec_date": exec_date},
            {"symbol": "SPXU", "numerator": 2.22, "denominator": 3.45, "exec_date": exec_date},
        ])
        cash_balance_pre = get_current_game_cash_balance(user_id, game_id)
        balances_pre = get_active_balances(game_id, user_id)
        with patch("backend.logic.stock_data.get_splits") as db_splits_mock:
            db_splits_mock.return_value = splits
            apply_stock_splits()

        cash_balance_post = get_current_game_cash_balance(user_id, game_id)
        balances_post = get_active_balances(game_id, user_id)

        pre_amzn = balances_pre[balances_pre["symbol"] == "AMZN"].iloc[0]["balance"]
        post_amzn = balances_post[balances_post["symbol"] == "AMZN"].iloc[0]["balance"]
        self.assertEqual(pre_amzn * 5 / 1, post_amzn)

        pre_tsla = balances_pre[balances_pre["symbol"] == "TSLA"].iloc[0]["balance"]
        post_tsla = balances_post[balances_post["symbol"] == "TSLA"].iloc[0]["balance"]
        self.assertEqual(pre_tsla * 5 // 2, post_tsla)

        pre_spxu = balances_pre[balances_pre["symbol"] == "SPXU"].iloc[0]["balance"]
        post_spxu = balances_post[balances_post["symbol"] == "SPXU"].iloc[0]["balance"]
        self.assertEqual(pre_spxu * 2.22 // 3.45, post_spxu)

        last_prices = get_most_recent_prices(["AMZN", "TSLA", "SPXU"])
        last_tsla_price = last_prices[last_prices["symbol"] == "TSLA"].iloc[0]["price"]
        last_spxu_price = last_prices[last_prices["symbol"] == "SPXU"].iloc[0]["price"]
        self.assertAlmostEqual(cash_balance_pre + (pre_tsla * 5 / 2 - post_tsla) * last_tsla_price + (
                    pre_spxu * 2.22 / 3.45 - post_spxu) * last_spxu_price, cash_balance_post, 3)


class TestDividendScrapper(BaseTestCase):
    july_7_dividends = pd.DataFrame({'symbol': {0: 'BDN', 1: 'CEA', 2: 'IDCC', 3: 'ROP', 4: 'SCS', 5: 'TGLS'},
                        'company': {0: 'Brandywine Realty Trust',
                                    1: 'China Eastern Airlines Corp. Ltd.',
                                    2: 'InterDigital Inc.',
                                    3: 'Roper Technologies Inc.',
                                    4: 'Steelcase Inc.',
                                    5: 'Tecnoglass Inc.'},
                        'amount': {0: 0.19, 1: 0.32, 2: 0.35, 3: 0.51, 4: 0.1, 5: 0.03},
                        'exec_date': {0: 1594080000,
                                      1: 1594080000,
                                      2: 1594080000,
                                      3: 1594080000,
                                      4: 1594080000,
                                      5: 1594080000}})
    scrapped_july_7 = parse_dividends(dt(2020, 7, 7))

    def test_parse_dividends_data(self):
        self.assertTrue(parse_dividends(dt(2020, 9, 6)).empty)
        pd.testing.assert_frame_equal(self.scrapped_july_7, self.july_7_dividends)
