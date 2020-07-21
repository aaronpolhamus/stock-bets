from unittest import TestCase

from backend.database.helpers import unpack_enumerated_field_mappings
from backend.database.models import (
    Benchmarks,
    SideBetPeriods
)
from backend.logic.games import (
    DEFAULT_GAME_DURATION,
    DEFAULT_BUYIN,
    DEFAULT_BENCHMARK,
    DEFAULT_SIDEBET_PERCENT,
    DEFAULT_SIDEBET_PERIOD,
    DEFAULT_INVITE_OPEN_WINDOW,
    TIME_TO_SHOW_FINISHED_GAMES
)
from backend.tasks.redis import DEFAULT_ASSET_EXPIRATION


class TestDefaults(TestCase):
    """The purpose of these tests is to ensure that every time we set a default for an enumerated field that it belongs
    to the set of valid options. If it's a free value, we'll test those here, too.
    """

    def test_make_game_defaults(self):
        benchmark_mappings = unpack_enumerated_field_mappings(Benchmarks)
        self.assertIn(DEFAULT_BENCHMARK, benchmark_mappings.keys())

        sidebet_period_mappings = unpack_enumerated_field_mappings(SideBetPeriods)
        self.assertIn(DEFAULT_SIDEBET_PERIOD, sidebet_period_mappings.keys())

        self.assertEqual(DEFAULT_GAME_DURATION, 30)
        self.assertEqual(DEFAULT_BUYIN, 100)
        self.assertEqual(DEFAULT_SIDEBET_PERCENT, 0)
        self.assertEqual(DEFAULT_INVITE_OPEN_WINDOW, 2)

    def test_defaults(self):
        # this ensures that users will continue to be able to see recently expired game data, even after it is no
        # longer being active serviced by the platform
        self.assertGreater(DEFAULT_ASSET_EXPIRATION, TIME_TO_SHOW_FINISHED_GAMES)
