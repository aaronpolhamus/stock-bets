"""Logic for creating games and storing default parameters
"""

from funkybob import RandomNameGenerator

from backend.database.models import GameModes, Benchmarks, SideBetPeriods


# frontend defaults
# -----------------
DEFAULT_GAME_MODE = "Return-weighted"
DEFAULT_GAME_DURATION = 20  # days
DEFAULT_BUYIN = 100  # dolllars
DEFAULT_REBUYS = 0  # How many rebuys are allowed
DEFAULT_BENCHMARK = "Simple return"
DEFAULT_SIDEBET_PERCENT = 0
DEFAULT_SIDEBET_PERIOD = "Monthly"


# defaults based on unpacking enumerated options from data model
# --------------------------------------------------------------
def unpack_enumerated_field_mappings(table_class):
    """This function unpacks the natural language descriptions of each enumerated field so that these can be passed
    to the frontend
    """
    return {x[1].value[0]: x[1].value[1] for x in table_class.__members__.items()}


GAME_MODES = unpack_enumerated_field_mappings(GameModes)
BENCHMARKS = unpack_enumerated_field_mappings(Benchmarks)
SIDE_BET_PERIODS = unpack_enumerated_field_mappings(SideBetPeriods)


# Define a couple different helper functions
# ------------------------------------------
def make_random_game_title():
    title_iterator = iter(RandomNameGenerator())
    return next(title_iterator).replace("_", " ")  # TODO: Enforce uniqueness at some point here
