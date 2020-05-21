from backend.tests import BaseTestCase
from backend.logic.games import (
    make_random_game_title,
    get_current_game_cash_balance,
    get_current_stock_holding,
    stop_limit_qc,
    qc_sell_order,
    qc_buy_order,
    get_order_price,
    get_order_quantity,
    get_all_open_orders
)


class TestGameLogic(BaseTestCase):
    """The purpose of these tests is to verify the integrity of the logic that we use to manage the mechanics of
    creating and playing games. In celery/integration tests, we'll mock these internals, but here the purpose is to
    make sure that they behave as expected at a base level. We'll also test the demo game data. If the game gets updated
    in the future we expect these tests to break--that's fine, as long as they're appropriately updated.
    """

    def test_game_logic(self):
        random_title = make_random_game_title()
        self.assertEqual(len(random_title.split(" ")), 2)
