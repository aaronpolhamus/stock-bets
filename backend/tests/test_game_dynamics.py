"""Bundles tests relating to games, including celery task tests
"""
import json
from unittest.mock import patch

import pandas as pd
from backend.database.helpers import query_to_dict

from backend.logic.games import (
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
    get_open_game_invite_ids,
    service_open_game,
    InsufficientFunds,
    InsufficientHoldings,
    LimitError,
    DEFAULT_VIRTUAL_CASH
)
from logic.base import get_all_active_symbols
from backend.tests import BaseTestCase
from sqlalchemy import select


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
        test_user_cash = get_current_game_cash_balance(test_user_id, game_id)
        self.assertAlmostEqual(test_user_cash, 14037.0190, 3)

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
        expected = [9, 10]
        all_open_orders = get_all_open_orders()
        self.assertEqual(len(expected), len(all_open_orders))

        with self.engine.connect() as conn:
            res = conn.execute(f"""
                SELECT symbol FROM orders WHERE id IN ({",".join(['%s']*len(expected))})
            """)

        stocks = [x[0] for x in res]
        self.assertEqual(stocks, ["MELI", "SPXU"])

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

        mock_buy_order["order_type"] = "bad_option"
        with self.assertRaises(Exception):
            get_order_price(mock_buy_order)

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
        open_game_ids = get_open_game_invite_ids()
        self.assertEqual(open_game_ids, [1, 2, 5])

        service_open_game(game_id)
        game_status_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s AND status = 'active'", game_id)

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
        game_status_entry = query_to_dict("SELECT * FROM game_status WHERE game_id = %s and status = 'expired'")

        self.assertEqual(json.loads(game_status_entry["users"]), [1, 3])

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
