import unittest

from backend.database.helpers import unpack_enumerated_field_mappings
from backend.database.models import (
    GameModes,
    Benchmarks,
    SideBetPeriods
)
from backend.logic.games import (
    DEFAULT_GAME_MODE,
    DEFAULT_GAME_DURATION,
    DEFAULT_BUYIN,
    DEFAULT_REBUYS,
    DEFAULT_BENCHMARK,
    DEFAULT_SIDEBET_PERCENT,
    DEFAULT_SIDEBET_PERIOD,
    DEFAULT_INVITE_OPEN_WINDOW
)


class TestDefaults(unittest.TestCase):
    """The purpose of these tests is to ensure that every time we set a default for an enumerated field that it belongs
    to the set of valid options. If it's a free value, we'll test those here, too.
    """

    def test_make_game_defaults(self):
        modes_mappings = unpack_enumerated_field_mappings(GameModes)
        self.assertIn(DEFAULT_GAME_MODE, modes_mappings.keys())

        benchmark_mappings = unpack_enumerated_field_mappings(Benchmarks)
        self.assertIn(DEFAULT_BENCHMARK, benchmark_mappings.keys())

        sidebet_period_mappings = unpack_enumerated_field_mappings(SideBetPeriods)
        self.assertIn(DEFAULT_SIDEBET_PERIOD, sidebet_period_mappings.keys())

        self.assertEqual(DEFAULT_GAME_DURATION, 30)
        self.assertEqual(DEFAULT_BUYIN, 100)
        self.assertEqual(DEFAULT_REBUYS, 0)
        self.assertEqual(DEFAULT_SIDEBET_PERCENT, 0)
        self.assertEqual(DEFAULT_INVITE_OPEN_WINDOW, 48 * 60 * 60)
