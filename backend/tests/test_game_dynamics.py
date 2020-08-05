"""Bundles tests relating to games, including celery task tests
"""
import json
import time
import unittest
from datetime import datetime as dt
from unittest import TestCase
from unittest.mock import patch

import numpy as np
import pandas as pd
from backend.database.fixtures.mock_data import (
    simulation_start_time,
    simulation_end_time
)
from backend.database.helpers import query_to_dict
from backend.logic.auth import (
    make_user_entry_from_google,
    register_user,
    register_username_with_token
)
from backend.logic.base import (
    get_user_ids_from_passed_emails,
    get_user_ids,
    get_pending_buy_order_value,
    get_all_active_symbols
)
from backend.logic.games import (
    get_invite_list_by_status,
    add_game,
    get_game_ids_by_status,
    get_game_info_for_user,
    expire_finished_game,
    suggest_symbols,
    process_order,
    execute_order,
    make_random_game_title,
    get_current_game_cash_balance,
    get_current_stock_holding,
    get_all_current_stock_holdings,
    stop_limit_qc,
    qc_buy_order,
    qc_sell_order,
    get_order_price,
    get_order_quantity,
    get_all_open_orders,
    place_order,
    get_open_game_ids_past_window,
    service_open_game,
    InsufficientFunds,
    InsufficientHoldings,
    LimitError,
    NoNegativeOrders,
    DEFAULT_VIRTUAL_CASH,
    DEFAULT_INVITE_OPEN_WINDOW,
    add_user_via_email,
    add_user_via_platform,
    respond_to_game_invite,
    get_external_invite_list_by_status,
    init_game_assets
)
from backend.logic.schemas import (
    balances_chart_schema,
    apply_validation,
    FailedValidation
)
from backend.logic.visuals import (
    FIELD_CHART_PREFIX,
    init_order_details)
from backend.tasks.redis import unpack_redis_json
from backend.tests import BaseTestCase


