"""Canonical test cases based on real production data. As appropriate, migrate cases in from production.
"""
from backend.tests import CanonicalSplitsCase

from backend.logic.visuals import make_order_performance_table


class TestSplits(CanonicalSplitsCase):
    """Stock splits introduce a lot of complexity into the order performance charting and calculating realized /
    unrealized P & L. This canonical test makes sure that we're nailing that  logic, and also does some values testing
    of the asset """
    def test_splits(self):
        make_order_performance_table(self.game_id, self.user_id)
