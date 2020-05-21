from backend.tests import BaseTestCase
from backend.tasks.definitions import (
    update_symbols_table,
    fetch_price,
    cache_price,
    fetch_symbols,
    place_order,
    process_single_order,
    process_open_orders
)


class TestCeleryTasks(BaseTestCase):

    def test_data_tasks(self):
        pass

    def test_game_tasks(self):
        pass
