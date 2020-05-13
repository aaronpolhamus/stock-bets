"""Logic for creating games and storing default parameters
"""

from funkybob import RandomNameGenerator

from backend.database.models import (
    GameModes,
    Benchmarks,
    SideBetPeriods,
    OrderTypes,
    BuyOrSell,
    TimeInForce)
from backend.database.helpers import unpack_enumerated_field_mappings

# Default make game settings
# --------------------------
DEFAULT_GAME_MODE = "return_weighted"
DEFAULT_GAME_DURATION = 30  # days
DEFAULT_BUYIN = 100  # dolllars
DEFAULT_REBUYS = 0  # How many rebuys are allowed
DEFAULT_BENCHMARK = "return_ratio"
DEFAULT_SIDEBET_PERCENT = 0
DEFAULT_SIDEBET_PERIOD = "weekly"
DEFAULT_INVITE_OPEN_WINDOW = 48  # Default number of hours that we'll allow a game to stay open for

"""Quick note about implementation here: The function unpack_enumerated_field_mappings extracts the natural language
label of each integer entry for the DB and send that value: label mapping to the frontend as a dictionary (or Object) 
in javascript. We handle value-label mapping concerns on the frontend.
"""
GAME_MODES = unpack_enumerated_field_mappings(GameModes)
BENCHMARKS = unpack_enumerated_field_mappings(Benchmarks)
SIDE_BET_PERIODS = unpack_enumerated_field_mappings(SideBetPeriods)


# Default play game settings
# --------------------------
ORDER_TYPES = unpack_enumerated_field_mappings(OrderTypes)
TIME_IN_FORCE = unpack_enumerated_field_mappings(TimeInForce)


# Define a couple different helper functions
# ------------------------------------------
def make_random_game_title():
    title_iterator = iter(RandomNameGenerator())
    return next(title_iterator).replace("_", " ")  # TODO: Enforce uniqueness at some point here