class TestGameLogic(BaseTestCase):
    """The purpose of these tests is to verify the integrity of the logic that we use to manage the mechanics of
    creating and playing games. In celery/integration tests, we'll mock these internals, but here the purpose is to
    make sure that they behave as expected at a base level. We'll also test the demo game data. If the game gets updated
    in the future we expect these tests to break--that's fine, as long as they're appropriately updated.
    """

    def test_mock_game_logic(self):
        random_title = make_random_game_title()
        self.assertEqual(len(random_title.split(" ")), 2)

        # Tests related to inspecting game data using test case
        test_user_id = 1
        game_id = 3
        # TODO: Bring this test back at some point -- for now it fails because how we spin the mock data up has baked-
        # in variation on time
        # test_user_cash = get_current_game_cash_balance(test_user_id, game_id)
        # self.assertAlmostEqual(test_user_cash, 14037.0190, 3)

        expctd = {
            "AMZN": 6,
            "TSLA": 35,
            "LYFT": 700,
            "SPXU": 1200,
            "NVDA": 8
        }

        test_amzn_holding = get_current_stock_holding(test_user_id, game_id, "AMZN")
        self.assertEqual(test_amzn_holding, expctd["AMZN"])
        test_tsla_holding = get_current_stock_holding(test_user_id, game_id, "TSLA")
        self.assertEqual(test_tsla_holding, expctd["TSLA"])
        test_lyft_holding = get_current_stock_holding(test_user_id, game_id, "LYFT")
        self.assertEqual(test_lyft_holding, expctd["LYFT"])
        test_spxu_holding = get_current_stock_holding(test_user_id, game_id, "SPXU")
        self.assertEqual(test_spxu_holding, expctd["SPXU"])
        test_nvda_holding = get_current_stock_holding(test_user_id, game_id, "NVDA")
        self.assertEqual(test_nvda_holding, expctd["NVDA"])
        test_jpm_holding = get_current_stock_holding(test_user_id, game_id, "JPM")
        self.assertEqual(test_jpm_holding, 0)

        all_test_user_holdings = get_all_current_stock_holdings(test_user_id, game_id)
        self.assertEqual(len(all_test_user_holdings), len(expctd))
        for stock, holding in all_test_user_holdings.items():
            self.assertEqual(expctd[stock], holding)

        # For now game_id #3 is the only mocked game that has orders, but this should capture all open orders for
        # all games on the platform
        expected = [9, 10, 13, 14]
        all_open_orders = get_all_open_orders()
        self.assertEqual(len(expected), len(all_open_orders))

        with self.engine.connect() as conn:
            res = conn.execute(f"""
                SELECT symbol FROM orders WHERE id IN ({",".join(['%s'] * len(expected))})
            """, expected)

        stocks = [x[0] for x in res]
        self.assertEqual(stocks, ["MELI", "SPXU", "SQQQ", "SPXU"])

    def test_game_management(self):
        """Tests of functions associated with starting, joining, and updating games
        """
        # Quick active symbols test
        active_symbols = set(get_all_active_symbols())
        expected_symbols = {
            "AMZN",
            "LYFT",
            "TSLA",
            "SPXU",
            "NVDA",
            "NKE",
            "MELI",
            "BABA"
        }
        self.assertEqual(active_symbols, expected_symbols)

        game_id = 1
        open_game_ids = get_open_game_ids_past_window()
        self.assertEqual(open_game_ids, [1, 2, 5])

        service_open_game(game_id)
        game_status_entry = \
            query_to_dict("SELECT * FROM game_status WHERE game_id = %s AND status = 'active'", game_id)[0]

        self.assertEqual(json.loads(game_status_entry["users"]), [4, 3])

        with self.engine.connect() as conn:
            result = conn.execute("SELECT status FROM game_invites WHERE user_id = 5 AND game_id = 1;").fetchall()
            status_entries = [x[0] for x in result]
            self.assertEqual(status_entries, ["invited", "expired"])

            df = pd.read_sql(
                "SELECT * FROM game_balances WHERE game_id = %s and balance_type = 'virtual_cash'", conn,
                params=str(game_id))
            self.assertEqual(df.shape, (2, 8))
            self.assertEqual(df["user_id"].to_list(), [4, 3])
            self.assertEqual(df["balance"].to_list(), [DEFAULT_VIRTUAL_CASH, DEFAULT_VIRTUAL_CASH])

        game_id = 2
        service_open_game(game_id)
        gs_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s and status = 'expired'", game_id)[0]

        self.assertEqual(json.loads(gs_entry["users"]), [1, 3])

        with self.engine.connect() as conn:
            df = pd.read_sql("SELECT * FROM game_invites WHERE game_id = %s", conn, params=str(game_id))
            self.assertEqual(df[df["user_id"] == 3]["status"].to_list(), ["joined", "expired"])
            self.assertEqual(df[df["user_id"] == 1]["status"].to_list(), ["invited", "declined"])

            df = pd.read_sql(
                "SELECT * FROM game_balances WHERE game_id = %s and balance_type = 'virtual_cash'", conn,
                params=str(game_id))
            self.assertTrue(df.empty)

        # similar setup for mock buy and sell orders as above, but this time setup to be valid from the get-go
        with patch("backend.logic.base.time") as base_time_mock:
            base_time_mock.time.side_effect = [
                1590516744,
                1590516744,
                1590516744,
                1590516744
            ]

            user_id = 1
            game_id = 3
            buy_stock = "MELI"
            mock_buy_order = {"amount": 1,
                              "buy_or_sell": "buy",
                              "game_id": 3,
                              "order_type": "market",
                              "market_price": 823.35,
                              "quantity_type": "Shares",
                              "symbol": buy_stock,
                              "time_in_force": "until_cancelled",
                              "title": "test game"}

            current_cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, buy_stock)
            place_order(user_id,
                        game_id,
                        mock_buy_order["symbol"],
                        mock_buy_order["buy_or_sell"],
                        current_cash_balance,
                        current_holding,
                        mock_buy_order["order_type"],
                        mock_buy_order["quantity_type"],
                        mock_buy_order["market_price"],
                        mock_buy_order["amount"],
                        mock_buy_order["time_in_force"])

            new_cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, buy_stock)
            self.assertAlmostEqual(new_cash_balance, current_cash_balance - mock_buy_order["market_price"], 2)
            self.assertEqual(current_holding, mock_buy_order["amount"])

        with patch("backend.logic.games.time") as game_time_mock, patch(
                "backend.logic.base.time") as base_time_mock:
            game_time_mock.time.side_effect = [
                1590516744,
                1590516744
            ]
            base_time_mock.time.side_effect = [
                1590516744,
                1590516744
            ]

            sell_stock = "AMZN"
            mock_sell_order = {"amount": 1,
                               "buy_or_sell": "sell",
                               "game_id": 3,
                               "order_type": "market",
                               "market_price": 2_436.88,
                               "quantity_type": "Shares",
                               "symbol": sell_stock,
                               "time_in_force": "until_cancelled",
                               "title": "test game"}

            current_cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, buy_stock)
            place_order(user_id,
                        game_id,
                        mock_sell_order["symbol"],
                        mock_sell_order["buy_or_sell"],
                        current_cash_balance,
                        current_holding,
                        mock_sell_order["order_type"],
                        mock_sell_order["quantity_type"],
                        mock_sell_order["market_price"],
                        mock_sell_order["amount"],
                        mock_sell_order["time_in_force"])

            new_cash_balance = get_current_game_cash_balance(user_id, game_id)
            current_holding = get_current_stock_holding(user_id, game_id, buy_stock)
            self.assertAlmostEqual(new_cash_balance, current_cash_balance + mock_sell_order["market_price"], 2)
            self.assertEqual(current_holding, mock_sell_order["amount"])

            # no negative orders tests
            with self.assertRaises(NoNegativeOrders):
                place_order(user_id,
                            game_id,
                            mock_sell_order["symbol"],
                            mock_sell_order["buy_or_sell"],
                            current_cash_balance,
                            current_holding,
                            mock_sell_order["order_type"],
                            mock_sell_order["quantity_type"],
                            mock_sell_order["market_price"],
                            -10,
                            mock_sell_order["time_in_force"])

    def test_cash_balance_and_buying_power(self):
        """Here we have pre-staged orders for MELI from the mock data, and we'll add one for NVDA. We exect to see
        outstanding buy order value being the sum of the  MELI order + the value of the new NVDA order
        """
        user_id = 1
        game_id = 3
        buy_stock = "NVDA"
        market_price = 1_000

        current_cash_balance = get_current_game_cash_balance(user_id, game_id)
        current_holding = get_current_stock_holding(user_id, game_id, buy_stock)
        new_order_time = simulation_start_time + 60 * 60 * 12  # after hours
        with patch("backend.logic.games.time") as game_time_mock, patch("backend.logic.base.time") as base_time_mock:
            game_time_mock.time.return_value = base_time_mock.time.return_value = new_order_time
            place_order(user_id,
                        game_id,
                        symbol=buy_stock,
                        buy_or_sell="buy",
                        cash_balance=current_cash_balance,
                        current_holding=current_holding,
                        order_type="market",
                        quantity_type="Shares",
                        market_price=market_price,
                        amount=10,
                        time_in_force="until_cancelled")

        with patch("backend.logic.base.fetch_price") as fetch_price_mock:
            fetch_price_mock.return_value = (market_price, new_order_time)
            buy_order_value = get_pending_buy_order_value(user_id, game_id)

        mock_data_meli_order_id = 9
        meli_ticket = query_to_dict("SELECT * FROM orders WHERE id = %s", mock_data_meli_order_id)[0]

        # This reflects the order price for the 2 shares of MELI + the last market price for the new shares of NVDA
        self.assertAlmostEqual(buy_order_value, meli_ticket["quantity"] * meli_ticket["price"] + 10 * market_price, 1)

    def test_order_form_logic(self):
        # functions for parsing and QC'ing incoming order tickets from the front end. We'll try to raise errors for all
        # the ways that an order ticket can be invalid
        test_user_id = 4
        game_id = 3
        meli_holding = get_current_stock_holding(test_user_id, game_id, "MELI")
        current_cash_balance = get_current_game_cash_balance(test_user_id, game_id)

        self.assertEqual(meli_holding, 107)
        self.assertAlmostEqual(current_cash_balance, 8130.8312, 3)

        mock_buy_order = {"amount": 70,
                          "buy_or_sell": "buy",
                          "game_id": 3,
                          "order_type": "limit",
                          "market_price": 823.35,
                          "quantity_type": "Shares",
                          "stop_limit_price": 800,
                          "symbol": "MELI",
                          "time_in_force": "until_cancelled",
                          "title": "test game"}

        order_price = get_order_price(mock_buy_order["order_type"], mock_buy_order["market_price"],
                                      mock_buy_order["stop_limit_price"])
        self.assertEqual(order_price, 800)
        order_quantity = get_order_quantity(order_price, mock_buy_order["amount"], mock_buy_order["quantity_type"])
        self.assertEqual(order_quantity, 70)
        with self.assertRaises(InsufficientFunds):
            qc_buy_order(
                mock_buy_order["order_type"],
                mock_buy_order["quantity_type"],
                mock_buy_order["stop_limit_price"],
                mock_buy_order["market_price"],
                mock_buy_order["amount"],
                current_cash_balance)

        fake_price = 790
        mock_buy_order["market_price"] = fake_price
        with self.assertRaises(LimitError):
            stop_limit_qc(
                mock_buy_order["buy_or_sell"],
                mock_buy_order["order_type"],
                mock_buy_order["stop_limit_price"],
                fake_price)

        mock_buy_order["amount"] = 10
        with self.assertRaises(LimitError):
            qc_buy_order(
                mock_buy_order["order_type"],
                mock_buy_order["quantity_type"],
                mock_buy_order["stop_limit_price"],
                fake_price,
                mock_buy_order["amount"],
                current_cash_balance)

        # construct a valid ticket with different inputs
        mock_buy_order["market_price"] = 823.35
        mock_buy_order["quantity_type"] = "USD"
        mock_buy_order["amount"] = 4_000
        mock_buy_order["order_type"] = "market"
        order_price = get_order_price(mock_buy_order["order_type"], mock_buy_order["market_price"],
                                      mock_buy_order["stop_limit_price"])
        self.assertEqual(order_price, 823.35)
        order_quantity = get_order_quantity(order_price, mock_buy_order["amount"], mock_buy_order["quantity_type"])
        self.assertEqual(order_quantity, 4)

        self.assertTrue(qc_buy_order(
            mock_buy_order["order_type"],
            mock_buy_order["quantity_type"],
            mock_buy_order["stop_limit_price"],
            mock_buy_order["market_price"],
            mock_buy_order["amount"],
            current_cash_balance))

        # Now raise an insufficient funds error related to cash
        mock_buy_order["amount"] = 100_000
        with self.assertRaises(InsufficientFunds):
            qc_buy_order(
                mock_buy_order["order_type"],
                mock_buy_order["quantity_type"],
                mock_buy_order["stop_limit_price"],
                mock_buy_order["market_price"],
                mock_buy_order["amount"],
                current_cash_balance)

        with self.assertRaises(Exception):
            get_order_price("bad_option", mock_buy_order["market_price"], mock_buy_order["stop_limit_price"])

        mock_buy_order["quantity_type"] = "bad_option"
        with self.assertRaises(Exception):
            get_order_quantity(order_price, mock_buy_order["amount"], mock_buy_order["quantity_type"])

        # Follow a similar permutation to above, but starting with a sell-stop order
        mock_sell_order = {"amount": 170,
                           "buy_or_sell": "sell",
                           "game_id": 3,
                           "order_type": "stop",
                           "market_price": 823.35,
                           "quantity_type": "Shares",
                           "stop_limit_price": 800,
                           "symbol": "MELI",
                           "time_in_force": "until_cancelled",
                           "title": "test game"}

        order_price = get_order_price(mock_sell_order["order_type"], mock_sell_order["market_price"],
                                      mock_sell_order["stop_limit_price"])
        self.assertEqual(order_price, 800)
        order_quantity = get_order_quantity(order_price, mock_sell_order["amount"], mock_sell_order["quantity_type"])
        self.assertEqual(order_quantity, 170)
        with self.assertRaises(InsufficientHoldings):
            qc_sell_order(
                mock_sell_order["order_type"],
                mock_sell_order["quantity_type"],
                mock_sell_order["stop_limit_price"],
                mock_sell_order["market_price"],
                mock_sell_order["amount"],
                meli_holding)

        fake_price = 790
        mock_sell_order["market_price"] = fake_price
        with self.assertRaises(LimitError):
            stop_limit_qc(
                mock_sell_order["buy_or_sell"],
                mock_sell_order["order_type"],
                mock_sell_order["stop_limit_price"],
                fake_price)

        mock_sell_order["amount"] = 10
        with self.assertRaises(LimitError):
            qc_sell_order(
                mock_sell_order["order_type"],
                mock_sell_order["quantity_type"],
                mock_sell_order["stop_limit_price"],
                fake_price,
                mock_sell_order["amount"],
                meli_holding)

        # construct a valid ticket with different inputs
        mock_sell_order["market_price"] = 823.35
        mock_sell_order["quantity_type"] = "USD"
        mock_sell_order["amount"] = 40_000
        mock_sell_order["order_type"] = "market"
        order_price = get_order_price(mock_sell_order["order_type"], mock_sell_order["market_price"],
                                      mock_sell_order["stop_limit_price"])
        self.assertEqual(order_price, 823.35)
        order_quantity = get_order_quantity(order_price, mock_sell_order["amount"], mock_sell_order["quantity_type"])
        self.assertEqual(order_quantity, 48)

        self.assertTrue(qc_sell_order(
            mock_sell_order["order_type"],
            mock_sell_order["quantity_type"],
            mock_sell_order["stop_limit_price"],
            mock_sell_order["market_price"],
            mock_sell_order["amount"],
            meli_holding))

        # Now raise an insufficient funds error related to cash
        mock_sell_order["amount"] = 100_000
        with self.assertRaises(InsufficientHoldings):
            qc_sell_order(
                mock_sell_order["order_type"],
                mock_sell_order["quantity_type"],
                mock_sell_order["stop_limit_price"],
                mock_sell_order["market_price"],
                mock_sell_order["amount"],
                meli_holding)

    def test_order_fulfillment(self):
        """This test goes into the internals of async_process_single_order"""
        user_id = 4
        game_id = 4
        init_order_details(game_id, user_id)
        test_data_array = [(13, 1592573410.15422, "SQQQ", 7.990), (14, 1592573410.71635, "SPXU", 11.305)]
        for order_id, timestamp, symbol, market_price in test_data_array:
            order_ticket = query_to_dict("SELECT * FROM orders WHERE id = %s;", order_id)[0]
            cash_balance = get_current_game_cash_balance(user_id=user_id, game_id=game_id)
            with patch("backend.logic.games.time") as game_time_mock, patch(
                    "backend.logic.games.fetch_price") as fetch_price_mock, patch(
                "backend.logic.base.time") as base_time_mock:
                base_time_mock.time.side_effect = game_time_mock.time.side_effect = [1592573410.15422] * 2
                fetch_price_mock.return_value = (market_price, None)
                process_order(order_id)
                new_cash_balance = get_current_game_cash_balance(user_id=user_id, game_id=game_id)
                self.assertAlmostEqual(new_cash_balance, cash_balance - market_price * order_ticket["quantity"], 3)


