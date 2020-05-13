"""For this iteration I'm conflating the definition of our applications database with the Flask-Migrate abstractions
to manage it. I'd like to do something cleaner, once I have a better understanding of what's going on with flake

Check out this structure:
https://stackoverflow.com/questions/56230626/why-is-sqlalchemy-database-uri-set-to-sqlite-memory-when-i-set-it-to-a-pa
"""

from enum import Enum

from backend.database.db import db


class OAuthProviders(Enum):
    google = "Google"
    facebook = "Facebook"
    twitter = "Twitter"


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    profile_pic = db.Column(db.Text)
    username = db.Column(db.Text)
    created_at = db.Column(db.DATETIME)
    provider = db.Column(db.Enum(OAuthProviders))
    resource_uuid = db.Column(db.Text)


class GameModes(Enum):
    return_weighted = "Return-weighted"
    consolation_prize = "Consolation prize"
    winner_takes_all = "Winner takes all"


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
    mode = db.Column(db.Enum(GameModes))
    duration = db.Column(db.Integer)
    buy_in = db.Column(db.Float)
    n_rebuys = db.Column(db.Integer)
    benchmark = db.Column(db.Enum(Benchmarks))
    side_bets_perc = db.Column(db.Float)
    side_bets_period = db.Column(db.Enum(SideBetPeriods))
    invite_window = db.Column(db.DateTime)


class GameStatusTypes(Enum):
    pending = "Pending"
    active = "Active"
    finished = "Finished"
    cancelled = "Cancelled"


class GameStatus(db.Model):
    __tablename__ = "game_status"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    status = db.Column(db.Enum(GameStatusTypes))
    users = db.Column(db.JSON)
    timestamp = db.Column(db.DateTime)  # When was the game opened


class BuyOrSell(Enum):
    buy = "Buy"
    sell = "Sell"


class OrderType(Enum):
    limit = "Limit"
    market = "Market"
    stop = "Stop"


class TimeInForce(Enum):
    day = "Day"
    until_cancelled = "Until Cancelled"


class Orders(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    ticker = db.Column(db.Text)
    buy_or_sell = db.Column(db.Enum(OrderType))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    order_type = db.Column(db.Enum(OrderType))
    time_in_force = db.Column(db.Enum(TimeInForce))


class OrderStatusTypes(Enum):
    pending = "Pending"
    fulfilled = "Fulfilled"
    cancelled = "Cancelled"
    expired = "Expired"


class Transactions(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    timestamp = db.Column(db.DateTime)
    order_status = db.Column(db.Enum(OrderStatusTypes))
    clear_price = db.Column(db.Float, nullable=True)


class BalanceTypes(Enum):
    actual_cash = "ActualCash"
    virtual_cash = "VirtualCash"
    virtual_stock = "VirtualStock"


class Balances(db.Model):
    __tablename__ = "balances"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"))
    timestamp = db.Column(db.DateTime)
    balance_type = db.Column(db.Enum(BalanceTypes))
    balance = db.Column(db.Float)
