"""For this iteration I'm conflating the definition of our applications database with the Flask-Migrate abstractions
to manage it. I'd like to do something cleaner, once I have a better understanding of what's going on with flake

Check out this structure:
https://stackoverflow.com/questions/56230626/why-is-sqlalchemy-database-uri-set-to-sqlite-memory-when-i-set-it-to-a-pa
"""

from enum import Enum

from backend.database.db import db
from sqlalchemy.schema import Index


class OAuthProviders(Enum):
    google = "Google"
    facebook = "Facebook"
    twitter = "Twitter"
    stockbets = "stockbets"


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, index=True)
    email = db.Column(db.Text, index=True)
    profile_pic = db.Column(db.Text)
    username = db.Column(db.Text, index=True)
    created_at = db.Column(db.Float(precision=32))
    provider = db.Column(db.Enum(OAuthProviders))
    resource_uuid = db.Column(db.Text, index=True)
    password = db.Column(db.Text, nullable=True)


class GameModes(Enum):
    single_player = "single_player"
    multi_player = "multi_player"


class Benchmarks(Enum):
    return_ratio = "Simple return"
    sharpe_ratio = "Sharpe ratio-adjusted"


class SideBetPeriods(Enum):
    weekly = "Weekly"
    monthly = "Monthly"


class Games(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    title = db.Column(db.Text)
    game_mode = db.Column(db.Enum(GameModes))
    duration = db.Column(db.Integer)
    buy_in = db.Column(db.Float(precision=32))
    benchmark = db.Column(db.Enum(Benchmarks))
    side_bets_perc = db.Column(db.Float(precision=32))
    side_bets_period = db.Column(db.Enum(SideBetPeriods))
    invite_window = db.Column(db.Float(precision=32))


class GameStatusTypes(Enum):
    pending = "Pending"
    active = "Active"
    finished = "Finished"
    expired = "Expired"


class GameStatus(db.Model):
    __tablename__ = "game_status"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    status = db.Column(db.Enum(GameStatusTypes))
    users = db.Column(db.JSON)
    timestamp = db.Column(db.Float(precision=32))  # When was the game opened


class GameInviteStatusTypes(Enum):
    invited = "Invited"
    joined = "Joined"
    declined = "Declined"
    expired = "Expired"
    left = "Left"


class GameInvites(db.Model):
    __tablename__ = "game_invites"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.Enum(GameInviteStatusTypes))
    timestamp = db.Column(db.Float(precision=32))


class BuyOrSell(Enum):
    buy = "Buy"
    sell = "Sell"


class OrderTypes(Enum):
    market = "Market"
    limit = "Limit"
    stop = "Stop"


class TimeInForce(Enum):
    day = "Day"
    until_cancelled = "Until Cancelled"


class Orders(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    symbol = db.Column(db.Text)
    buy_or_sell = db.Column(db.Enum(BuyOrSell))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float(precision=32))
    order_type = db.Column(db.Enum(OrderTypes))
    time_in_force = db.Column(db.Enum(TimeInForce))


class OrderStatusTypes(Enum):
    pending = "Pending"
    fulfilled = "Fulfilled"
    cancelled = "Cancelled"
    expired = "Expired"


class Transactions(db.Model):
    __tablename__ = "order_status"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    timestamp = db.Column(db.Float(precision=32))
    status = db.Column(db.Enum(OrderStatusTypes))
    clear_price = db.Column(db.Float(precision=32), nullable=True)


class GameBalanceTypes(Enum):
    virtual_cash = "VirtualCash"
    virtual_stock = "VirtualStock"


class GameBalances(db.Model):
    __tablename__ = "game_balances"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    order_status_id = db.Column(db.Integer, db.ForeignKey("order_status.id"))
    timestamp = db.Column(db.Float(precision=32))
    balance_type = db.Column(db.Enum(GameBalanceTypes))
    balance = db.Column(db.Float(precision=32))
    symbol = db.Column(db.Text)


class Symbols(db.Model):
    """This is less of a formal data model table and more of a data store for available tickers. Thus the handling
    later on in the code is a bit more ad-hoc. Specifically, when pandas updates this table it blows away the id
    primary key.
    """

    __tablename__ = "symbols"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.Text)
    name = db.Column(db.Text)


class Prices(db.Model):
    __tablename__ = "prices"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.Text, index=True)
    price = db.Column(db.Float(precision=32))
    timestamp = db.Column(db.Float(precision=32), index=True)


Index("prices_symbol_timestamp_ix", Prices.symbol, Prices.timestamp)


class Indexes(db.Model):
    __tablename__ = "indexes"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.Text)
    value = db.Column(db.Float(precision=32))
    timestamp = db.Column(db.Float(precision=32))


class FriendStatuses(Enum):
    invited = "Invited"
    accepted = "Accepted"
    declined = "Declined"


class Friends(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    invited_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    status = db.Column(db.Enum(FriendStatuses))
    timestamp = db.Column(db.Float(precision=32))


class PayoutType(Enum):
    sidebet = "Sidebet"
    overall = "Overall"


class Winners(db.Model):
    __tablename__ = "winners"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    winner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    benchmark = db.Column(db.Enum(Benchmarks))
    score = db.Column(db.Float(precision=32))
    start_time = db.Column(db.Float(precision=32))
    end_time = db.Column(db.Float(precision=32))
    payout = db.Column(db.Float(precision=32))
    type = db.Column(db.Enum(PayoutType))
    timestamp = db.Column(db.Float(precision=32))


class ExternalInviteStatus(Enum):
    invited = "Invited"
    accepted = "Accepted"
    error = "error"
    declined = "Declined"


class ExternalInviteTypes(Enum):
    platform = "Platform"
    game = "Game"


class ExternalInvites(db.Model):
    __tablename__ = "external_invites"

    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    invited_email = db.Column(db.Text)
    status = db.Column(db.Enum(ExternalInviteStatus))
    timestamp = db.Column(db.Float(precision=32))
    type = db.Column(db.Enum(ExternalInviteTypes))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)


class BalancesAndPricesCache(db.Model):
    """Note: the defined fields here track the balances_and_prices_table_schema definition in schemas.py"""
    __tablename__ = "balances_and_prices_cache"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    symbol = db.Column(db.Text, index=True)
    timestamp = db.Column(db.Float(precision=32), index=True)
    balance = db.Column(db.Float(precision=32))
    price = db.Column(db.Float(precision=32))
    value = db.Column(db.Float(precision=32))


Index("balances_and_prices_game_user_timestamp_ix", BalancesAndPricesCache.game_id, BalancesAndPricesCache.user_id,
      BalancesAndPricesCache.timestamp)


class PaymentTypes(Enum):
    start = "start"
    refund = "refund"
    sidebet = "sidebet"
    overall = "overall"


class PaymentDirection(Enum):
    inflow = "inflow"
    outflow = "outflow"


class Processors(Enum):
    paypal = "paypal"


class Payments(db.Model):
    """This table handles real payments -- this isn't virtual currency, but an actual record of cash liabilities vis-a-
    vis the platform=
    """
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    processor = db.Column(db.Enum(Processors))
    uuid = db.Column(db.Text)
    winner_table_id = db.Column(db.Integer, db.ForeignKey("winners.id"))
    type = db.Column(db.Enum(PaymentTypes))
    direction = db.Column(db.Enum(PaymentDirection))
    timestamp = db.Column(db.Float(precision=32))