class TestRebookMarketOrder(BaseTestCase):

    def test_rebook_market_order(self):
        """A market order's clear price and quantity after hours is calculated based on the previous day's close. In
        some cases the price moves enough that the order is no longer valid. This test behavior to automatically adjust
        the purchase quantity and clear the order"""
        user_id = 1
        game_id = 3
        init_game_assets(game_id)

        symbol = "JPM"
        cash_on_hand = get_current_game_cash_balance(user_id, game_id)
        current_holding = get_current_stock_holding(user_id, game_id, symbol)
        day_1_market_price = 100
        original_order_quantity = cash_on_hand // day_1_market_price
        with patch("backend.logic.base.time") as base_time_mock:
            base_time_mock.time.return_value = 1596485499.580801

            order_id = place_order(
                user_id,
                game_id,
                symbol,
                "buy",
                cash_on_hand,
                current_holding,
                "market",
                "Shares",
                day_1_market_price,
                original_order_quantity,
                "until_cancelled")

        with patch("backend.logic.base.time") as base_time_mock, patch(
                "backend.logic.games.fetch_price") as fetch_price_mock:
            base_time_mock.time.return_value = 1596557499.580801
            mock_price = 150
            fetch_price_mock.return_value = mock_price, 1596557499.580801
            process_order(order_id)

        original_order_status = query_to_dict(
            "SELECT * FROM order_status WHERE order_id = %s ORDER BY id DESC LIMIT 0, 1", order_id)[0]
        self.assertEqual(original_order_status["status"], "cancelled")

        updated_order_status = query_to_dict(
            "SELECT * FROM order_status WHERE order_id = %s ORDER BY id DESC LIMIT 0, 1", order_id + 1)[0]
        self.assertEqual(updated_order_status["status"], "fulfilled")

        updated_order_ticket = query_to_dict("SELECT * FROM orders WHERE id = %s;", order_id + 1)[0]
        self.assertEqual(updated_order_ticket["quantity"], cash_on_hand // mock_price)


class TestOrderLogic(unittest.TestCase):

    def test_order_execution_logic(self):
        """After an order has been placed, there's a really important function, execute_order, that determines whether
        that order is subsequently fulfilled. We'll test different permutations of that here.
        """

        # ------------- #
        # market orders #
        # ------------- #

        # market order to buy, enough cash
        self.assertTrue(execute_order(buy_or_sell="buy",
                                      order_type="market",
                                      market_price=100,
                                      order_price=100,
                                      cash_balance=200,
                                      current_holding=0,
                                      quantity=1))

        # market order to buy, not enough cash
        self.assertFalse(execute_order(buy_or_sell="buy",
                                       order_type="market",
                                       market_price=100,
                                       order_price=100,
                                       cash_balance=50,
                                       current_holding=0,
                                       quantity=1))

        # ----------------------------------------- #
        # market price clears stop and limit orders #
        # ----------------------------------------- #

        # limit order to buy, enough cash
        self.assertTrue(execute_order(buy_or_sell="buy",
                                      order_type="limit",
                                      market_price=50,
                                      order_price=100,
                                      cash_balance=200,
                                      current_holding=0,
                                      quantity=1))

        # limit order to buy, not enough cash
        self.assertFalse(execute_order(buy_or_sell="buy",
                                       order_type="limit",
                                       market_price=50,
                                       order_price=100,
                                       cash_balance=25,
                                       current_holding=0,
                                       quantity=1))

        # stop order to buy, enough cash
        self.assertTrue(execute_order(buy_or_sell="buy",
                                      order_type="stop",
                                      market_price=150,
                                      order_price=100,
                                      cash_balance=200,
                                      current_holding=0,
                                      quantity=1))

        # stop order to buy, not enough cash
        self.assertFalse(execute_order(buy_or_sell="buy",
                                       order_type="stop",
                                       market_price=150,
                                       order_price=100,
                                       cash_balance=100,
                                       current_holding=0,
                                       quantity=1))

        # limit order to sell, sufficient holding
        self.assertTrue(execute_order(buy_or_sell="sell",
                                      order_type="limit",
                                      market_price=150,
                                      order_price=100,
                                      cash_balance=200,
                                      current_holding=2,
                                      quantity=1))

        # limit order to sell, insufficient holding
        self.assertFalse(execute_order(buy_or_sell="sell",
                                       order_type="limit",
                                       market_price=150,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=0,
                                       quantity=1))

        # stop order to sell, sufficient holding
        self.assertTrue(execute_order(buy_or_sell="sell",
                                      order_type="stop",
                                      market_price=75,
                                      order_price=100,
                                      cash_balance=200,
                                      current_holding=2,
                                      quantity=1))

        # stop order to sell, insufficient holding
        self.assertFalse(execute_order(buy_or_sell="sell",
                                       order_type="stop",
                                       market_price=75,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=0,
                                       quantity=1))

        # market price doesn't clear order
        # -------------------------------

        # limit order to buy, enough cash
        self.assertFalse(execute_order(buy_or_sell="buy",
                                       order_type="limit",
                                       market_price=150,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=0,
                                       quantity=1))

        # limit order to buy, not enough cash
        self.assertFalse(execute_order(buy_or_sell="buy",
                                       order_type="limit",
                                       market_price=150,
                                       order_price=100,
                                       cash_balance=25,
                                       current_holding=0,
                                       quantity=1))

        # stop order to buy, enough cash
        self.assertFalse(execute_order(buy_or_sell="buy",
                                       order_type="stop",
                                       market_price=50,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=0,
                                       quantity=1))

        # stop order to buy, not enough cash
        self.assertFalse(execute_order(buy_or_sell="buy",
                                       order_type="stop",
                                       market_price=50,
                                       order_price=100,
                                       cash_balance=100,
                                       current_holding=0,
                                       quantity=1))

        # limit order to sell, sufficient holding
        self.assertFalse(execute_order(buy_or_sell="sell",
                                       order_type="limit",
                                       market_price=50,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=2,
                                       quantity=1))

        # limit order to sell, insufficient holding
        self.assertFalse(execute_order(buy_or_sell="sell",
                                       order_type="limit",
                                       market_price=50,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=0,
                                       quantity=1))

        # stop order to sell, sufficient holding
        self.assertFalse(execute_order(buy_or_sell="sell",
                                       order_type="stop",
                                       market_price=175,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=2,
                                       quantity=1))

        # stop order to sell, insufficient holding
        self.assertFalse(execute_order(buy_or_sell="sell",
                                       order_type="stop",
                                       market_price=175,
                                       order_price=100,
                                       cash_balance=200,
                                       current_holding=0,
                                       quantity=1))


class TestSymbolSuggestion(BaseTestCase):

    def test_symbol_suggestion(self):
        game_id = 3
        user_id = 1

        # test buy suggestions
        text = "A"
        buy_or_sell = "buy"
        expected_suggestions = [
            {'symbol': 'T', 'label': 'T (AT&T)', 'dist': 1},
            {'symbol': 'AAPL', 'label': 'AAPL (APPLE)', 'dist': 3},
            {'symbol': 'AMZN', 'label': 'AMZN (AMAZON)', 'dist': 3},
            {'symbol': 'GOOG', 'label': 'GOOG (ALPHABET CLASS C)', 'dist': 4},
            {'symbol': 'GOOGL', 'label': 'GOOGL (ALPHABET CLASS A)', 'dist': 5}]

        result = suggest_symbols(game_id, user_id, text, buy_or_sell)
        self.assertEqual(result, expected_suggestions)

        # test sell suggestions
        text = "A"
        buy_or_sell = "sell"
        expected_suggestions = [{"symbol": "AMZN", "label": "AMZN (AMAZON)", "dist": 3}]
        result = suggest_symbols(game_id, user_id, text, buy_or_sell)
        self.assertEqual(result, expected_suggestions)

        # validate distance metric with Google
        text = "GOOG"
        buy_or_sell = "buy"
        result = suggest_symbols(game_id, user_id, text, buy_or_sell)
        expected_suggestions = [
            {'symbol': 'GOOG', 'label': 'GOOG (ALPHABET CLASS C)', 'dist': 0},
            {'symbol': 'GOOGL', 'label': 'GOOGL (ALPHABET CLASS A)', 'dist': 1}]
        self.assertEqual(result, expected_suggestions)


class TestSchemaValidation(TestCase):

    def test_schema_validators(self):
        # all data is proper
        df = pd.DataFrame(
            dict(symbol=["TSLA", "AMZN", "JETS"], value=[20, 30, 40], label=["Jun 1 9:30", "Jun 2 9:35", "Jun 3 9:40"],
                 timestamp=[dt.now(), dt.now(), dt.now()]))
        result = apply_validation(df, balances_chart_schema)
        self.assertTrue(result)

        # columns are there but data has a bad type
        df = pd.DataFrame(
            dict(symbol=[1, 2, 3], value=["20", "30", "40"], label=["Jun 1 9:30", "Jun 2 9:35", "Jun 3 9:40"],
                 timestamp=[dt.now(), dt.now(), dt.now()]))
        with self.assertRaises(FailedValidation):
            apply_validation(df, balances_chart_schema)

        # a column is missing
        df = pd.DataFrame(
            dict(value=[20, 30, 40], label=["Jun 1 9:30", "Jun 2 9:35", "Jun 3 9:40"],
                 timestamp=[dt.now(), dt.now(), dt.now()]))
        with self.assertRaises(FailedValidation):
            apply_validation(df, balances_chart_schema)

        # test throwing flags for null or missing data when this is not allowed
        df.loc[0, "value"] = None
        with self.assertRaises(FailedValidation):
            apply_validation(df, balances_chart_schema)

        df.loc[0, "value"] = np.nan
        with self.assertRaises(FailedValidation):
            apply_validation(df, balances_chart_schema)

        # strict mode is on, and there is an extra column
        df = pd.DataFrame(
            dict(symbol=["TSLA", "AMZN", "JETS"], value=[20, 30, 40], label=["Jun 1 9:30", "Jun 2 9:35", "Jun 3 9:40"],
                 timestamp=[dt.now(), dt.now(), dt.now()], bad_column=["x", "y", "z"]))
        with self.assertRaises(FailedValidation):
            apply_validation(df, balances_chart_schema, strict=True)


class TestGameExpiration(BaseTestCase):

    def test_game_expiration(self):
        # we have two mock games that are "finished." One has been done for less than a week, and should still be
        # visible to the frontend. The other has been finished for two weeks and should be hidden
        user_id = 1
        visible_game_id = 6
        expired_game_id = 7
        finished_ids = get_game_ids_by_status("finished")
        self.assertEqual(set(finished_ids), {visible_game_id, expired_game_id})
        with patch("backend.logic.base.time") as mock_base_time, patch("backend.logic.games.time") as mock_game_time:
            mock_base_time.time.return_value = mock_game_time.time.return_value = simulation_end_time
            for game_id in finished_ids:
                expire_finished_game(game_id)

        # when we check the game information for our test user, game 6 should be in there, game 7 should not
        game_info = get_game_info_for_user(user_id)
        self.assertEqual(len(game_info), 4)
        active_game = [x for x in game_info if x["game_id"] == 3][0]
        self.assertEqual(active_game["title"], "test game")
        pending_game = [x for x in game_info if x["game_id"] == 5][0]
        self.assertEqual(pending_game["title"], "valiant roset")
        finished_game = [x for x in game_info if x["game_id"] == visible_game_id][0]
        self.assertEqual(finished_game["title"], "finished game to show")
        finished_game = [x for x in game_info if x["game_mode"] == "single_player"][0]
        self.assertEqual(finished_game["title"], "single player test")

        # TODO: tests that if all users cancel the game is also moved to cancelled


class TestExternalInviteFunctionality(BaseTestCase):

    @patch("backend.logic.friends.send_invite_email")
    def test_external_invite_functionality(self, send_invite_email_mock):
        send_invite_email_mock.return_value = True
        creator_id = 1

        # [A] test user makes a new game -- it should include (a) username invites, (b) email invites on platform, (c)
        # email invites not on platform
        # -----------------------------

        game_1_title = "external test game 1"
        game_1_platform_invites = ["jack", "jadis"]
        # (capitalization off on purpose to text matching function against DB
        minion_1_email = "MinIon1@despicable.me"
        external_email_1 = "externaluser@example.com"
        game_1_email_invites = [minion_1_email, external_email_1]
        add_game(
            creator_id=creator_id,
            title=game_1_title,
            game_mode="multi_player",
            duration=90,
            benchmark="return_ratio",
            buy_in=100,
            side_bets_perc=0,
            side_bets_period="weekly",
            invitees=game_1_platform_invites,
            invite_window=DEFAULT_INVITE_OPEN_WINDOW,
            email_invitees=game_1_email_invites
        )
        with self.engine.connect() as conn:
            game_1_id = conn.execute("SELECT id FROM games WHERE title = %s;", game_1_title).fetchone()[0]

        # platform invites follow regular invite flow
        game_1_invites = query_to_dict("SELECT * FROM game_invites WHERE game_id = %s", game_1_id)
        self.assertEqual(len(game_1_invites),
                         4)  # creator, two platform invites, one external invite linked to platform
        for entry in game_1_invites:
            if entry["user_id"] == creator_id:
                self.assertEqual(entry["status"], "joined")
                continue
            self.assertEqual(entry["status"], "invited")

        # explicitly check to confirm that the minion user is in there
        invited_user_ids_initial = get_invite_list_by_status(game_1_id, "invited")
        minion1_user_id = get_user_ids(["minion1"])[0]
        self.assertIn(minion1_user_id, invited_user_ids_initial)

        # email invites w platform users match email and follow regular flow, but also update the external invites table
        external_email_invites_1 = query_to_dict("SELECT * FROM external_invites WHERE game_id = %s;", game_1_id)
        minion_invites = [x for x in external_email_invites_1 if x["invited_email"] == minion_1_email]
        self.assertEqual(len(minion_invites), 1)
        self.assertEqual(minion_invites[0]["status"], "invited")
        self.assertEqual(minion_invites[0]["game_id"], game_1_id)
        self.assertEqual(minion_invites[0]["requester_id"], creator_id)

        # matched users' platform IDs are also included in the game_status users field
        game_1_status = query_to_dict("""SELECT * FROM game_status 
            WHERE game_id = %s AND status = 'pending';""", game_1_id)[0]
        game_1_invited_users_start = json.loads(game_1_status["users"])
        self.assertIn(minion1_user_id, game_1_invited_users_start)

        # email to users not on platform generates external game invite and platform invite.
        external_user_invites = query_to_dict("SELECT * FROM external_invites WHERE invited_email = %s",
                                              external_email_1)
        self.assertEqual(len(external_user_invites), 2)
        for invite_entry in external_user_invites:
            if invite_entry["type"] == "platform":
                self.assertTrue(np.isnan(invite_entry["game_id"]))

            if invite_entry["type"] == "game":
                self.assertEqual(invite_entry["game_id"], game_1_id)

            self.assertEqual(invite_entry["requester_id"], creator_id)

        registered_user_invite = query_to_dict("SELECT * FROM external_invites WHERE invited_email = %s",
                                               minion_1_email)
        self.assertEqual(len(registered_user_invite), 1)
        self.assertEqual(registered_user_invite[0]["game_id"], game_1_id)

        # create a second test game. an additional new game invite to the same user generates another external invite
        # entry, but _not_ an additional platform entry
        game_2_title = "external test game 2"
        game_2_platform_invites = ["jack", "jadis"]
        game_2_email_invites = [minion_1_email, external_email_1]
        add_game(
            creator_id=creator_id,
            title=game_2_title,
            game_mode="multi_player",
            duration=90,
            benchmark="return_ratio",
            buy_in=100,
            side_bets_perc=0,
            side_bets_period="weekly",
            invitees=game_2_platform_invites,
            invite_window=DEFAULT_INVITE_OPEN_WINDOW,
            email_invitees=game_2_email_invites
        )
        with self.engine.connect() as conn:
            game_2_id = conn.execute("SELECT id FROM games WHERE title = %s;", game_2_title).fetchone()[0]

        external_invite_entries_2 = query_to_dict("SELECT * FROM external_invites WHERE invited_email = %s;",
                                                  external_email_1)
        self.assertEqual(len(external_invite_entries_2), 3)
        self.assertEqual(len([x for x in external_invite_entries_2 if x["type"] == "platform"]), 1)
        self.assertEqual(len([x for x in external_invite_entries_2 if x["type"] == "game"]), 2)

        # [B] after creating the game the host wants to invite additional users. they invite the same three groups above
        # ----------------------------------------------------------------------------------------------------------
        minion_1_id = get_user_ids(["minion1"])[0]
        minion_2_id = get_user_ids(["minion2"])[0]
        minion_2_email = "minion2@despicable.me"
        second_external_user = "externaluser2@example.com"

        add_user_via_platform(game_1_id, minion_1_id)
        add_user_via_email(game_1_id, creator_id, minion_2_email)
        add_user_via_email(game_1_id, creator_id, second_external_user)

        # platform invites implement standard invite flow and create an updated entry for the game status table
        minion_1_invite_entry = query_to_dict("SELECT * FROM game_invites WHERE user_id = %s AND game_id = %s",
                                              minion_1_id, game_1_id)
        self.assertEqual(len(minion_1_invite_entry), 1)  # there shouldn't be a second entry for minion 1

        # email invites to current users create an external invite entry, match the internal ID, and implement standard
        # invite flow
        minion_2_invite_entry = query_to_dict("SELECT * FROM game_invites WHERE user_id = %s", minion_2_id)[0]
        self.assertEqual(minion_2_invite_entry["status"], "invited")

        minion_2_external_entry = query_to_dict("SELECT * FROM external_invites WHERE invited_email = %s",
                                                minion_2_email)
        self.assertEqual(len(minion_2_external_entry), 1)
        self.assertEqual(minion_2_external_entry[0]["game_id"], game_1_id)
        self.assertEqual(minion_2_external_entry[0]["type"], "game")
        self.assertEqual(minion_2_external_entry[0]["requester_id"], creator_id)

        invited_user_ids_updated = get_invite_list_by_status(game_1_id, "invited")
        self.assertEqual(set(invited_user_ids_initial + [minion_1_id, minion_2_id]), set(invited_user_ids_updated))

        # we've sent a bunch of email invites out at this point. we should have 8 external registries in total:
        # external user #1: 2 game invites and 1 platform invite
        # external user #2: 1 game invite and 1 platform invite
        # minion #1: 2 game invites
        # minion #2: 1 game invite
        external_email_invites_updated = query_to_dict("SELECT * FROM external_invites;")
        self.assertEqual(len(external_email_invites_updated), 8)
        for invite_entry in external_email_invites_updated:
            if invite_entry["type"] == "platform":
                self.assertTrue(np.isnan(invite_entry["game_id"]))

            if invite_entry["type"] == "game":
                self.assertIn(invite_entry["game_id"], [game_1_id, game_2_id])
            self.assertEqual(invite_entry["requester_id"], creator_id)

        # [C/D] we should now have 4 different email invitations to handle  -- 2 who is on the platform currently, and 2
        # who are not
        # ---------------------------------------------------------------------------------------------------------
        with self.engine.connect() as conn:
            starting_game_invite_count = conn.execute("""
                SELECT COUNT(*) FROM game_invites 
                WHERE game_id IN (%s, %s);""", game_1_id, game_2_id).fetchone()[0]
        self.assertEqual(starting_game_invite_count, 9)

        # jack, jadis, and minion1 will accept their game invite. now we're just waiting on the un-registered user
        jadis_id = get_user_ids(["jadis"])[0]
        jack_id = get_user_ids(["jack"])[0]
        minion_2_user_id = get_user_ids(["minion2"])[0]
        for user_id in [jadis_id, jack_id, minion1_user_id, minion_2_user_id]:
            respond_to_game_invite(game_1_id, user_id, "joined", time.time())

        # test external invite accepted update
        accepted_invite_emails = get_external_invite_list_by_status(game_1_id, "accepted")
        accepted_invite_ids = get_user_ids_from_passed_emails(accepted_invite_emails)
        self.assertEqual({minion1_user_id, minion_2_user_id}, set(accepted_invite_ids))

        # we added functionality to block game starts if there are pending external invites -- check to make sure that
        # is working here
        open_game_ids = get_game_ids_by_status("pending")
        self.assertIn(game_1_id, open_game_ids)

        # external user from [A] has two email game invitations. when they sign in, they'll have two game invitations
        # waiting for them. their platform invitation will register as accepted. the game_invites table will reflect
        # their new entries, and the game_status 'pending' entry will update with their user ids
        with patch("backend.logic.auth.verify_google_oauth") as oauth_response_mock:
            class GoogleOAuthMock:
                status_code = 200

                def __init__(self, email, uuid):
                    self._email = email
                    self._uuid = uuid

                def json(self):
                    return dict(given_name="frederick",
                                email=self._email,
                                picture="not_relevant",
                                username=None,
                                created_at=time.time(),
                                provider="google",
                                resource_uuid=self._uuid)

            oauth_response_mock.return_value = GoogleOAuthMock(external_email_1, "unique1")
            user_entry, resource_uuid, status_code = make_user_entry_from_google("abc123", "cde456")
            register_user(user_entry)

        with self.engine.connect() as conn:
            updated_game_invite_count = conn.execute("""
                SELECT COUNT(*) FROM game_invites 
                WHERE game_id IN (%s, %s);""", game_1_id, game_2_id).fetchone()[0]
        self.assertEqual(updated_game_invite_count, 15)

        # quick patch to simulate that this user has successfuly picked a username
        with self.engine.connect() as conn:
            user_id = conn.execute("SELECT id FROM users WHERE name = 'frederick';").fetchone()[0]
        register_username_with_token(user_id, external_email_1, "frederick")
        external_example_user_id = get_user_ids(["frederick"])[0]

        # they'll accept the first game invitation, updating the external_invites  and game_invites table and kicking
        # off the game
        respond_to_game_invite(game_1_id, external_example_user_id, "joined", time.time())

        # finally, the last external user will join the game to kick it off
        with patch("backend.logic.auth.verify_google_oauth") as oauth_response_mock:
            class GoogleOAuthMock(object):
                status_code = 200

                def __init__(self, email, uuid):
                    self._email = email
                    self._uuid = uuid

                def json(self):
                    return dict(given_name="frederick2",
                                email=self._email,
                                picture="not_relevant",
                                username=None,
                                created_at=time.time(),
                                provider="google",
                                resource_uuid=self._uuid)

            oauth_response_mock.return_value = GoogleOAuthMock(second_external_user, "unique2")
            user_entry, resource_uuid, status_code = make_user_entry_from_google("fgh789", "ijk101")
            register_user(user_entry)

        # quick patch to simulate that this user has successfuly picked a username
        with self.engine.connect() as conn:
            user_id = conn.execute("SELECT id FROM users WHERE name = 'frederick2';").fetchone()[0]
        register_username_with_token(user_id, external_email_1, "frederick2")
        external_example_user_id2 = get_user_ids(["frederick2"])[0]
        respond_to_game_invite(game_1_id, external_example_user_id2, "joined", time.time())

        field_chart = unpack_redis_json(f"{FIELD_CHART_PREFIX}_{game_1_id}")
        players = [x["label"] for x in field_chart["datasets"]]
        self.assertEqual(set(players), {'cheetos', 'jack', 'jadis', 'minion1', 'minion2', 'frederick', 'frederick2'})

        # in a separate API test write logic for catching bad emails
        # with self.assertRaises(Exception):
        #     send_invite_email(creator_id, "BADEMAILTHATSHOULDFAIL", email_type="platform")
